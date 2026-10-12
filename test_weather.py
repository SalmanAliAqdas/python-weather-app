"""Automated tests. They use fake data, so they work without internet.

Run with:  python -m unittest -v
"""

import io
import json
import ssl
import unittest
import urllib.error

import weather

SAMPLE = {
    "current": {
        "time": "2026-10-12T10:00",
        "temperature_2m": 29.44,
        "apparent_temperature": 31.0,
        "relative_humidity_2m": 45,
        "wind_speed_10m": 8.3,
        "weather_code": 2,
    },
    "daily": {
        "time": ["2026-10-12", "2026-10-13", "2026-10-14"],
        "weather_code": [2, 0, 61],
        "temperature_2m_max": [31.2, 32.0, 28.5],
        "temperature_2m_min": [19.0, 20.1, 21.0],
        "precipitation_sum": [0.0, 0.0, 4.2],
    },
}

GEOCODE_SAMPLE = {
    "results": [{"name": "Multan", "country": "Pakistan", "latitude": 30.1978, "longitude": 71.4711}]
}


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def fake_opener_returning(data):
    def opener(request, timeout=None):
        return FakeResponse(json.dumps(data).encode("utf-8"))
    return opener


def fake_opener_raising(error):
    def opener(request, timeout=None):
        raise error
    return opener


def smart_opener(request, timeout=None):
    """Answers like the real service: geocoding or forecast, depending on the address."""
    url = request.full_url if hasattr(request, "full_url") else request
    data = GEOCODE_SAMPLE if "geocoding" in url else SAMPLE
    return FakeResponse(json.dumps(data).encode("utf-8"))


class ParsingTests(unittest.TestCase):
    def test_parse_forecast(self):
        result = weather.parse_forecast(SAMPLE)
        self.assertEqual(result["temperature"], 29.44)
        self.assertEqual(result["conditions"], "Partly cloudy")
        self.assertEqual(len(result["days"]), 3)
        self.assertEqual(result["days"][2]["conditions"], "Light rain")
        self.assertEqual(result["days"][2]["rain"], 4.2)

    def test_missing_data_gives_friendly_error(self):
        with self.assertRaises(weather.WeatherError):
            weather.parse_forecast({"current": {}})
        with self.assertRaises(weather.WeatherError):
            weather.parse_forecast({})

    def test_unknown_weather_code(self):
        self.assertEqual(weather.describe_code(12345), "Unknown conditions")

    def test_missing_number_shows_na(self):
        self.assertEqual(weather.number_text(None), "n/a")
        self.assertEqual(weather.number_text(3.14159), "3.1")


class UrlTests(unittest.TestCase):
    def test_forecast_url_asks_for_celsius(self):
        url = weather.build_forecast_url(31.5497, 74.3436)
        self.assertIn("latitude=31.5497", url)
        self.assertIn("longitude=74.3436", url)
        self.assertIn("temperature_unit=celsius", url)

    def test_geocoding_url_encodes_spaces(self):
        url = weather.build_geocoding_url("New York")
        self.assertIn("New+York", url)


class FormattingTests(unittest.TestCase):
    def test_report_contains_key_information(self):
        city = weather.CITIES["1"]
        text = weather.format_report(city, weather.parse_forecast(SAMPLE))
        self.assertIn("Lahore, Pakistan", text)
        self.assertIn("29.4°C", text)
        self.assertIn("Partly cloudy", text)
        self.assertIn("Humidity: 45%", text)
        self.assertIn("3-day forecast", text)
        self.assertIn("Light rain", text)


class NetworkErrorTests(unittest.TestCase):
    def test_no_internet(self):
        opener = fake_opener_raising(urllib.error.URLError("no route"))
        with self.assertRaises(weather.WeatherError) as caught:
            weather.fetch_json("https://example.com", opener)
        self.assertIn("internet", str(caught.exception))

    def test_connection_error_shows_technical_detail(self):
        opener = fake_opener_raising(urllib.error.URLError("some real reason"))
        with self.assertRaises(weather.WeatherError) as caught:
            weather.fetch_json("https://example.com", opener)
        self.assertIn("some real reason", str(caught.exception))

    def test_certificate_problem_gets_helpful_hint(self):
        error = urllib.error.URLError(ssl.SSLCertVerificationError("CERTIFICATE_VERIFY_FAILED"))
        with self.assertRaises(weather.WeatherError) as caught:
            weather.fetch_json("https://example.com", fake_opener_raising(error))
        self.assertIn("SSL", str(caught.exception))
        self.assertIn("date/time", str(caught.exception))

    def test_other_os_errors_are_caught(self):
        with self.assertRaises(weather.WeatherError):
            weather.fetch_json("https://example.com", fake_opener_raising(ConnectionResetError("reset")))

    def test_http_error(self):
        error = urllib.error.HTTPError("https://example.com", 500, "Server error", {}, None)
        with self.assertRaises(weather.WeatherError) as caught:
            weather.fetch_json("https://example.com", fake_opener_raising(error))
        self.assertIn("500", str(caught.exception))

    def test_timeout(self):
        with self.assertRaises(weather.WeatherError):
            weather.fetch_json("https://example.com", fake_opener_raising(TimeoutError()))

    def test_garbage_answer(self):
        def opener(request, timeout=None):
            return FakeResponse(b"this is not json")
        with self.assertRaises(weather.WeatherError):
            weather.fetch_json("https://example.com", opener)


class CitySearchTests(unittest.TestCase):
    def test_find_city(self):
        city = weather.find_city("Multan", fake_opener_returning(GEOCODE_SAMPLE))
        self.assertEqual(city["name"], "Multan")
        self.assertEqual(city["latitude"], 30.1978)

    def test_unknown_city(self):
        with self.assertRaises(weather.WeatherError):
            weather.find_city("Asdfghjkl", fake_opener_returning({}))

    def test_empty_name(self):
        with self.assertRaises(weather.WeatherError):
            weather.find_city("   ", fake_opener_returning(GEOCODE_SAMPLE))


class MenuTests(unittest.TestCase):
    def test_choose_by_number_and_by_name(self):
        self.assertIn("Lahore", weather.handle_choice("1", opener=smart_opener))
        self.assertIn("Karachi", weather.handle_choice("karachi", opener=smart_opener))
        self.assertIn("Islamabad", weather.handle_choice("3", opener=smart_opener))

    def test_all_cities(self):
        text = weather.handle_choice("4", opener=smart_opener)
        for name in ("Lahore", "Karachi", "Islamabad"):
            self.assertIn(name, text)

    def test_all_cities_survives_a_failure(self):
        opener = fake_opener_raising(urllib.error.URLError("down"))
        text = weather.handle_choice("all", opener=opener)
        self.assertEqual(text.count("Error:"), 3)

    def test_search_another_city(self):
        text = weather.handle_choice("5", ask=lambda prompt: "Multan", opener=smart_opener)
        self.assertIn("Multan, Pakistan", text)

    def test_quit(self):
        self.assertIsNone(weather.handle_choice("q"))

    def test_bad_choice(self):
        with self.assertRaises(weather.WeatherError):
            weather.handle_choice("banana")


if __name__ == "__main__":
    unittest.main()

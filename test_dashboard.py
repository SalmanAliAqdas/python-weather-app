"""Regression checks for the redesigned UI, with no live API requests."""

from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
import unittest
from unittest.mock import patch

import streamlit as st
from streamlit.testing.v1 import AppTest

from test_weather import SAMPLE
from weather import CITIES, WeatherError, parse_forecast
from weather_ui import daily_markup, details_markup, hero_markup, location_markup, upcoming_hours, weather_kind


APP = str(Path(__file__).with_name("streamlit_app.py"))


def full_response():
    response = deepcopy(SAMPLE)
    response["current"].update({"surface_pressure": 1002, "visibility": 9000, "is_day": 1})
    start = datetime(2026, 10, 12, 0)
    response["hourly"] = {
        "time": [(start + timedelta(hours=i)).isoformat(timespec="minutes") for i in range(48)],
        "temperature_2m": [20 + i % 12 for i in range(48)],
        "weather_code": [2] * 48,
        "precipitation_probability": [10] * 48,
    }
    response["daily"].update({
        "sunrise": [f"{date}T06:00" for date in response["daily"]["time"]],
        "sunset": [f"{date}T18:00" for date in response["daily"]["time"]],
    })
    response["timezone"] = "Asia/Karachi"
    return response


class PresentationTests(unittest.TestCase):
    def test_condition_aware_backgrounds(self):
        self.assertEqual(weather_kind(0), "sunny")
        self.assertEqual(weather_kind(3), "cloudy")
        self.assertEqual(weather_kind(61), "rainy")
        self.assertEqual(weather_kind(73), "snowy")
        self.assertEqual(weather_kind(0, False), "night")

    def test_external_text_is_escaped(self):
        city = {**CITIES["1"], "name": '<script>alert("city")</script>'}
        weather = parse_forecast(full_response())
        weather["conditions"] = "<img src=x onerror=alert(1)>"
        markup = location_markup(city, weather) + hero_markup(city, weather, "°C")
        self.assertNotIn("<script>", markup)
        self.assertNotIn("<img src=x", markup)
        self.assertIn("&lt;script&gt;", markup)

    def test_missing_metrics_are_omitted(self):
        weather = parse_forecast({"current": {"temperature_2m": 18}})
        markup = details_markup(weather)
        self.assertNotIn("Humidity", markup)
        self.assertNotIn("Sunrise", markup)
        self.assertNotIn("None", markup)

    def test_upcoming_forecast_covers_next_24_hours(self):
        weather = parse_forecast(full_response())
        hours = upcoming_hours(weather)
        self.assertEqual(len(hours), 24)
        self.assertEqual(hours[0]["time"], "2026-10-12T10:00")
        self.assertEqual(hours[-1]["time"], "2026-10-13T09:00")

    def test_hero_shows_converted_values_and_today_limits(self):
        markup = hero_markup(CITIES["1"], parse_forecast(full_response()), "°F")
        self.assertIn("85<span>°F", markup)
        self.assertIn("Feels like 88°F", markup)
        self.assertIn("88°F", markup)  # today's high
        self.assertIn("66°F", markup)  # today's low

    def test_daily_precipitation_amount_remains_available(self):
        markup = daily_markup(parse_forecast(full_response()), "°C")
        self.assertIn("4.2 mm", markup)


class DashboardFlowTests(unittest.TestCase):
    def setUp(self):
        st.cache_data.clear()

    def test_unit_rerun_uses_cached_weather(self):
        with patch("weather.fetch_json", return_value=full_response()) as fetch:
            app = AppTest.from_file(APP, default_timeout=15).run()
            self.assertEqual(len(app.exception), 0)
            app.get("button_group")[0].set_value("°F").run()
            self.assertEqual(app.session_state["temperature_unit"], "°F")
            self.assertEqual(fetch.call_count, 1)
            self.assertEqual(len(app.exception), 0)

    def test_search_and_recent_history(self):
        multan = {"name": "Multan", "country": "Pakistan", "latitude": 30.2, "longitude": 71.5}
        karachi = CITIES["2"]
        with patch("weather.fetch_json", return_value=full_response()) as fetch, \
                patch("weather.find_city", side_effect=[multan, karachi]):
            app = AppTest.from_file(APP, default_timeout=15).run()
            for city in (multan, karachi):
                app.text_input[0].set_value(city["name"])
                app.button[0].click().run()
                self.assertEqual(len(app.exception), 0)
            self.assertEqual(app.session_state["selected_city"]["name"], "Karachi")
            self.assertEqual(len(app.session_state["search_history"]), 2)
            next(button for button in app.button if button.label == "Multan").click().run()
            self.assertEqual(app.session_state["selected_city"]["name"], "Multan")
            self.assertEqual(fetch.call_count, 3)

    def test_invalid_search_keeps_active_city(self):
        with patch("weather.fetch_json", return_value=full_response()), \
                patch("weather.find_city", side_effect=WeatherError("Could not find that city.")):
            app = AppTest.from_file(APP, default_timeout=15).run()
            app.text_input[0].set_value("Unknown City")
            app.button[0].click().run()
            self.assertEqual(app.session_state["selected_city"]["name"], "Lahore")
            self.assertIn("Could not find", app.error[0].value)
            self.assertEqual(len(app.exception), 0)

    def test_empty_search_is_explained(self):
        with patch("weather.fetch_json", return_value=full_response()):
            app = AppTest.from_file(APP, default_timeout=15).run()
            app.button[0].click().run()
            self.assertIn("city name", app.warning[0].value)
            self.assertEqual(len(app.exception), 0)

    def test_missing_optional_fields_render(self):
        with patch("weather.fetch_json", return_value={"current": {"temperature_2m": 18}}):
            app = AppTest.from_file(APP, default_timeout=15).run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.error), 0)

    def test_api_failure_renders_friendly_state(self):
        with patch("weather.fetch_json", side_effect=WeatherError("The service is temporarily busy.")):
            app = AppTest.from_file(APP, default_timeout=15).run()
            self.assertIn("temporarily busy", app.error[0].value)
            self.assertEqual(len(app.exception), 0)


if __name__ == "__main__":
    unittest.main()

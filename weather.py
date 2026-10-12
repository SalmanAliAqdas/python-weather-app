"""Command-line weather app for Lahore, Karachi and Islamabad.

Data comes from the free Open-Meteo service (no account or API key needed).
Temperatures are in degrees Celsius.
"""

import json
import socket
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import date

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
TIMEOUT_SECONDS = 10
FORECAST_DAYS = 5

CITIES = {
    "1": {"name": "Lahore", "country": "Pakistan", "latitude": 31.5497, "longitude": 74.3436},
    "2": {"name": "Karachi", "country": "Pakistan", "latitude": 24.8607, "longitude": 67.0011},
    "3": {"name": "Islamabad", "country": "Pakistan", "latitude": 33.6844, "longitude": 73.0479},
}

# WMO weather codes used by Open-Meteo, in plain English.
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mostly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Freezing fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    56: "Light freezing drizzle",
    57: "Freezing drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light rain showers",
    81: "Rain showers",
    82: "Heavy rain showers",
    85: "Light snow showers",
    86: "Snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Severe thunderstorm with hail",
}


class WeatherError(Exception):
    """A problem we can explain to the user in plain English."""


# ---------- Talking to the internet ----------

def explain_connection_problem(reason):
    """Turn a technical network error into a message that shows the real cause."""
    detail = str(reason) or type(reason).__name__
    if isinstance(reason, ssl.SSLError) or "CERTIFICATE" in detail.upper():
        hint = ("A secure-connection (SSL) check failed. Common causes: wrong date/time on this "
                "computer, antivirus or firewall scanning web traffic, or a company/school proxy.")
    elif "getaddrinfo" in detail or "Name or service" in detail:
        hint = "The computer could not look up the website address (DNS). Check Wi-Fi and internet."
    elif "timed out" in detail:
        hint = "The connection timed out. A firewall may be blocking Python, or the internet is slow."
    else:
        hint = "Check your internet connection, firewall and antivirus, then try again."
    return f"Could not connect. {hint}\n  Technical detail: {detail}"


def fetch_json(url, opener=urllib.request.urlopen):
    """Download a web address and return the JSON inside it."""
    request = urllib.request.Request(url, headers={"User-Agent": "python-weather-app/1.0"})
    try:
        with opener(request, timeout=TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise WeatherError(f"The weather service returned an error (code {error.code}). Try again later.")
    except urllib.error.URLError as error:
        raise WeatherError(explain_connection_problem(error.reason))
    except (TimeoutError, socket.timeout):
        raise WeatherError("The weather service took too long to answer. Try again.")
    except OSError as error:
        raise WeatherError(explain_connection_problem(error))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise WeatherError("The weather service sent an answer we could not read.")


def build_forecast_url(latitude, longitude):
    query = urllib.parse.urlencode({
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
        "forecast_days": FORECAST_DAYS,
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
    })
    return f"{FORECAST_URL}?{query}"


def build_geocoding_url(name):
    query = urllib.parse.urlencode({"name": name, "count": 1, "language": "en", "format": "json"})
    return f"{GEOCODING_URL}?{query}"


def find_city(name, opener=urllib.request.urlopen):
    """Look up any city name and return its details."""
    name = name.strip()
    if not name:
        raise WeatherError("Please type a city name.")
    data = fetch_json(build_geocoding_url(name), opener)
    results = data.get("results") or []
    if not results:
        raise WeatherError(f"Could not find a city called '{name}'. Check the spelling.")
    first = results[0]
    try:
        return {
            "name": first["name"],
            "country": first.get("country", ""),
            "latitude": first["latitude"],
            "longitude": first["longitude"],
        }
    except KeyError:
        raise WeatherError("The city search sent an incomplete answer. Try again.")


# ---------- Turning raw data into something readable ----------

def describe_code(code):
    return WEATHER_CODES.get(code, "Unknown conditions")


def parse_forecast(data):
    """Pick out the numbers we need. Raises WeatherError if anything is missing."""
    try:
        current = data["current"]
        daily = data["daily"]
        parsed = {
            "time": current["time"],
            "temperature": current["temperature_2m"],
            "feels_like": current["apparent_temperature"],
            "humidity": current["relative_humidity_2m"],
            "wind": current["wind_speed_10m"],
            "conditions": describe_code(current["weather_code"]),
            "days": [],
        }
        for index, day in enumerate(daily["time"]):
            parsed["days"].append({
                "date": day,
                "conditions": describe_code(daily["weather_code"][index]),
                "max": daily["temperature_2m_max"][index],
                "min": daily["temperature_2m_min"][index],
                "rain": daily["precipitation_sum"][index],
            })
        return parsed
    except (KeyError, IndexError, TypeError):
        raise WeatherError("The weather service sent incomplete data. Try again.")


def number_text(value, decimals=1):
    """Show a number, or 'n/a' if the service did not supply it."""
    if value is None:
        return "n/a"
    return f"{value:.{decimals}f}"


def format_day(day_text):
    try:
        return date.fromisoformat(day_text).strftime("%a %d %b")
    except ValueError:
        return day_text


def format_report(city, weather):
    place = city["name"] + (f", {city['country']}" if city.get("country") else "")
    lines = [
        place,
        f"  Now: {number_text(weather['temperature'])}°C "
        f"(feels like {number_text(weather['feels_like'])}°C), {weather['conditions']}",
        f"  Humidity: {number_text(weather['humidity'], 0)}%   "
        f"Wind: {number_text(weather['wind'])} km/h",
        f"  {len(weather['days'])}-day forecast:",
    ]
    for day in weather["days"]:
        lines.append(
            f"    {format_day(day['date'])}  {day['conditions']:<22} "
            f"{number_text(day['min'])} to {number_text(day['max'])}°C   "
            f"rain {number_text(day['rain'])} mm"
        )
    return "\n".join(lines)


def get_report(city, opener=urllib.request.urlopen):
    """Fetch and format the weather for one city."""
    url = build_forecast_url(city["latitude"], city["longitude"])
    weather = parse_forecast(fetch_json(url, opener))
    return format_report(city, weather)


# ---------- Menu ----------

MENU_TEXT = """\
Weather App (temperatures in °C)
  1. Lahore
  2. Karachi
  3. Islamabad
  4. All three cities
  5. Search another city
  q. Quit"""


def handle_choice(choice, ask=input, opener=urllib.request.urlopen):
    """Return the text to show for a menu choice, or None to quit."""
    choice = choice.strip().lower()

    names = {city["name"].lower(): key for key, city in CITIES.items()}
    choice = names.get(choice, choice)

    if choice in ("q", "quit", "exit"):
        return None
    if choice in CITIES:
        return get_report(CITIES[choice], opener)
    if choice in ("4", "all"):
        reports = []
        for city in CITIES.values():
            try:
                reports.append(get_report(city, opener))
            except WeatherError as error:
                reports.append(f"{city['name']}\n  Error: {error}")
        return "\n\n".join(reports)
    if choice in ("5", "search"):
        city = find_city(ask("City name: "), opener)
        return get_report(city, opener)
    raise WeatherError("Please choose 1, 2, 3, 4, 5 or q.")


def main():
    while True:
        print()
        print(MENU_TEXT)
        choice = input("Your choice: ")
        try:
            result = handle_choice(choice)
        except WeatherError as error:
            print(f"Error: {error}")
            continue
        if result is None:
            print("Goodbye!")
            break
        print()
        print(result)
        print()
        input("Press Enter to go back to the menu...")


if __name__ == "__main__":
    main()

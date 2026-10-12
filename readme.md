# Python Weather App

A command-line weather app written in Python. It shows the current weather and a 5-day forecast for **Lahore, Karachi and Islamabad**, in degrees Celsius, and can also look up any other city in the world.

Weather data comes from the free [Open-Meteo](https://open-meteo.com/) service. No account, no API key and no extra packages are needed.

## Features
- Current temperature, "feels like" temperature, humidity and wind speed
- 5-day forecast with conditions, minimum and maximum temperature, and expected rain
- One-key shortcuts for Lahore, Karachi and Islamabad, or show all three at once
- Search any other city by name
- Friendly messages when there is no internet, the city is not found, or the service is down
- Automated tests that work without internet (20 tests)

## Requirements
- Python 3 installed
- An internet connection when you run the app

## How to run
```
python weather.py
```
If `python` is not recognized on Windows, use `py weather.py`.

## How to use it
Type a number from the menu and press Enter:

```
Weather App (temperatures in °C)
  1. Lahore
  2. Karachi
  3. Islamabad
  4. All three cities
  5. Search another city
  q. Quit
```

Example output (format only, the numbers change every time):
```
Lahore, Pakistan
  Now: 29.4°C (feels like 31.0°C), Partly cloudy
  Humidity: 45%   Wind: 8.3 km/h
  3-day forecast:
    Mon 12 Oct  Partly cloudy          19.0 to 31.2°C   rain 0.0 mm
    Tue 13 Oct  Clear sky              20.1 to 32.0°C   rain 0.0 mm
    Wed 14 Oct  Light rain             21.0 to 28.5°C   rain 4.2 mm
```

## Running the tests
The tests use fake weather data, so they run without internet:
```
python -m unittest -v
```

## How it works
1. The app builds a web address containing the city's latitude and longitude.
2. It downloads the answer (JSON data) using Python's built-in `urllib`.
3. It picks out the numbers it needs and turns weather codes into plain English.
4. It prints a readable report.

## Data source and licensing
Weather data by [Open-Meteo.com](https://open-meteo.com/). Their free service is intended for non-commercial use. Check their terms before using this in a commercial product.

## Project structure
- `weather.py`: the app
- `test_weather.py`: automated tests
- `.gitignore`: files Git should ignore
- `readme.md`: this file

## Possible future improvements
- Hourly forecast
- Choose Celsius or Fahrenheit
- A web or mobile version

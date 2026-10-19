# Skyline Weather

A polished weather dashboard built with Streamlit and Open-Meteo. Search cities worldwide, browse current conditions and forecasts, or run the original command-line app for quick reports.

**Live demo:** [Add Streamlit Community Cloud URL after deployment](https://share.streamlit.io/)

## Features

- Current temperature, conditions, feels-like temperature, humidity and wind
- Surface pressure, visibility, sunrise and sunset when available
- Next-hours forecast with an interactive temperature chart
- Five-day forecast with highs, lows and rain probability when available
- Celsius/Fahrenheit display switch and recent searches for the current browser session
- Friendly messages for invalid cities and service failures
- Ten-minute in-memory API response cache to limit requests

All weather values come from Open-Meteo. Missing provider values are omitted rather than estimated by the app.

## Technologies

Python 3.10+, Streamlit, Altair (installed with Streamlit), pandas (installed with Streamlit), and Python's standard-library `urllib` for API requests. The web and command-line apps share the same provider and parsing functions in `weather.py`.

## Installation and local use

```bash
git clone <repository-url>
cd python-weather-app
python -m venv .venv
```

Activate the virtual environment with `.venv\Scripts\activate` on Windows or `source .venv/bin/activate` on macOS/Linux, then run:

```bash
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Open the local URL printed by Streamlit. The original command-line app remains available with `python weather.py`.

## Configuration

**Required environment variables: none.** The Open-Meteo public, non-commercial API requires no API key. No Streamlit Cloud secrets need to be configured. Do not commit a `.env` file or `.streamlit/secrets.toml` if you add unrelated local settings later.

## Deploy to Streamlit Community Cloud

1. Push this repository to GitHub after reviewing the changes.
2. In [Streamlit Community Cloud](https://share.streamlit.io/), create a new app from that repository and choose the branch to publish.
3. Set the main file path to **`streamlit_app.py`**.
4. Leave app secrets empty; no secret name is required.
5. Deploy and add the public URL to the live demo link above.

The platform installs `requirements.txt` automatically. Docker is not required.

## Tests

```bash
python -m unittest -v
```

Tests mock API responses and run without network access.

## Screenshots

Add screenshots of the desktop and mobile dashboard after deployment.

## Data source and limitations

Weather data and geocoding: [Open-Meteo](https://open-meteo.com/). Open-Meteo's [free API terms](https://open-meteo.com/en/terms) allow non-commercial use and require attribution. Commercial use needs an appropriate Open-Meteo plan or license. Forecasts are estimates, and available fields can vary by location or model. The free service has rate limits and no uptime guarantee. Search history lasts only for the current Streamlit session.

## Project files

- `streamlit_app.py`: Streamlit dashboard
- `weather.py`: shared API client, parsing, and original command-line app
- `test_weather.py`: automated API and parsing tests
- `requirements.txt`: web dependencies

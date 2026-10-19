"""Streamlit weather dashboard backed by the original Open-Meteo client."""

from datetime import datetime
from html import escape

import altair as alt
import pandas as pd
import streamlit as st

from weather import CITIES, WeatherError, build_forecast_url, convert_temperature, fetch_json, find_city, parse_forecast


st.set_page_config(page_title="Skyline | Weather", page_icon="☀️", layout="wide")

st.markdown("""
<style>
  :root { color-scheme: light; }
  .stApp { background: linear-gradient(160deg, #e9f5ff 0%, #f8fbff 35%, #f3f7fc 100%); color: #183451; }
  .block-container { max-width: 1160px; padding-top: 2.2rem; padding-bottom: 3rem; }
  h1, h2, h3, p { color: #183451; }
  h1 { font-size: clamp(2rem, 4vw, 3rem) !important; letter-spacing: -.04em; }
  h2 { font-size: 1.35rem !important; letter-spacing: -.02em; }
  .eyebrow { color: #3475aa; font-size: .75rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
  .subtle { color: #5a7390; font-size: .94rem; }
  .hero { padding: 2rem 2.2rem; border-radius: 26px; background: linear-gradient(115deg, #1466a9, #52afe5); box-shadow: 0 16px 38px rgba(35,100,158,.18); color: white; margin: 1rem 0 1.4rem; }
  .hero * { color: white; }
  .hero-city { font-size: clamp(1.35rem, 2.5vw, 2rem); font-weight: 700; }
  .hero-main { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; margin: .6rem 0; }
  .hero-icon { font-size: clamp(3rem, 7vw, 5rem); line-height: 1; }
  .hero-temp { font-size: clamp(3.5rem, 8vw, 6rem); font-weight: 750; line-height: 1; letter-spacing: -.07em; }
  .hero-condition { font-size: 1.1rem; font-weight: 600; }
  .hero-meta { font-size: .88rem; opacity: .88; margin-top: .6rem; }
  .metric-card { background: #fff; border: 1px solid #dfebf5; border-radius: 18px; padding: 1.15rem 1.25rem; min-height: 110px; box-shadow: 0 6px 22px rgba(39,92,137,.07); margin-bottom: .8rem; }
  .metric-label { color: #58738f; font-size: .85rem; font-weight: 600; }
  .metric-value { color: #173b5e; font-size: 1.5rem; font-weight: 750; margin-top: .35rem; }
  .day-card { background: #fff; border: 1px solid #dfebf5; border-radius: 18px; padding: 1.1rem; min-height: 165px; box-shadow: 0 6px 22px rgba(39,92,137,.06); margin-bottom: .8rem; }
  .day-title { color: #395a79; font-weight: 700; font-size: .9rem; }
  .day-icon { font-size: 2rem; line-height: 1.4; }
  .day-temp { color: #173b5e; font-weight: 750; font-size: 1.15rem; }
  .day-extra { color: #5a7390; font-size: .79rem; margin-top: .3rem; }
  .hour-card { background: #fff; border: 1px solid #dfebf5; border-radius: 16px; padding: .8rem; text-align: center; margin-bottom: .7rem; }
  .hour-icon { font-size: 1.65rem; }
  .card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: .85rem; margin-bottom: 1rem; }
  .card-grid .metric-card, .card-grid .day-card, .card-grid .hour-card { margin-bottom: 0; }
  @media (max-width: 640px) { .block-container { padding: 1rem; } .hero { padding: 1.5rem; } }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=600, show_spinner=False)
def cached_city(name):
    return find_city(name)


@st.cache_data(ttl=600, show_spinner=False)
def cached_weather(latitude, longitude):
    return parse_forecast(fetch_json(build_forecast_url(latitude, longitude)))


def temp_text(value, unit, digits=0):
    converted = convert_temperature(value, unit)
    return f"{converted:.{digits}f}{unit}" if converted is not None else None


def icon_for(code, is_day=True):
    if code is None:
        return "🌡️"
    if code == 0:
        return "☀️" if is_day else "🌙"
    if code in (1, 2):
        return "🌤️" if is_day else "☁️"
    if code == 3:
        return "☁️"
    if code in (45, 48):
        return "🌫️"
    if 51 <= code <= 67 or 80 <= code <= 82:
        return "🌧️"
    if 71 <= code <= 77 or code in (85, 86):
        return "❄️"
    if code in (95, 96, 99):
        return "⛈️"
    return "🌡️"


def local_time(value, date_only=False):
    if not value:
        return None
    try:
        stamp = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return str(value)
    return stamp.strftime("%a %d %b" if date_only else "%I:%M %p").lstrip("0")


def card(label, value):
    return (f'<div class="metric-card"><div class="metric-label">{escape(label)}</div>'
            f'<div class="metric-value">{escape(str(value))}</div></div>')


def render_dashboard(city, weather, unit):
    place = city["name"] + (f", {city['country']}" if city.get("country") else "")
    updated = local_time(weather.get("time"))
    timezone = weather.get("timezone")
    updated_text = f"Updated {updated}" if updated else ""
    if updated_text and timezone:
        updated_text += f" · {timezone}"
    hero = (
        '<div class="hero">'
        f'<div class="eyebrow">Current weather</div><div class="hero-city">{escape(place)}</div>'
        f'<div class="hero-main"><span class="hero-icon">{icon_for(weather.get("code"), weather.get("is_day") != 0)}</span>'
        f'<span class="hero-temp">{escape(temp_text(weather["temperature"], unit) or "")}</span></div>'
        f'<div class="hero-condition">{escape(weather.get("conditions") or "Current conditions")}</div>'
        f'<div class="hero-meta">{escape(updated_text)}</div></div>'
    )
    st.markdown(hero, unsafe_allow_html=True)

    st.subheader("At a glance")
    today = weather["days"][0] if weather["days"] else {}
    metrics = [
        ("Feels like", temp_text(weather.get("feels_like"), unit)),
        ("Humidity", f'{weather["humidity"]:.0f}%' if weather.get("humidity") is not None else None),
        ("Wind speed", f'{weather["wind"]:.1f} km/h' if weather.get("wind") is not None else None),
        ("Surface pressure", f'{weather["pressure"]:.0f} hPa' if weather.get("pressure") is not None else None),
        ("Visibility", f'{weather["visibility"] / 1000:.1f} km' if weather.get("visibility") is not None else None),
        ("Sunrise", local_time(today.get("sunrise"))),
        ("Sunset", local_time(today.get("sunset"))),
    ]
    metrics = [(label, value) for label, value in metrics if value is not None]
    if metrics:
        st.markdown('<div class="card-grid">' + ''.join(card(label, value) for label, value in metrics) + '</div>', unsafe_allow_html=True)

    hours = weather.get("hours", [])
    current_time = weather.get("time") or ""
    upcoming = [hour for hour in hours if hour.get("time") and hour["time"] >= current_time][:8]
    if upcoming:
        st.subheader("Next hours")
        hour_cards = []
        for hour in upcoming:
            rain = hour.get("rain_probability")
            rain_text = f" · Rain {rain:.0f}%" if rain is not None else ""
            hour_cards.append(
                '<div class="hour-card">'
                f'<div class="day-title">{escape(local_time(hour["time"]) or "")}</div>'
                f'<div class="hour-icon">{icon_for(hour.get("code"))}</div>'
                f'<div class="day-temp">{escape(temp_text(hour.get("temperature"), unit) or "—")}</div>'
                f'<div class="day-extra">{escape(hour.get("conditions") or "")}{escape(rain_text)}</div></div>'
            )
        st.markdown('<div class="card-grid">' + ''.join(hour_cards) + '</div>', unsafe_allow_html=True)

        chart_rows = []
        for hour in upcoming:
            if hour.get("temperature") is None:
                continue
            try:
                chart_time = datetime.fromisoformat(hour["time"])
            except (TypeError, ValueError):
                continue
            chart_rows.append({"Time": chart_time, "Temperature": convert_temperature(hour["temperature"], unit)})
        if chart_rows:
            chart = alt.Chart(pd.DataFrame(chart_rows)).mark_line(point=True, strokeWidth=3, color="#217ec0").encode(
                x=alt.X("Time:T", title="Local time", axis=alt.Axis(format="%I %p", labelColor="#58738f")),
                y=alt.Y("Temperature:Q", title=f"Temperature ({unit})", scale=alt.Scale(zero=False), axis=alt.Axis(labelColor="#58738f")),
                tooltip=[alt.Tooltip("Time:T", format="%a %I:%M %p"), alt.Tooltip("Temperature:Q", format=".1f")],
            ).properties(height=230, background="transparent")
            st.altair_chart(chart, width="stretch")

    if weather["days"]:
        st.subheader("5-day forecast")
        day_cards = []
        for day in weather["days"]:
            high = temp_text(day.get("max"), unit)
            low = temp_text(day.get("min"), unit)
            range_text = " / ".join(x for x in (high, low) if x) or "—"
            extra = []
            if day.get("rain_probability") is not None:
                extra.append(f'Rain {day["rain_probability"]:.0f}%')
            if day.get("rain") is not None:
                extra.append(f'{day["rain"]:.1f} mm')
            day_cards.append(
                '<div class="day-card">'
                f'<div class="day-title">{escape(local_time(day.get("date"), True) or "")}</div>'
                f'<div class="day-icon">{icon_for(day.get("code"))}</div>'
                f'<div class="day-temp">{escape(range_text)}</div>'
                f'<div class="day-extra">{escape(day.get("conditions") or "")}</div>'
                f'<div class="day-extra">{escape(" · ".join(extra))}</div></div>'
            )
        st.markdown('<div class="card-grid">' + ''.join(day_cards) + '</div>', unsafe_allow_html=True)
    elif not upcoming:
        st.info("Forecast data is unavailable for this location right now.")


def main():
    st.markdown('<div class="eyebrow">Skyline weather</div>', unsafe_allow_html=True)
    st.title("A clearer view of the day")
    st.markdown('<p class="subtle">Live conditions and a thoughtful forecast, wherever you are.</p>', unsafe_allow_html=True)

    if "selected_city" not in st.session_state:
        st.session_state.selected_city = CITIES["1"]
    if "search_history" not in st.session_state:
        st.session_state.search_history = []

    with st.form("city_search"):
        input_col, button_col = st.columns([4, 1])
        with input_col:
            query = st.text_input("City", placeholder="Search any city, e.g. Tokyo", label_visibility="collapsed")
        with button_col:
            submitted = st.form_submit_button("Search weather", width="stretch")

    if submitted:
        if not query.strip():
            st.warning("Please enter a city name.")
        else:
            try:
                with st.spinner("Finding your city..."):
                    city = cached_city(query.strip())
                    # Confirm weather is available before changing the selected city.
                    cached_weather(city["latitude"], city["longitude"])
                st.session_state.selected_city = city
                history = [item for item in st.session_state.search_history if item["name"] != city["name"] or item.get("country") != city.get("country")]
                st.session_state.search_history = [city] + history[:5]
            except WeatherError as error:
                st.error(str(error))

    controls = st.columns([3, 1])
    with controls[0]:
        if st.session_state.search_history:
            st.caption("Recent searches")
            history_cols = st.columns(min(4, len(st.session_state.search_history)))
            for column, city in zip(history_cols, st.session_state.search_history[:4]):
                with column:
                    if st.button(city["name"], key=f'history_{city["name"]}_{city.get("country", "")}', width="stretch"):
                        st.session_state.selected_city = city
    with controls[1]:
        unit = st.segmented_control("Temperature unit", ["°C", "°F"], default="°C", label_visibility="collapsed") or "°C"

    city = st.session_state.selected_city
    try:
        with st.spinner("Loading the latest weather..."):
            weather = cached_weather(city["latitude"], city["longitude"])
        render_dashboard(city, weather, unit)
    except WeatherError as error:
        st.error(str(error))
    st.caption("Weather data: [Open-Meteo](https://open-meteo.com/). Times are local to the selected city. Forecasts are estimates.")


if __name__ == "__main__":
    main()

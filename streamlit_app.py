"""Skyline's Streamlit interface; the original weather client stays in weather.py."""

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from weather import CITIES, WeatherError, build_forecast_url, convert_temperature, fetch_json, find_city, parse_forecast
from weather_ui import (
    daily_markup, details_markup, hero_markup, hourly_markup, location_markup,
    parse_time, section_heading, upcoming_hours, weather_icon,
)


st.set_page_config(
    page_title="Skyline · Weather", page_icon="☀️", layout="wide",
    initial_sidebar_state="collapsed",
)

ASSETS = Path(__file__).resolve().parent / "assets"


@st.cache_data(ttl=600, show_spinner=False, max_entries=256)
def cached_city(name):
    return find_city(name)


@st.cache_data(ttl=600, show_spinner=False, max_entries=256)
def cached_weather(latitude, longitude):
    return parse_forecast(fetch_json(build_forecast_url(latitude, longitude)))


def temperature_chart(hours, unit):
    """A light, interactive trend chart using only available provider readings."""
    rows = [
        {"Time": parse_time(hour["time"]), "Temperature": convert_temperature(hour["temperature"], unit)}
        for hour in hours if parse_time(hour.get("time")) and hour.get("temperature") is not None
    ]
    if not rows:
        return None
    frame = pd.DataFrame(rows)
    floor = frame["Temperature"].min() - 2
    ceiling = frame["Temperature"].max() + 2
    base = alt.Chart(frame).encode(
        x=alt.X("Time:T", axis=alt.Axis(format="%I %p", tickCount=4, grid=False)),
        y=alt.Y("Temperature:Q", scale=alt.Scale(domain=[floor, ceiling], zero=False),
                axis=alt.Axis(tickCount=4, labelExpr="datum.label + '°'")),
    )
    tooltip = [alt.Tooltip("Time:T", title="Local time", format="%a, %I:%M %p"),
               alt.Tooltip("Temperature:Q", title=f"Temperature ({unit})", format=".1f")]
    hover = alt.selection_point(nearest=True, on="mouseover", fields=["Time"], empty=False, clear="mouseout")
    area = base.mark_area(interpolate="monotone", color=alt.Gradient(
        gradient="linear", x1=0, y1=0, x2=0, y2=1,
        stops=[alt.GradientStop(color="#d9edfc", offset=0), alt.GradientStop(color="#ffffff", offset=1)],
    )).encode(y2=alt.datum(float(floor)))
    line = base.mark_line(interpolate="monotone", color="#388ad7", strokeWidth=2.5).encode(tooltip=tooltip)
    points = base.mark_circle(size=55, color="#2879cd").encode(
        opacity=alt.condition(hover, alt.value(1), alt.value(0)), tooltip=tooltip,
    ).add_params(hover)
    return (alt.layer(area, line, points).properties(height=180, background="#ffffff")
            .configure_view(stroke=None)
            .configure_axis(title=None, domain=False, ticks=False, labelFontSize=10,
                            labelColor="#6d8296", labelPadding=9, gridColor="#edf3f8"))


def daylight_hours(weather):
    """Use returned sunrise/sunset times to choose day/night forecast artwork."""
    hours = []
    for raw in upcoming_hours(weather):
        hour = dict(raw)
        stamp = parse_time(hour.get("time"))
        day = next((item for item in weather.get("days", []) if item.get("date") == stamp.date().isoformat()), {})
        sunrise, sunset = parse_time(day.get("sunrise")), parse_time(day.get("sunset"))
        if sunrise and sunset:
            try:
                hour["is_day"] = sunrise <= stamp < sunset
            except TypeError:
                pass
        hours.append(hour)
    return hours


def render_dashboard(city, weather, unit):
    st.html(location_markup(city, weather))
    hero_column, detail_column = st.columns([1.7, 1], gap="medium")
    with hero_column:
        st.html(hero_markup(city, weather, unit))
    with detail_column:
        st.html(details_markup(weather))

    hours = daylight_hours(weather)
    hourly_column, daily_column = st.columns([1.7, 1], gap="medium")
    with hourly_column:
        with st.container(key="sky-hourly"):
            st.html(section_heading("Hourly outlook", "Next 24 hours · local time"))
            if hours:
                st.html(hourly_markup(hours, unit))
                chart = temperature_chart(hours, unit)
                if chart is not None:
                    st.html(f'<div class="sky-chart-label"><i></i> Temperature trend · {unit}</div>')
                    st.altair_chart(chart, width="stretch", theme=None)
            else:
                st.html('<div class="sky-empty">Hourly forecast data is unavailable right now. Current conditions are shown above.</div>')
    with daily_column:
        with st.container(key="sky-daily"):
            days = weather.get("days", [])
            st.html(section_heading(f"{len(days)}-day forecast" if days else "Daily forecast", f"High / low · {unit}"))
            if days:
                st.html(daily_markup(weather, unit))
            else:
                st.html('<div class="sky-empty">Daily forecast data is unavailable for this location right now.</div>')


def search_city(query):
    """Keep the active location until both search and weather loading succeed."""
    if not query.strip():
        st.warning("Enter a city name to see its weather.")
        return
    try:
        with st.spinner("Finding your city and its latest forecast…"):
            city = cached_city(query.strip())
            cached_weather(city["latitude"], city["longitude"])
        st.session_state.selected_city = city
        history = [item for item in st.session_state.search_history
                   if (item["latitude"], item["longitude"]) != (city["latitude"], city["longitude"])]
        st.session_state.search_history = [city] + history[:5]
    except WeatherError as error:
        st.error(str(error))


def main():
    st.html(ASSETS / "dashboard.css")
    st.session_state.setdefault("selected_city", CITIES["1"].copy())
    st.session_state.setdefault("search_history", [])

    with st.container(key="sky-shell"):
        with st.container(key="sky-header"):
            brand, controls = st.columns([1.1, 3.4], gap="medium", vertical_alignment="center")
            with brand:
                st.html('<div class="sky-brand"><div class="sky-brand-mark">'
                        + weather_icon(2) + '</div><div><div class="sky-brand-name">skyline<span>.</span></div>'
                        '<div class="sky-brand-tag">YOUR DAILY OUTLOOK</div></div></div>')
            with controls:
                with st.container(horizontal=True, wrap=False, vertical_alignment="center", gap="medium"):
                    with st.container(key="sky-search"):
                        with st.form("city_search", border=False):
                            with st.container(horizontal=True, wrap=False, gap="small", vertical_alignment="center"):
                                query = st.text_input("Search city", placeholder="Search for a city…", label_visibility="collapsed")
                                submitted = st.form_submit_button("Search", type="primary", width=78)
                    with st.container(key="sky-unit", width=100):
                        unit = st.segmented_control("Temperature unit", ["°C", "°F"], default="°C",
                                                    label_visibility="collapsed", key="temperature_unit") or "°C"

        if submitted:
            search_city(query)

        if st.session_state.search_history:
            with st.container(key="sky-history", horizontal=True, vertical_alignment="center", gap="small"):
                st.caption("RECENT")
                for city in st.session_state.search_history:
                    key = f'history_{city["latitude"]}_{city["longitude"]}'
                    if st.button(city["name"], key=key, type="tertiary", help=city.get("country") or city["name"]):
                        st.session_state.selected_city = city

        city = st.session_state.selected_city
        try:
            with st.spinner("Gathering the latest weather…"):
                weather = cached_weather(city["latitude"], city["longitude"])
            render_dashboard(city, weather, unit)
        except WeatherError as error:
            st.html(section_heading("Weather is temporarily unavailable"))
            st.error(str(error))
            st.info("Try the search above or come back in a moment to load the latest conditions.")

        st.html('<footer class="sky-footer"><span>Weather by <a href="https://open-meteo.com/" target="_blank" '
                'rel="noopener noreferrer">Open-Meteo</a></span><span>All times are local to the city · Forecasts are estimates</span></footer>')


if __name__ == "__main__":
    main()

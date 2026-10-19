"""Presentation helpers and original vector artwork for the Skyline dashboard.

The weather symbols in this module are original project artwork, released under
CC0-1.0. They are bundled with the app and require no image or font service.
"""

import base64
from datetime import datetime
from html import escape
import math

from weather import convert_temperature


def parse_time(value):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def local_time(value, date_only=False):
    stamp = parse_time(value)
    if stamp is None:
        return None
    return stamp.strftime("%a %d %b" if date_only else "%I:%M %p").lstrip("0")


def temp_text(value, unit, digits=0):
    converted = convert_temperature(value, unit)
    return f"{converted:.{digits}f}{unit}" if converted is not None else None


def weather_kind(code, is_day=True):
    if is_day is False or is_day == 0:
        return "night"
    if code in (0, 1, 2):
        return "sunny"
    if code in (71, 73, 75, 77, 85, 86):
        return "snowy"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99):
        return "rainy"
    return "cloudy"


def _svg_image(body, viewbox="0 0 120 120", css_class="sky-symbol", alt=""):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}">{body}</svg>'
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return (f'<img class="{css_class}" src="data:image/svg+xml;base64,{encoded}" '
            f'alt="{escape(alt, quote=True)}" draggable="false">')


def weather_icon(code, is_day=True, css_class="sky-symbol", description=""):
    """Build a self-contained, accessible SVG image; no external requests."""
    defs = (
        '<defs><linearGradient id="sun" x2="0.8" y2="1"><stop stop-color="#ffe99a"/>'
        '<stop offset="1" stop-color="#ffb53e"/></linearGradient>'
        '<linearGradient id="cloud" x2=".3" y2="1"><stop stop-color="#fff"/>'
        '<stop offset="1" stop-color="#c8deef"/></linearGradient>'
        '<linearGradient id="moon" x2="1" y2="1"><stop stop-color="#fff2c3"/>'
        '<stop offset="1" stop-color="#e6bd68"/></linearGradient></defs>'
    )
    sun = ('<g stroke="#ffc756" stroke-width="5" stroke-linecap="round">'
           '<path d="M60 9v9m0 84v9M9 60h9m84 0h9M24 24l7 7m58 58 7 7M24 96l7-7m58-58 7-7"/>'
           '</g><circle cx="60" cy="60" r="29" fill="url(#sun)"/>')
    moon = '<path d="M82 17a43 43 0 1 0 19 69A40 40 0 0 1 82 17Z" fill="url(#moon)"/>'
    cloud = ('<path d="M29 87a18 18 0 0 1-3-36 28 28 0 0 1 53-10 23 23 0 1 1 12 46Z" '
             'fill="url(#cloud)" stroke="#b9d1e5" stroke-width="1.4"/>')
    rain = ('<g stroke="#47b7ef" stroke-width="5" stroke-linecap="round">'
            '<path d="m37 96-5 10m29-10-5 10m29-10-5 10"/></g>')
    if code == 0:
        body = sun if is_day else moon
    elif code in (1, 2):
        body = (f'<g transform="translate(9 -2) scale(.73)">{sun if is_day else moon}</g>' + cloud)
    elif code == 3:
        body = cloud
    elif code in (45, 48):
        body = cloud + '<path d="M20 98h65m-53 11h65" stroke="#8caec5" stroke-width="4" stroke-linecap="round"/>'
    elif code in (71, 73, 75, 77, 85, 86):
        body = cloud + '<g fill="#63b8dd"><circle cx="35" cy="101" r="3"/><circle cx="59" cy="107" r="3"/><circle cx="84" cy="100" r="3"/></g>'
    elif code in (95, 96, 99):
        body = cloud + '<path d="m64 77-17 24h12l-5 16 26-28H65l8-12Z" fill="#ffc957"/>'
    elif weather_kind(code) == "rainy":
        body = cloud + rain
    else:
        body = '<rect x="49" y="19" width="22" height="63" rx="11" fill="#cdeaff" stroke="#4195cd" stroke-width="3"/><circle cx="60" cy="89" r="18" fill="#4195cd"/><path d="M60 42v45" stroke="#4195cd" stroke-width="7" stroke-linecap="round"/>'
    return _svg_image(defs + body, css_class=css_class, alt=description)


def detail_icon(name):
    paths = {
        "location": '<path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z"/><circle cx="12" cy="10" r="2.5"/>',
        "humidity": '<path d="M12 3S5 11 5 15a7 7 0 0 0 14 0c0-4-7-12-7-12Z"/><path d="M9 16a3 3 0 0 0 3 3"/>',
        "wind": '<path d="M3 8h12a3 3 0 1 0-3-3M3 12h16a3 3 0 1 1-3 3M3 16h5a3 3 0 1 1-3 3"/>',
        "pressure": '<path d="M4 18a9 9 0 1 1 16 0M12 13l4-5M5 12h1m12 0h1M12 4v1"/><circle cx="12" cy="14" r="2"/>',
        "visibility": '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
        "sunrise": '<path d="M2 17h20M5 13a7 7 0 0 1 14 0M12 1v7m-3-3 3-3 3 3M3 7l2 2m14 0 2-2M5 21h14"/>',
        "sunset": '<path d="M2 17h20M5 13a7 7 0 0 1 14 0M12 1v7m-3-3 3 3 3-3M3 7l2 2m14 0 2-2M5 21h14"/>',
        "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/>',
    }
    body = '<g fill="none" stroke="#49799e" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">' + paths.get(name, paths["clock"]) + '</g>'
    return _svg_image(body, "0 0 24 24", "sky-detail-icon")


def section_heading(title, subtitle=""):
    return (f'<header class="sky-section-heading"><h2>{escape(title)}</h2>'
            f'<span>{escape(subtitle)}</span></header>')


def location_markup(city, weather):
    place = str(city["name"]) + (f", {city['country']}" if city.get("country") else "")
    stamp = parse_time(weather.get("time"))
    date = stamp.strftime("%A, %B %d").replace(" 0", " ") if stamp else ""
    updated = f'Updated {local_time(weather["time"])}' if stamp else ""
    zone = weather.get("timezone") or ""
    return (
        '<div class="sky-location-bar">'
        f'<div class="sky-location">{detail_icon("location")}<span>{escape(place)}</span>'
        f'<span class="sky-location-date">{escape(date)}</span></div>'
        f'<div class="sky-update">{escape(updated)}'
        f'<span>{escape(zone)}</span></div></div>'
    )


def hero_markup(city, weather, unit):
    today = today_forecast(weather)
    is_day = weather.get("is_day") != 0
    condition = weather.get("conditions") or "Current weather"
    converted = convert_temperature(weather["temperature"], unit)
    notes = []
    if weather.get("feels_like") is not None:
        notes.append(f'Feels like {temp_text(weather["feels_like"], unit)}')
    high = temp_text(today.get("max"), unit)
    low = temp_text(today.get("min"), unit)
    limits = []
    if high:
        limits.append(f'<span>High <strong>{escape(high)}</strong></span>')
    if low:
        limits.append(f'<span>Low <strong>{escape(low)}</strong></span>')
    return (
        f'<section class="sky-hero sky-hero--{weather_kind(weather.get("code"), is_day)}" aria-label="Current weather">'
        '<div class="sky-hero-copy"><div class="sky-kicker"><i></i> CURRENT CONDITIONS</div>'
        f'<h1>{escape(str(city["name"]))}</h1>'
        f'<div class="sky-temperature">{converted:.0f}<span>{escape(unit)}</span></div>'
        f'<div class="sky-condition">{escape(condition)}</div>'
        f'<div class="sky-feels">{escape(" · ".join(notes))}</div>'
        f'<div class="sky-limits">{"".join(limits)}</div></div>'
        '<div class="sky-hero-art" aria-hidden="true"><div class="sky-orbit"></div>'
        f'{weather_icon(weather.get("code"), is_day, "sky-hero-symbol")}</div></section>'
    )


def today_forecast(weather):
    current = parse_time(weather.get("time"))
    if not current:
        return {}
    return next((day for day in weather.get("days", []) if day.get("date") == current.date().isoformat()), {})


def details_markup(weather):
    today = today_forecast(weather)
    fields = [
        ("humidity", "Humidity", weather.get("humidity"), "%", 0),
        ("wind", "Wind speed", weather.get("wind"), "km/h", 1),
        ("pressure", "Surface pressure", weather.get("pressure"), "hPa", 0),
        ("visibility", "Visibility", weather.get("visibility") / 1000 if weather.get("visibility") is not None else None, "km", 1),
        ("sunrise", "Sunrise", local_time(today.get("sunrise")), "", None),
        ("sunset", "Sunset", local_time(today.get("sunset")), "", None),
    ]
    cards = []
    for icon, label, value, suffix, digits in fields:
        if value is None:
            continue
        display = f"{value:.{digits}f}" if digits is not None else value
        cards.append(
            '<article class="sky-metric">'
            f'<div class="sky-metric-top">{detail_icon(icon)}<span>{escape(label)}</span></div>'
            f'<div class="sky-metric-value">{escape(display)} <small>{escape(suffix)}</small></div></article>'
        )
    if not cards:
        return '<p class="sky-empty">Additional weather details are unavailable for this location.</p>'
    return '<div class="sky-details-grid">' + ''.join(cards) + '</div>'


def upcoming_hours(weather, count=24):
    now = parse_time(weather.get("time"))
    hours = []
    for hour in weather.get("hours", []):
        stamp = parse_time(hour.get("time"))
        if stamp is None:
            continue
        # Open-Meteo returns local timestamps consistently; malformed mixed
        # offsets should not prevent the rest of the dashboard from rendering.
        try:
            if now is not None and stamp < now:
                continue
        except TypeError:
            continue
        hours.append(hour)
    return sorted(hours, key=lambda hour: hour["time"])[:count]


def hourly_markup(hours, unit):
    cards = []
    for hour in hours[:6]:
        stamp = parse_time(hour.get("time"))
        time = stamp.strftime("%I %p").lstrip("0") if stamp else ""
        rain = hour.get("rain_probability")
        rain_text = f'<span class="sky-hour-rain">{rain:.0f}% rain</span>' if rain is not None else ""
        value = temp_text(hour.get("temperature"), unit)
        cards.append(
            '<article class="sky-hour">'
            f'<span class="sky-hour-time">{escape(time)}</span>'
            f'{weather_icon(hour.get("code"), hour.get("is_day", True), description=hour.get("conditions") or "")}'
            f'<strong>{escape(value or "—")}</strong>{rain_text}</article>'
        )
    return '<div class="sky-hour-grid">' + ''.join(cards) + '</div>'


def daily_markup(weather, unit):
    rows = []
    now = parse_time(weather.get("time"))
    days = weather.get("days", [])
    temperatures = [day[key] for day in days for key in ("min", "max") if day.get(key) is not None]
    floor, ceiling = (min(temperatures), max(temperatures)) if temperatures else (0, 1)
    span = max(ceiling - floor, 1)
    for day in days:
        stamp = parse_time(day.get("date"))
        label = "Today" if now and stamp and stamp.date() == now.date() else stamp.strftime("%a") if stamp else ""
        date = stamp.strftime("%d %b").lstrip("0") if stamp else ""
        high, low = day.get("max"), day.get("min")
        limits = []
        for value, css in ((high, "sky-high"), (low, "sky-low")):
            if value is not None:
                limits.append(f'<span class="{css}">{convert_temperature(value, unit):.0f}°</span>')
        bar = ""
        if high is not None and low is not None and all(math.isfinite(v) for v in (high, low, floor, span)):
            left = max(0, min(100, (low - floor) / span * 100))
            width = max(4, min(100 - left, (high - low) / span * 100))
            bar = f'<div class="sky-range"><i style="left:{left:.1f}%;width:{width:.1f}%"></i></div>'
        rain_details = []
        if day.get("rain_probability") is not None:
            rain_details.append(f'{day["rain_probability"]:.0f}% rain')
        if day.get("rain") is not None:
            rain_details.append(f'{day["rain"]:.1f} mm')
        rain_text = f'<small class="sky-day-rain">{escape(" · ".join(rain_details))}</small>' if rain_details else ""
        rows.append(
            '<article class="sky-day-row">'
            f'<div class="sky-day-name"><strong>{escape(label)}</strong><span>{escape(date)}</span></div>'
            f'{weather_icon(day.get("code"), description=day.get("conditions") or "")}'
            f'<div class="sky-day-condition">{escape(day.get("conditions") or "")}{rain_text}</div>'
            f'<div class="sky-day-temperatures"><div>{"".join(limits)}</div>{bar}</div></article>'
        )
    return '<div class="sky-daily">' + ''.join(rows) + '</div>'

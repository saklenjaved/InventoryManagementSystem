"""Fetch current weather from Open-Meteo (free, no signup)."""

import json
import logging
from urllib.parse import urlencode
from urllib.request import urlopen

logger = logging.getLogger(__name__)

API = 'https://api.open-meteo.com/v1/forecast'

# Common codes → short text (full list: Open-Meteo docs).
_SIMPLE_LABEL = {
    0: 'Clear',
    1: 'Mostly clear',
    2: 'Partly cloudy',
    3: 'Cloudy',
    61: 'Light rain',
    63: 'Rain',
    65: 'Heavy rain',
    95: 'Thunderstorm',
}


def fetch_current_weather(latitude, longitude, location_label, timeout=6):
    """Returns dict with 'ok' True/False. Shop template uses this as-is."""
    query = urlencode(
        {'latitude': latitude, 'longitude': longitude, 'current_weather': 'true'}
    )
    url = f'{API}?{query}'
    try:
        with urlopen(url, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))
    except Exception as exc:
        logger.warning('weather fetch failed: %s', exc)
        return {'ok': False, 'error': 'Weather unavailable'}

    cw = data.get('current_weather')
    if not cw:
        return {'ok': False, 'error': 'No weather data'}

    raw_code = cw.get('weathercode', 0)
    try:
        code = int(raw_code)
    except (TypeError, ValueError):
        code = 0
    return {
        'ok': True,
        'location_label': location_label,
        'temperature_c': round(float(cw.get('temperature', 0)), 1),
        'wind_kmh': round(float(cw.get('windspeed', 0)), 1),
        'summary': _SIMPLE_LABEL.get(code, 'Mixed'),
        'time_utc': cw.get('time', ''),
        'source': 'Open-Meteo',
    }

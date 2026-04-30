"""
weather_api.py — OpenWeatherMap API client.

Usage:
    from utils.weather_api import get_current_weather, get_forecast

If WEATHER_API_KEY is empty, realistic mock data is returned so the
app is fully functional without an API key.
"""

import random
import time
import math
import requests
from datetime import datetime, timedelta
from config import WEATHER_API_KEY, WEATHER_BASE_URL


# ── Public API ────────────────────────────────────────────────────────────────

def get_current_weather(city: str) -> dict:
    """Return current weather for *city*. Falls back to mock if no API key."""
    if not WEATHER_API_KEY:
        return _mock_current(city)

    try:
        url    = f"{WEATHER_BASE_URL}/weather"
        params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric"}
        resp   = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        data   = resp.json()
        return _parse_current(data)
    except Exception as e:
        print(f"[WeatherAPI] Error fetching current weather: {e} — using mock data")
        return _mock_current(city)


def get_forecast(city: str) -> list[dict]:
    """Return 7-day daily forecast for *city*. Falls back to mock if no API key."""
    if not WEATHER_API_KEY:
        return _mock_forecast(city)

    try:
        # OWM free tier provides 5-day / 3-hour forecast
        url    = f"{WEATHER_BASE_URL}/forecast"
        params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric", "cnt": 40}
        resp   = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        data   = resp.json()
        return _parse_forecast(data)
    except Exception as e:
        print(f"[WeatherAPI] Error fetching forecast: {e} — using mock data")
        return _mock_forecast(city)


# ── UV-index helper (OWM /weather has no uvi field) ──────────────────────────

def _estimate_uv(data: dict) -> float:
    """
    Estimate UV index from local solar time using a simple bell-curve proxy.
    Peaks at ~7 around solar noon, 0 at night.  Clouds reduce it by ~40%.
    """
    import math as _math
    # Use timezone offset (seconds) from OWM to get local hour
    tz_offset = data.get("timezone", 0)       # seconds east of UTC
    utc_ts    = data.get("dt", time.time())
    local_hour = ((utc_ts + tz_offset) % 86400) / 3600   # 0-24

    # Cosine bell centred on 12:00, zero outside sunrise/sunset (6-18)
    angle = _math.pi * (local_hour - 6) / 12             # 0 at 06:00, π at 18:00
    solar = max(0.0, _math.sin(angle))                    # 0–1

    # Cloud attenuation (cloudiness 0-100 → reduction factor)
    cloud_pct = data.get("clouds", {}).get("all", 20)
    cloud_factor = 1 - cloud_pct * 0.004                  # 100% cloud → 0.6×

    uv = round(solar * 10 * cloud_factor, 1)              # peak ~10 on clear noon
    return min(12.0, max(0.0, uv))


# ── Parsers ───────────────────────────────────────────────────────────────────

def _parse_current(data: dict) -> dict:
    return {
        "city":        data.get("name", "Unknown"),
        "country":     data.get("sys", {}).get("country", ""),
        "temperature": round(data["main"]["temp"], 1),
        "feels_like":  round(data["main"]["feels_like"], 1),
        "humidity":    data["main"]["humidity"],
        "rainfall":    data.get("rain", {}).get("1h", 0) * 24,  # mm/day estimate
        "wind_speed":  round(data["wind"]["speed"] * 3.6, 1),   # m/s → km/h
        "description": data["weather"][0]["description"].title(),
        "icon":        data["weather"][0]["icon"],
        # uvi is NOT available on the /weather endpoint (only /onecall).
        # Estimate from a simple solar-elevation proxy keyed to local hour.
        "uv_index":    data.get("uvi", _estimate_uv(data)),
        "pressure":    data["main"]["pressure"],
        "visibility":  data.get("visibility", 10000) // 1000,
    }


def _parse_forecast(data: dict) -> list[dict]:
    """Aggregate 3-hour slots into daily summaries (up to 7 days)."""
    daily: dict[str, list] = {}
    for item in data.get("list", []):
        date = item["dt_txt"][:10]
        daily.setdefault(date, []).append(item)

    result = []
    for date, items in list(daily.items())[:7]:
        temps    = [i["main"]["temp"]     for i in items]
        humids   = [i["main"]["humidity"] for i in items]
        rains    = [i.get("rain", {}).get("3h", 0) for i in items]
        winds    = [i["wind"]["speed"]    for i in items]
        desc     = items[len(items)//2]["weather"][0]["description"].title()
        icon     = items[len(items)//2]["weather"][0]["icon"]
        result.append({
            "date":        date,
            "temp_max":    round(max(temps), 1),
            "temp_min":    round(min(temps), 1),
            "temp_avg":    round(sum(temps)/len(temps), 1),
            "humidity":    round(sum(humids)/len(humids), 1),
            "rainfall":    round(sum(rains), 1),
            "wind_speed":  round(sum(winds)/len(winds)*3.6, 1),
            "description": desc,
            "icon":        icon,
        })
    return result


# ── Mock data generators ──────────────────────────────────────────────────────

# City-specific weather "personality" so results feel realistic
_CITY_PROFILES = {
    "default":   {"base_temp": 28, "base_rain": 5,  "base_humid": 70},
    "delhi":     {"base_temp": 32, "base_rain": 3,  "base_humid": 55},
    "mumbai":    {"base_temp": 30, "base_rain": 15, "base_humid": 85},
    "kolkata":   {"base_temp": 31, "base_rain": 10, "base_humid": 80},
    "chennai":   {"base_temp": 33, "base_rain": 8,  "base_humid": 75},
    "bangalore": {"base_temp": 24, "base_rain": 6,  "base_humid": 65},
    "hyderabad": {"base_temp": 30, "base_rain": 4,  "base_humid": 60},
    "pune":      {"base_temp": 27, "base_rain": 5,  "base_humid": 62},
    "jaipur":    {"base_temp": 34, "base_rain": 2,  "base_humid": 45},
    "lucknow":   {"base_temp": 29, "base_rain": 4,  "base_humid": 65},
    "london":    {"base_temp": 15, "base_rain": 4,  "base_humid": 78},
    "paris":     {"base_temp": 17, "base_rain": 3,  "base_humid": 72},
    "new york":  {"base_temp": 18, "base_rain": 4,  "base_humid": 65},
    "tokyo":     {"base_temp": 22, "base_rain": 6,  "base_humid": 75},
    "beijing":   {"base_temp": 20, "base_rain": 3,  "base_humid": 55},
}


def _profile(city: str) -> dict:
    return _CITY_PROFILES.get(city.lower(), _CITY_PROFILES["default"])


_DESCS = [
    ("Partly Cloudy", "02d"), ("Clear Sky", "01d"), ("Overcast Clouds", "04d"),
    ("Light Rain", "10d"), ("Scattered Clouds", "03d"), ("Broken Clouds", "04d"),
    ("Moderate Rain", "10d"), ("Sunny", "01d"),
]


# ── Mock weather cache ───────────────────────────────────────────────────────
# Caches mock responses per city so every API call within a session returns
# the SAME base weather.  Without this, each call gets different random values,
# which makes the What-If Scenario Engine's delta comparisons meaningless.
_mock_cache: dict[str, tuple[float, dict]] = {}
_CACHE_TTL  = 120   # seconds — regenerate mock data every 2 minutes


def _mock_current(city: str) -> dict:
    city_key = city.lower()
    now      = time.time()

    # Return cached snapshot if still fresh
    if city_key in _mock_cache:
        ts, cached = _mock_cache[city_key]
        if now - ts < _CACHE_TTL:
            return dict(cached)   # return a copy so callers can't mutate the cache

    # Generate a fresh snapshot and cache it
    p          = _profile(city)
    temp       = round(p["base_temp"] + random.uniform(-3, 3), 1)
    desc, icon = random.choice(_DESCS)
    snapshot   = {
        "city":        city.title(),
        "country":     "IN",
        "temperature": temp,
        "feels_like":  round(temp + random.uniform(-2, 2), 1),
        "humidity":    min(100, max(20, int(p["base_humid"] + random.uniform(-10, 10)))),
        "rainfall":    round(max(0, p["base_rain"] + random.uniform(-3, 8)), 1),
        "wind_speed":  round(random.uniform(6, 22), 1),
        "description": desc,
        "icon":        icon,
        "uv_index":    round(random.uniform(3, 9), 1),
        "pressure":    random.randint(1005, 1025),
        "visibility":  random.randint(5, 20),
    }
    _mock_cache[city_key] = (now, snapshot)
    return dict(snapshot)


def _mock_forecast(city: str) -> list[dict]:
    p      = _profile(city)
    today  = datetime.now()
    result = []
    for i in range(7):
        day      = today + timedelta(days=i)
        # Gentle sine wave variation across the week
        wave     = math.sin(i * 0.9) * 2.5
        t_avg    = round(p["base_temp"] + wave + random.uniform(-1.5, 1.5), 1)
        t_max    = round(t_avg + random.uniform(3, 6), 1)
        t_min    = round(t_avg - random.uniform(3, 6), 1)
        rain     = round(max(0, p["base_rain"] + random.uniform(-3, 12)), 1)
        desc, icon = random.choice(_DESCS)
        result.append({
            "date":        day.strftime("%Y-%m-%d"),
            "temp_max":    t_max,
            "temp_min":    t_min,
            "temp_avg":    t_avg,
            "humidity":    min(100, max(20, int(p["base_humid"] + random.uniform(-8, 8)))),
            "rainfall":    rain,
            "wind_speed":  round(random.uniform(6, 20), 1),
            "description": desc,
            "icon":        icon,
        })
    return result

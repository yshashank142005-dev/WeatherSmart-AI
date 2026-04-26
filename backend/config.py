"""
config.py — Application configuration and environment variables.
Reads from .env file if present; falls back to sensible defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── OpenWeatherMap API ────────────────────────────────────────────────────────
# Get a FREE key at: https://openweathermap.org/api
# If left empty, the app falls back to realistic mock weather data.
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

# ── Flask ─────────────────────────────────────────────────────────────────────
DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
PORT  = int(os.getenv("PORT", 5000))

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_PATH  = os.path.join(BASE_DIR, "data", "crop_data.csv")
MODEL_PATH = os.path.join(BASE_DIR, "ml", "model.pkl")

# ── Crop configuration ────────────────────────────────────────────────────────
SUPPORTED_CROPS = ["wheat", "rice", "maize", "cotton", "sugarcane", "soybean", "barley"]

# Ideal growing conditions per crop  {temp_min, temp_max, rain_min, rain_max, ph_min, ph_max}
CROP_CONDITIONS = {
    "wheat":     {"temp": (10, 25), "rain": (60, 120),  "ph": (6.0, 7.5), "water_need": 450},
    "rice":      {"temp": (20, 38), "rain": (150, 300),  "ph": (5.0, 6.5), "water_need": 1200},
    "maize":     {"temp": (18, 32), "rain": (80, 180),   "ph": (5.8, 7.0), "water_need": 600},
    "cotton":    {"temp": (22, 35), "rain": (70, 130),   "ph": (6.0, 7.5), "water_need": 700},
    "sugarcane": {"temp": (24, 38), "rain": (100, 200),  "ph": (5.5, 7.0), "water_need": 1500},
    "soybean":   {"temp": (20, 32), "rain": (60, 130),   "ph": (6.0, 7.0), "water_need": 500},
    "barley":    {"temp": (8,  22), "rain": (40,  90),   "ph": (6.5, 8.0), "water_need": 350},
}

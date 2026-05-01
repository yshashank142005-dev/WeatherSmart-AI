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
WEATHER_API_KEY  = os.getenv("WEATHER_API_KEY", "")
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

# ── Flask ─────────────────────────────────────────────────────────────────────
DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
PORT  = int(os.getenv("PORT", 5000))

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_PATH  = os.path.join(BASE_DIR, "data", "crop_data.csv")
MODEL_PATH = os.path.join(BASE_DIR, "ml", "model.pkl")

# ── Supported crops (all 22 from the Kaggle crop recommendation dataset) ──────
SUPPORTED_CROPS = [
    "rice", "maize", "chickpea", "kidneybeans", "pigeonpeas",
    "mothbeans", "mungbean", "blackgram", "lentil",
    "pomegranate", "banana", "mango", "grapes", "watermelon",
    "muskmelon", "apple", "orange", "papaya", "coconut",
    "cotton", "jute", "coffee",
]

# ── Ideal growing conditions per crop ─────────────────────────────────────────
# Keys: temp (°C), rain (mm/month), ph, water_need (mm/year),
#       N, P, K  (kg/ha ratio — Kaggle dataset scale)
CROP_CONDITIONS = {
    "rice": {
        "temp": (20, 38), "rain": (150, 300), "ph": (5.0, 6.5),
        "water_need": 1200,
        "N": (60, 100), "P": (35, 60), "K": (30, 50),
    },
    "maize": {
        "temp": (18, 32), "rain": (80, 180), "ph": (5.8, 7.0),
        "water_need": 600,
        "N": (60, 100), "P": (35, 60), "K": (15, 26),
    },
    "chickpea": {
        "temp": (15, 23), "rain": (60, 100), "ph": (6.5, 8.0),
        "water_need": 350,
        "N": (30, 50), "P": (55, 80), "K": (70, 90),
    },
    "kidneybeans": {
        "temp": (15, 24), "rain": (80, 130), "ph": (5.0, 6.5),
        "water_need": 450,
        "N": (15, 26), "P": (55, 80), "K": (15, 26),
    },
    "pigeonpeas": {
        "temp": (24, 32), "rain": (120, 175), "ph": (5.0, 6.5),
        "water_need": 500,
        "N": (15, 26), "P": (55, 80), "K": (15, 26),
    },
    "mothbeans": {
        "temp": (24, 32), "rain": (36, 65), "ph": (6.5, 7.5),
        "water_need": 280,
        "N": (15, 26), "P": (40, 55), "K": (15, 26),
    },
    "mungbean": {
        "temp": (25, 32), "rain": (36, 65), "ph": (6.2, 7.2),
        "water_need": 300,
        "N": (15, 26), "P": (40, 55), "K": (15, 26),
    },
    "blackgram": {
        "temp": (26, 33), "rain": (55, 80), "ph": (6.5, 7.8),
        "water_need": 320,
        "N": (32, 48), "P": (55, 80), "K": (15, 26),
    },
    "lentil": {
        "temp": (20, 28), "rain": (36, 55), "ph": (6.5, 7.5),
        "water_need": 250,
        "N": (15, 24), "P": (55, 80), "K": (15, 24),
    },
    "pomegranate": {
        "temp": (18, 25), "rain": (82, 130), "ph": (5.5, 7.0),
        "water_need": 600,
        "N": (14, 22), "P": (14, 22), "K": (34, 46),
    },
    "banana": {
        "temp": (24, 30), "rain": (80, 130), "ph": (5.5, 6.8),
        "water_need": 900,
        "N": (82, 118), "P": (65, 98), "K": (42, 58),
    },
    "mango": {
        "temp": (28, 35), "rain": (75, 115), "ph": (5.5, 6.8),
        "water_need": 700,
        "N": (15, 25), "P": (20, 34), "K": (24, 36),
    },
    "grapes": {
        "temp": (20, 27), "rain": (55, 82), "ph": (5.5, 6.8),
        "water_need": 600,
        "N": (18, 28), "P": (115, 150), "K": (174, 224),
    },
    "watermelon": {
        "temp": (22, 30), "rain": (40, 62), "ph": (6.0, 7.2),
        "water_need": 400,
        "N": (82, 118), "P": (14, 22), "K": (42, 58),
    },
    "muskmelon": {
        "temp": (25, 32), "rain": (18, 32), "ph": (6.0, 7.0),
        "water_need": 350,
        "N": (82, 118), "P": (14, 22), "K": (42, 58),
    },
    "apple": {
        "temp": (18, 25), "rain": (88, 135), "ph": (5.5, 6.5),
        "water_need": 800,
        "N": (17, 25), "P": (115, 152), "K": (174, 224),
    },
    "orange": {
        "temp": (20, 26), "rain": (88, 130), "ph": (6.5, 7.5),
        "water_need": 750,
        "N": (15, 25), "P": (12, 20), "K": (7, 13),
    },
    "papaya": {
        "temp": (30, 37), "rain": (112, 170), "ph": (6.2, 7.2),
        "water_need": 850,
        "N": (40, 60), "P": (48, 70), "K": (42, 58),
    },
    "coconut": {
        "temp": (24, 30), "rain": (140, 210), "ph": (5.2, 6.5),
        "water_need": 1200,
        "N": (18, 26), "P": (12, 20), "K": (24, 36),
    },
    "cotton": {
        "temp": (21, 28), "rain": (60, 100), "ph": (6.5, 7.5),
        "water_need": 700,
        "N": (100, 136), "P": (38, 54), "K": (15, 25),
    },
    "jute": {
        "temp": (22, 28), "rain": (140, 210), "ph": (6.2, 7.2),
        "water_need": 900,
        "N": (62, 92), "P": (38, 54), "K": (32, 46),
    },
    "coffee": {
        "temp": (23, 28), "rain": (130, 190), "ph": (6.2, 7.5),
        "water_need": 1100,
        "N": (84, 118), "P": (22, 34), "K": (24, 34),
    },
    # Legacy aliases kept for backwards compatibility
    "wheat": {
        "temp": (10, 25), "rain": (60, 120), "ph": (6.0, 7.5),
        "water_need": 450,
        "N": (80, 120), "P": (40, 60), "K": (30, 50),
    },
    "sugarcane": {
        "temp": (24, 38), "rain": (100, 200), "ph": (5.5, 7.0),
        "water_need": 1500,
        "N": (80, 120), "P": (35, 55), "K": (40, 60),
    },
    "soybean": {
        "temp": (20, 32), "rain": (60, 130), "ph": (6.0, 7.0),
        "water_need": 500,
        "N": (40, 80), "P": (40, 60), "K": (20, 40),
    },
    "barley": {
        "temp": (8, 22), "rain": (40, 90), "ph": (6.5, 8.0),
        "water_need": 350,
        "N": (60, 100), "P": (30, 50), "K": (20, 40),
    },
}

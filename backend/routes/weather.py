"""
weather.py — Weather API routes.

GET /api/weather?city=<city>
GET /api/forecast?city=<city>
"""

from flask import Blueprint, request, jsonify
from utils.weather_api import get_current_weather, get_forecast

weather_bp = Blueprint("weather", __name__)


@weather_bp.route("/api/weather")
def current_weather():
    """Return current weather for the given city."""
    city = request.args.get("city", "Delhi").strip()
    if not city:
        return jsonify({"error": "city parameter is required"}), 400

    data = get_current_weather(city)
    return jsonify({"success": True, "data": data})


@weather_bp.route("/api/forecast")
def forecast():
    """Return 7-day forecast for the given city."""
    city = request.args.get("city", "Delhi").strip()
    if not city:
        return jsonify({"error": "city parameter is required"}), 400

    data = get_forecast(city)
    return jsonify({"success": True, "data": data, "days": len(data)})

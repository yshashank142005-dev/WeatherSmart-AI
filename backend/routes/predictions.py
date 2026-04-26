"""
predictions.py — ML prediction routes.

POST /api/predict
Body: { city, crop, soil_moisture, soil_ph }

POST /api/suitability
Body: { city, soil_moisture, soil_ph }
"""

from flask import Blueprint, request, jsonify
from utils.weather_api import get_current_weather
from utils.risk_scorer  import calculate_risk, calculate_pest_risk
from ml.model           import model_manager

predictions_bp = Blueprint("predictions", __name__)


@predictions_bp.route("/api/predict", methods=["POST"])
def predict():
    """
    Run yield prediction + climate risk + pest risk for a crop + location.
    """
    body = request.get_json(force=True) or {}

    city          = body.get("city",          "Delhi")
    crop          = body.get("crop",          "wheat").lower()
    soil_moisture = float(body.get("soil_moisture", 50))
    soil_ph       = float(body.get("soil_ph",       6.5))

    # Fetch live / mock weather
    weather = get_current_weather(city)

    soil = {"moisture": soil_moisture, "ph": soil_ph}

    # ML prediction
    yield_pred   = model_manager.predict_yield(crop, weather, soil)

    # Risk scoring
    climate_risk = calculate_risk(weather, crop)
    pest_risk    = calculate_pest_risk(weather)

    return jsonify({
        "success": True,
        "city":    city,
        "crop":    crop,
        "weather": weather,
        "soil":    soil,
        "yield_prediction": yield_pred,
        "climate_risk":     climate_risk,
        "pest_risk":        pest_risk,
    })


@predictions_bp.route("/api/suitability", methods=["POST"])
def suitability():
    """
    Rank all crops by predicted suitability for current conditions.
    """
    body = request.get_json(force=True) or {}

    city          = body.get("city",          "Delhi")
    soil_moisture = float(body.get("soil_moisture", 50))
    soil_ph       = float(body.get("soil_ph",       6.5))

    weather  = get_current_weather(city)
    soil     = {"moisture": soil_moisture, "ph": soil_ph}
    rankings = model_manager.rank_crop_suitability(weather, soil)

    return jsonify({
        "success":  True,
        "city":     city,
        "weather":  weather,
        "rankings": rankings,
    })

"""
predictions.py — ML prediction routes.

POST /api/predict
Body: { city, crop, soil_moisture, soil_ph }

POST /api/suitability
Body: { city, soil_moisture, soil_ph }

POST /api/whatif
Body: { city, crop, soil_moisture, soil_ph, temp_delta, rain_delta }
"""

from flask import Blueprint, request, jsonify
from utils.weather_api import get_current_weather
from utils.risk_scorer  import calculate_risk, calculate_pest_risk
from ml.model           import model_manager

predictions_bp = Blueprint("predictions", __name__)


def _validate_crop(crop: str):
    """
    Return a 422 JSON response if *crop* is not in the encoder's known classes,
    otherwise return None (caller continues normally).

    Using 422 Unprocessable Entity: the request is well-formed JSON but the
    value fails semantic validation.
    """
    valid = list(model_manager.encoder.classes_)
    if crop not in valid:
        return jsonify({
            "success": False,
            "error":   "invalid_crop",
            "message": (
                f"'{crop}' is not a recognised crop. "
                f"Valid options are: {', '.join(sorted(valid))}."
            ),
            "valid_crops": sorted(valid),
        }), 422
    return None


@predictions_bp.route("/api/predict", methods=["POST"])
def predict():
    """
    Run yield prediction + climate risk + pest risk for a crop + location.
    """
    body = request.get_json(force=True) or {}

    city          = body.get("city",          "Delhi")
    crop          = body.get("crop",          "wheat").lower().strip()
    soil_moisture = float(body.get("soil_moisture", 50))
    soil_ph       = float(body.get("soil_ph",       6.5))
    soil_N        = body.get("N")   # optional — defaults handled in model
    soil_P        = body.get("P")
    soil_K        = body.get("K")

    # Validate crop before any expensive work
    err = _validate_crop(crop)
    if err:
        return err

    # Fetch live / mock weather
    weather = get_current_weather(city)

    soil = {"moisture": soil_moisture, "ph": soil_ph}
    if soil_N is not None: soil["N"] = float(soil_N)
    if soil_P is not None: soil["P"] = float(soil_P)
    if soil_K is not None: soil["K"] = float(soil_K)

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
    soil_N        = body.get("N")
    soil_P        = body.get("P")
    soil_K        = body.get("K")

    weather = get_current_weather(city)
    soil    = {"moisture": soil_moisture, "ph": soil_ph}
    if soil_N is not None: soil["N"] = float(soil_N)
    if soil_P is not None: soil["P"] = float(soil_P)
    if soil_K is not None: soil["K"] = float(soil_K)

    rankings = model_manager.rank_crop_suitability(weather, soil)

    return jsonify({
        "success":  True,
        "city":     city,
        "weather":  weather,
        "rankings": rankings,
    })


@predictions_bp.route("/api/whatif", methods=["POST"])
def whatif():
    """
    What-If Scenario Engine.
    Applies user-specified temperature and rainfall deltas to the live
    weather snapshot, then compares original vs modified predictions.
    """
    body = request.get_json(force=True) or {}

    city          = body.get("city",          "Delhi")
    crop          = body.get("crop",          "wheat").lower().strip()
    soil_moisture = float(body.get("soil_moisture", 50))
    soil_ph       = float(body.get("soil_ph",       6.5))
    temp_delta    = float(body.get("temp_delta",    0))
    rain_delta    = float(body.get("rain_delta",    0))
    soil_N        = body.get("N")
    soil_P        = body.get("P")
    soil_K        = body.get("K")

    # Validate crop before any expensive work
    err = _validate_crop(crop)
    if err:
        return err

    # Fetch live weather (once)
    weather = get_current_weather(city)
    soil    = {"moisture": soil_moisture, "ph": soil_ph}
    if soil_N is not None: soil["N"] = float(soil_N)
    if soil_P is not None: soil["P"] = float(soil_P)
    if soil_K is not None: soil["K"] = float(soil_K)

    # ── Original predictions ──────────────────────────────────────────
    orig_yield   = model_manager.predict_yield(crop, weather, soil)
    orig_climate = calculate_risk(weather, crop)
    orig_pest    = calculate_pest_risk(weather)

    # ── Build modified weather snapshot ──────────────────────────────
    mod_weather = dict(weather)
    mod_weather["temperature"] = round(weather.get("temperature", 25) + temp_delta, 1)
    mod_weather["rainfall"]    = round(max(0, weather.get("rainfall", 5) + rain_delta), 1)

    # ── Scenario predictions ──────────────────────────────────────────
    scen_yield   = model_manager.predict_yield(crop, mod_weather, soil)
    scen_climate = calculate_risk(mod_weather, crop)
    scen_pest    = calculate_pest_risk(mod_weather)

    yield_delta = round(
        scen_yield["yield_index"] - orig_yield["yield_index"], 1
    )

    return jsonify({
        "success": True,
        "city":    city,
        "crop":    crop,
        "deltas":  {"temp": temp_delta, "rain": rain_delta},
        "yield_delta": yield_delta,
        "original": {
            "weather":          weather,
            "yield_prediction": orig_yield,
            "climate_risk":     orig_climate,
            "pest_risk":        orig_pest,
        },
        "scenario": {
            "weather":          mod_weather,
            "yield_prediction": scen_yield,
            "climate_risk":     scen_climate,
            "pest_risk":        scen_pest,
        },
    })

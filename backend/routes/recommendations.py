"""
recommendations.py — Hybrid (rule + ML) farming recommendation engine.

POST /api/recommend
Body: { city, crop, soil_moisture, soil_ph }

POST /api/irrigation
Body: { city, crop, soil_moisture, soil_ph }

POST /api/alert
Body: { city, crop }
"""

from flask import Blueprint, request, jsonify
from utils.weather_api  import get_current_weather, get_forecast
from utils.risk_scorer  import calculate_risk, calculate_pest_risk
from utils.irrigation   import calculate_irrigation
from utils.notifier     import send_email, send_sms, send_in_app, get_in_app_notifications
from ml.model           import model_manager
from config             import CROP_CONDITIONS

recommendations_bp = Blueprint("recommendations", __name__)


# ── Recommendation engine ─────────────────────────────────────────────────────

def _generate_recommendations(crop, weather, soil, yield_pred, climate_risk, pest_risk):
    """
    Hybrid rule-based + ML recommendation generator.
    Returns a categorised list of actionable recommendations.
    """
    recs  = []
    t     = weather.get("temperature", 25)
    h     = weather.get("humidity",    65)
    r     = weather.get("rainfall",    5)
    w     = weather.get("wind_speed",  10)
    ph    = soil.get("ph",             6.5)
    moist = soil.get("moisture",       50)
    yi    = yield_pred.get("yield_index", 70)
    cond  = CROP_CONDITIONS.get(crop, {})

    # ── Temperature advice ───────────────────────────────────────────
    t_range = cond.get("temp", (15, 35))
    if t > t_range[1]:
        recs.append({"category": "Temperature", "priority": "high",
                     "icon": "🌡️",
                     "message": f"Temperature ({t}°C) exceeds ideal for {crop}. "
                                "Use shade nets and increase irrigation frequency."})
    elif t < t_range[0]:
        recs.append({"category": "Temperature", "priority": "high",
                     "icon": "❄️",
                     "message": f"Temperature ({t}°C) is too low for {crop}. "
                                "Use plastic mulch or frost covers to retain soil heat."})
    else:
        recs.append({"category": "Temperature", "priority": "low",
                     "icon": "✅",
                     "message": f"Temperature ({t}°C) is ideal for {crop}. No action needed."})

    # ── Rainfall / water advice ──────────────────────────────────────
    r_range = cond.get("rain", (80, 150))
    if r < r_range[0] / 30:           # daily equivalent
        recs.append({"category": "Irrigation", "priority": "high",
                     "icon": "💧",
                     "message": "Low rainfall detected. Begin supplemental irrigation. "
                                "Prefer drip irrigation to minimise water loss."})
    elif r > r_range[1] / 20:
        recs.append({"category": "Drainage", "priority": "medium",
                     "icon": "🌊",
                     "message": "Excess rainfall risk. Ensure proper field drainage. "
                                "Delay fertiliser application to prevent nutrient washout."})
    else:
        recs.append({"category": "Irrigation", "priority": "low",
                     "icon": "✅",
                     "message": "Rainfall levels are adequate. Monitor soil moisture and irrigate only if it drops below 40%."})

    # ── Soil pH advice ───────────────────────────────────────────────
    ph_range = cond.get("ph", (6.0, 7.5))
    if ph < ph_range[0]:
        recs.append({"category": "Soil Health", "priority": "medium",
                     "icon": "🧪",
                     "message": f"Soil pH ({ph}) is too acidic for {crop} (ideal: {ph_range[0]}–{ph_range[1]}). "
                                "Apply agricultural lime (calcium carbonate) to raise pH."})
    elif ph > ph_range[1]:
        recs.append({"category": "Soil Health", "priority": "medium",
                     "icon": "🧪",
                     "message": f"Soil pH ({ph}) is too alkaline for {crop} (ideal: {ph_range[0]}–{ph_range[1]}). "
                                "Apply elemental sulphur or acidic organic matter (peat moss) to lower pH."})
    else:
        recs.append({"category": "Soil Health", "priority": "low",
                     "icon": "✅",
                     "message": f"Soil pH ({ph}) is in the ideal range for {crop}."})

    # ── Soil moisture advice ─────────────────────────────────────────
    if moist < 30:
        recs.append({"category": "Soil Moisture", "priority": "high",
                     "icon": "🏜️",
                     "message": f"Soil moisture ({moist}%) is critically low. "
                                "Irrigate immediately and apply organic mulch to retain moisture."})
    elif moist > 75:
        recs.append({"category": "Soil Moisture", "priority": "medium",
                     "icon": "💦",
                     "message": f"Soil moisture ({moist}%) is very high. "
                                "Pause irrigation and improve drainage to prevent root rot."})

    # ── Humidity / disease advice ────────────────────────────────────
    if h > 85:
        recs.append({"category": "Disease Prevention", "priority": "high",
                     "icon": "🍄",
                     "message": "High humidity favours fungal diseases. "
                                "Apply preventive fungicide spray and ensure canopy ventilation."})

    # ── Pest risk advice ─────────────────────────────────────────────
    if pest_risk["level"] in ("medium", "high"):
        for threat in pest_risk["threats"][:2]:
            recs.append({"category": "Pest Alert", "priority": "high" if pest_risk["level"] == "high" else "medium",
                         "icon": "🐛",
                         "message": f"{threat} risk detected. Scout fields immediately and consider targeted pesticide application."})

    # ── Wind advice ──────────────────────────────────────────────────
    if w > 40:
        recs.append({"category": "Wind", "priority": "high",
                     "icon": "💨",
                     "message": f"High wind speeds ({w} km/h). Avoid spraying pesticides/fertilisers. "
                                "Install windbreaks to prevent crop lodging."})

    # ── ML-based yield nudge ─────────────────────────────────────────
    if yi < 50:
        recs.append({"category": "Yield Improvement", "priority": "high",
                     "icon": "📉",
                     "message": f"ML model predicts low yield index ({yi}/100). "
                                "Consider crop variety switching, applying balanced NPK fertiliser, "
                                "and consulting an agronomist."})
    elif yi >= 80:
        recs.append({"category": "Yield Outlook", "priority": "low",
                     "icon": "🌾",
                     "message": f"Excellent yield conditions predicted ({yi}/100). "
                                "Maintain current practices and prepare for harvest logistics."})

    # Sort: high → medium → low
    priority_order = {"high": 0, "medium": 1, "low": 2}
    recs.sort(key=lambda x: priority_order.get(x["priority"], 3))

    return recs


# ── Routes ────────────────────────────────────────────────────────────────────

@recommendations_bp.route("/api/recommend", methods=["POST"])
def recommend():
    """Generate full hybrid recommendations."""
    body = request.get_json(force=True) or {}

    city          = body.get("city",          "Delhi")
    crop          = body.get("crop",          "wheat").lower()
    soil_moisture = float(body.get("soil_moisture", 50))
    soil_ph       = float(body.get("soil_ph",       6.5))

    weather      = get_current_weather(city)
    soil         = {"moisture": soil_moisture, "ph": soil_ph}
    yield_pred   = model_manager.predict_yield(crop, weather, soil)
    climate_risk = calculate_risk(weather, crop)
    pest_risk    = calculate_pest_risk(weather)
    recs         = _generate_recommendations(crop, weather, soil, yield_pred, climate_risk, pest_risk)

    return jsonify({
        "success":         True,
        "city":            city,
        "crop":            crop,
        "recommendations": recs,
        "total":           len(recs),
    })


@recommendations_bp.route("/api/irrigation", methods=["POST"])
def irrigation():
    """Generate smart irrigation schedule."""
    body = request.get_json(force=True) or {}

    city          = body.get("city",          "Delhi")
    crop          = body.get("crop",          "wheat").lower()
    soil_moisture = float(body.get("soil_moisture", 50))
    soil_ph       = float(body.get("soil_ph",       6.5))

    weather  = get_current_weather(city)
    forecast = get_forecast(city)
    soil     = {"moisture": soil_moisture, "ph": soil_ph}
    schedule = calculate_irrigation(crop, weather, forecast, soil_moisture)

    return jsonify({"success": True, "schedule": schedule})


@recommendations_bp.route("/api/alert", methods=["POST"])
def alert():
    """
    Check for extreme weather and dispatch real notifications.

    Body:
      { city, crop,
        email?       — recipient email address
        phone?       — recipient phone number (E.164, e.g. +919876543210)
        channels?    — list: ["email", "sms", "inapp"]  (default: ["inapp"])
      }
    """
    body     = request.get_json(force=True) or {}
    city     = body.get("city",     "Delhi")
    crop     = body.get("crop",     "wheat").lower()
    email    = body.get("email",    "").strip()
    phone    = body.get("phone",    "").strip()
    channels = [c.lower() for c in body.get("channels", ["inapp"])]

    weather = get_current_weather(city)
    t = weather.get("temperature", 25)
    r = weather.get("rainfall",    5)
    w = weather.get("wind_speed",  10)
    h = weather.get("humidity",    65)

    alerts = []

    if t > 40:
        alerts.append({
            "type":     "HEAT_WAVE",
            "severity": "critical",
            "message":  f"⚠️ HEAT WAVE ALERT: Temperature {t}°C in {city}. "
                        f"Immediate action needed to protect {crop} crops.",
            "action":   "Increase irrigation, apply shade nets, avoid field work 11 AM–4 PM."
        })

    if t < 5:
        alerts.append({
            "type":     "FROST",
            "severity": "critical",
            "message":  f"❄️ FROST ALERT: Temperature {t}°C in {city}. Risk of crop damage.",
            "action":   "Cover crops with frost cloth, use smudge pots or heaters if available."
        })

    if r > 50:
        alerts.append({
            "type":     "HEAVY_RAIN",
            "severity": "high",
            "message":  f"🌧️ HEAVY RAIN ALERT: {r} mm/day in {city}. Flooding risk.",
            "action":   "Open drainage channels, halt irrigation, delay fertiliser application."
        })

    if w > 60:
        alerts.append({
            "type":     "STRONG_WIND",
            "severity": "high",
            "message":  f"💨 STRONG WIND ALERT: {w} km/h in {city}. Crop lodging risk.",
            "action":   "Stake tall crops, postpone spraying operations."
        })

    if h > 92:
        alerts.append({
            "type":     "HIGH_HUMIDITY",
            "severity": "medium",
            "message":  f"💧 HIGH HUMIDITY ALERT: {h}% in {city}. Disease outbreak risk.",
            "action":   "Apply preventive fungicide, improve canopy airflow."
        })

    # ── Dispatch notifications ────────────────────────────────────────────────
    dispatch_results = {}

    if alerts:  # only send if there are actual alerts
        if "inapp" in channels or not channels:
            dispatch_results["inapp"] = send_in_app(alerts, city)

        if "email" in channels and email:
            dispatch_results["email"] = send_email(email, alerts, city)
        elif "email" in channels and not email:
            dispatch_results["email"] = {"success": False, "message": "No email address provided"}

        if "sms" in channels and phone:
            dispatch_results["sms"] = send_sms(phone, alerts, city)
        elif "sms" in channels and not phone:
            dispatch_results["sms"] = {"success": False, "message": "No phone number provided"}
    else:
        dispatch_results["inapp"] = {"success": True, "message": "No alerts to dispatch"}

    return jsonify({
        "success":          True,
        "city":             city,
        "alerts":           alerts,
        "alert_count":      len(alerts),
        "dispatch_results": dispatch_results,
    })


@recommendations_bp.route("/api/notifications", methods=["GET"])
def notifications():
    """Return all in-app notifications for the bell icon / notification feed."""
    items  = get_in_app_notifications()
    unread = sum(1 for n in items if not n["read"])
    return jsonify({"success": True, "notifications": items, "unread": unread})

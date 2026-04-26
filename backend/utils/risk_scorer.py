"""
risk_scorer.py — Climate Risk Scoring Engine.

Evaluates current weather conditions and returns a risk level
(low / medium / high) along with contributing risk factors.
"""

from config import CROP_CONDITIONS


# ── Risk thresholds ───────────────────────────────────────────────────────────

RISK_RULES = {
    "extreme_heat":     {"condition": lambda t, **_: t > 40,       "weight": 3, "label": "Extreme heat stress"},
    "high_heat":        {"condition": lambda t, **_: t > 35,       "weight": 2, "label": "High temperature"},
    "extreme_cold":     {"condition": lambda t, **_: t < 5,        "weight": 3, "label": "Frost / freeze risk"},
    "low_cold":         {"condition": lambda t, **_: t < 12,       "weight": 1, "label": "Below-optimal temperature"},
    "heavy_rain":       {"condition": lambda r, **_: r > 50,       "weight": 3, "label": "Heavy rainfall / flooding risk"},
    "moderate_rain":    {"condition": lambda r, **_: r > 25,       "weight": 1, "label": "Moderate excess rainfall"},
    "drought":          {"condition": lambda r, **_: r < 2,        "weight": 2, "label": "Drought / dry conditions"},
    "high_humidity":    {"condition": lambda h, **_: h > 90,       "weight": 2, "label": "High humidity (disease risk)"},
    "low_humidity":     {"condition": lambda h, **_: h < 30,       "weight": 1, "label": "Low humidity (transpiration stress)"},
    "strong_wind":      {"condition": lambda w, **_: w > 50,       "weight": 2, "label": "Strong wind (crop lodging)"},
}


def calculate_risk(weather: dict, crop: str = None) -> dict:
    """
    Compute a climate risk score for the given weather snapshot.

    Parameters
    ----------
    weather : dict   Keys: temperature, humidity, rainfall, wind_speed
    crop    : str    Optional crop name for crop-specific risk adjustment

    Returns
    -------
    dict with keys: level, score, factors, crop_specific_notes
    """

    t = weather.get("temperature", 25)
    h = weather.get("humidity",    65)
    r = weather.get("rainfall",    5)
    w = weather.get("wind_speed",  10)

    # Evaluate each rule
    triggered_factors = []
    total_weight      = 0

    for key, rule in RISK_RULES.items():
        # Pass only the params the lambda accepts
        args = {"t": t, "h": h, "r": r, "w": w}
        try:
            if rule["condition"](**args):
                triggered_factors.append(rule["label"])
                total_weight += rule["weight"]
        except TypeError:
            pass

    # Normalise to 0-100 score
    max_possible = sum(r["weight"] for r in RISK_RULES.values())
    score        = min(100, round(total_weight / max_possible * 100))

    # Determine level
    if score < 25:
        level = "low"
    elif score < 55:
        level = "medium"
    else:
        level = "high"

    # Crop-specific notes
    notes = []
    if crop and crop in CROP_CONDITIONS:
        cond    = CROP_CONDITIONS[crop]
        t_range = cond["temp"]
        r_range = cond["rain"]
        ph      = cond.get("ph", (6.0, 7.5))

        if t < t_range[0]:
            notes.append(f"Temperature is below the ideal range for {crop} ({t_range[0]}–{t_range[1]}°C)")
        elif t > t_range[1]:
            notes.append(f"Temperature is above the ideal range for {crop} ({t_range[0]}–{t_range[1]}°C)")

        if r < r_range[0]:
            notes.append(f"Rainfall is insufficient for {crop} (needs ≥{r_range[0]} mm/month)")
        elif r > r_range[1]:
            notes.append(f"Excess rainfall for {crop} (max {r_range[1]} mm/month tolerated)")

    return {
        "level":               level,
        "score":               score,
        "factors":             triggered_factors if triggered_factors else ["No significant risk factors detected"],
        "crop_specific_notes": notes,
    }


def calculate_pest_risk(weather: dict) -> dict:
    """
    Predict pest and disease risk based on weather patterns.
    Returns risk level and list of likely threats.
    """
    t = weather.get("temperature", 25)
    h = weather.get("humidity",    65)
    r = weather.get("rainfall",    5)

    threats = []
    risk_score = 0

    # Fungal diseases thrive in warm, humid, wet conditions
    if h > 80 and t > 20:
        threats.append("Fungal blight / leaf spot")
        risk_score += 2
    if h > 85 and r > 10:
        threats.append("Powdery mildew / downy mildew")
        risk_score += 2

    # Insect pests prefer warm and dry
    if t > 28 and h < 65:
        threats.append("Aphid / whitefly infestation")
        risk_score += 1
    if t > 32 and h < 55:
        threats.append("Thrips / spider mites")
        risk_score += 2

    # Locust conditions
    if t > 30 and r < 3 and weather.get("wind_speed", 0) > 20:
        threats.append("Locust swarm risk")
        risk_score += 3

    # Bacterial infections in waterlogged soils
    if r > 30:
        threats.append("Root rot / bacterial wilt (waterlogging)")
        risk_score += 2

    max_score = 12
    score = min(100, round(risk_score / max_score * 100))

    return {
        "level":   "high" if score > 55 else ("medium" if score > 25 else "low"),
        "score":   score,
        "threats": threats if threats else ["No significant pest/disease risk detected"],
    }

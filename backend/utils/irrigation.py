"""
irrigation.py — Smart Irrigation Scheduler.

Computes irrigation frequency and duration recommendations based on:
  - Crop water requirements
  - Forecast rainfall (next 7 days)
  - Soil moisture
  - Current evapotranspiration proxy (temperature + wind)
"""

from config import CROP_CONDITIONS


def calculate_irrigation(crop: str, weather: dict, forecast: list, soil_moisture: float) -> dict:
    """
    Generate an irrigation schedule for the current week.

    Parameters
    ----------
    crop          : str    Crop type
    weather       : dict   Current weather snapshot
    forecast      : list   7-day forecast list (each item has rainfall, temp_avg, wind_speed)
    soil_moisture : float  Current soil moisture % (0-100)

    Returns
    -------
    dict with schedule, daily_plan, total_water_needed, savings_tip
    """

    cond = CROP_CONDITIONS.get(crop, CROP_CONDITIONS["wheat"])
    weekly_water_need = cond["water_need"] / 52  # mm/week from annual need

    # Estimate total forecast rainfall this week
    forecast_rain = sum(day.get("rainfall", 0) for day in forecast[:7])

    # Evapotranspiration proxy (Hargreaves simplified)
    avg_temp  = weather.get("temperature", 25)
    wind      = weather.get("wind_speed",  10)
    et_factor = max(0.8, 1 + (avg_temp - 20) * 0.03 + (wind - 10) * 0.01)
    adjusted_need = weekly_water_need * et_factor

    # Net irrigation need after rainfall
    net_need   = max(0, adjusted_need - forecast_rain)

    # Adjust for soil moisture (less irrigation if soil already moist)
    moisture_factor = max(0.2, 1 - (soil_moisture / 100) * 0.6)
    final_need      = round(net_need * moisture_factor, 1)

    # Decide frequency
    if final_need < 5:
        frequency  = "No irrigation needed this week"
        sessions   = 0
        per_session = 0
    elif final_need < 20:
        sessions   = 2
        per_session = round(final_need / sessions, 1)
        frequency  = f"Irrigate {sessions}x this week ({per_session} mm each)"
    elif final_need < 40:
        sessions   = 3
        per_session = round(final_need / sessions, 1)
        frequency  = f"Irrigate {sessions}x this week ({per_session} mm each)"
    else:
        sessions   = 5
        per_session = round(final_need / sessions, 1)
        frequency  = f"Irrigate {sessions}x this week ({per_session} mm each)"

    # Build daily plan for the week
    daily_plan = _build_daily_plan(sessions, per_session, forecast)

    # Savings tip
    tip = _savings_tip(soil_moisture, forecast_rain, avg_temp, crop)

    return {
        "crop":               crop,
        "weekly_water_need":  round(adjusted_need, 1),
        "forecast_rainfall":  round(forecast_rain, 1),
        "net_irrigation_need": final_need,
        "soil_moisture":      soil_moisture,
        "frequency":          frequency,
        "sessions_per_week":  sessions,
        "mm_per_session":     per_session,
        "daily_plan":         daily_plan,
        "savings_tip":        tip,
    }


def _build_daily_plan(sessions: int, per_session: float, forecast: list) -> list:
    """Assign irrigation sessions across the week, skipping rainy days."""
    from datetime import datetime, timedelta

    plan  = []
    today = datetime.now()
    done  = 0

    # Prefer days with low rainfall for irrigation
    day_rains = [(i, forecast[i]["rainfall"] if i < len(forecast) else 0) for i in range(7)]
    sorted_days = sorted(day_rains, key=lambda x: x[1])

    # Only assign irrigation to days with < 10 mm expected rainfall.
    # If there are fewer eligible days than requested sessions, use what's available
    # rather than spilling into rainy days (which would produce contradictory plans).
    LOW_RAIN_THRESHOLD = 10.0
    eligible_days = [d for d in sorted_days if d[1] < LOW_RAIN_THRESHOLD]
    irrigate_days = set(d[0] for d in eligible_days[:sessions]) if sessions > 0 else set()

    for i in range(7):
        date   = (today + timedelta(days=i)).strftime("%a, %b %d")
        rain   = forecast[i]["rainfall"] if i < len(forecast) else 0
        if i in irrigate_days and done < sessions:
            plan.append({"day": date, "action": f"Irrigate {per_session} mm", "rainfall": rain, "irrigate": True})
            done += 1
        elif rain >= LOW_RAIN_THRESHOLD:
            plan.append({"day": date, "action": "Skip — rainfall expected", "rainfall": rain, "irrigate": False})
        else:
            plan.append({"day": date, "action": "Monitor soil moisture", "rainfall": rain, "irrigate": False})

    return plan


def _savings_tip(moisture: float, forecast_rain: float, temp: float, crop: str) -> str:
    """Generate a context-aware water-saving tip."""
    if moisture > 70:
        return "Soil is already moist. Delay irrigation to avoid waterlogging and root diseases."
    if forecast_rain > 30:
        return "Significant rainfall expected this week. Rely on natural rainfall and reduce irrigation."
    if temp > 35:
        return "High temperatures detected. Irrigate in the early morning (5–7 AM) to minimise evaporation."
    if crop in ("rice", "sugarcane"):
        return f"Drip irrigation can save up to 40% water for {crop} while maintaining yield."
    return "Use mulching to retain soil moisture and reduce irrigation frequency by up to 30%."

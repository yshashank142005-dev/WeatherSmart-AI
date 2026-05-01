"""
generate_dataset.py — Generate a 2200-row crop recommendation dataset
inspired by the Kaggle Crop Recommendation Dataset (NPK + climate + yield_index).

Crops (22, 100 rows each):
  rice, maize, chickpea, kidneybeans, pigeonpeas, mothbeans, mungbean,
  blackgram, lentil, pomegranate, banana, mango, grapes, watermelon,
  muskmelon, apple, orange, papaya, coconut, cotton, jute, coffee

Columns:
  N, P, K, temperature, humidity, ph, rainfall,
  wind_speed, soil_moisture, crop_type, yield_index

yield_index (0-100) is derived from a Gaussian distance-to-optimum formula
so conditions perfectly at the crop's ideal → ~90-95, extremes → ~20-30.

Run from: backend/data/
  python generate_dataset.py
"""

import random
import math
import csv
import os

random.seed(42)

# ── Crop profiles ────────────────────────────────────────────────────────────
# Each tuple: (N_mean, N_std, P_mean, P_std, K_mean, K_std,
#              temp_mean, temp_std, humid_mean, humid_std,
#              ph_mean, ph_std, rain_mean, rain_std)
# Based on Kaggle Crop Recommendation Dataset distribution statistics.

CROPS = {
    "rice":        (80, 15, 48, 12, 40, 10, 23.7, 1.5, 82.0, 3.5, 6.4, 0.4, 236, 35),
    "maize":       (77, 18, 48, 14, 20, 8,  22.6, 1.8, 65.0, 5.0, 6.3, 0.4, 84,  25),
    "chickpea":    (40, 12, 68, 14, 80, 14, 18.9, 2.2, 16.9, 3.2, 7.3, 0.3, 80,  22),
    "kidneybeans": (20, 8,  68, 14, 20, 8,  19.0, 2.0, 22.0, 4.0, 5.7, 0.4, 105, 28),
    "pigeonpeas":  (20, 8,  68, 14, 20, 8,  27.8, 1.5, 48.1, 5.0, 5.8, 0.4, 149, 30),
    "mothbeans":   (21, 8,  48, 12, 20, 7,  28.2, 2.0, 53.2, 5.5, 6.9, 0.3, 51,  18),
    "mungbean":    (21, 8,  48, 12, 20, 7,  28.5, 1.8, 85.5, 4.0, 6.7, 0.3, 49,  15),
    "blackgram":   (40, 12, 68, 14, 20, 8,  29.9, 1.5, 65.1, 5.0, 7.1, 0.3, 68,  20),
    "lentil":      (19, 7,  68, 14, 19, 7,  24.5, 2.0, 65.0, 5.5, 6.9, 0.3, 45,  15),
    "pomegranate": (18, 7,  18, 6,  40, 10, 21.8, 2.5, 90.1, 4.0, 6.0, 0.4, 108, 28),
    "banana":      (100,20, 82, 18, 50, 12, 27.4, 1.5, 80.9, 4.0, 6.0, 0.4, 105, 30),
    "mango":       (20, 8,  27, 8,  30, 10, 31.2, 2.0, 50.1, 5.0, 6.0, 0.4, 94,  25),
    "grapes":      (23, 8,  133,20, 200,30, 23.8, 2.0, 82.0, 4.5, 6.1, 0.4, 69,  20),
    "watermelon":  (100,20, 18, 6,  50, 12, 25.6, 1.8, 85.0, 4.0, 6.5, 0.4, 51,  15),
    "muskmelon":   (100,20, 18, 6,  50, 12, 28.7, 1.8, 92.3, 3.5, 6.4, 0.3, 25,  10),
    "apple":       (21, 7,  134,22, 200,28, 21.9, 2.5, 92.3, 3.5, 5.9, 0.4, 113, 28),
    "orange":      (20, 7,  16, 5,  10, 4,  23.0, 2.0, 92.2, 3.5, 7.0, 0.4, 110, 28),
    "papaya":      (50, 12, 59, 14, 50, 12, 33.7, 1.5, 92.1, 3.5, 6.7, 0.3, 142, 32),
    "coconut":     (22, 8,  16, 5,  30, 8,  27.4, 1.5, 94.8, 3.0, 5.9, 0.4, 175, 35),
    "cotton":      (118,20, 46, 12, 20, 7,  24.0, 2.5, 79.9, 5.0, 6.9, 0.3, 80,  22),
    "jute":        (78, 15, 46, 12, 39, 10, 24.9, 1.5, 80.0, 4.5, 6.7, 0.3, 175, 35),
    "coffee":      (101,18, 28, 8,  29, 8,  25.5, 1.5, 58.5, 5.0, 6.8, 0.3, 159, 35),
}

# Ideal ranges for yield_index calculation (N, P, K, temp, humid, ph, rain)
IDEAL = {
    "rice":        {"N":(60,100), "P":(35,60),  "K":(30,50),  "t":(22,26), "h":(78,88),  "ph":(5.8,7.0), "r":(175,280)},
    "maize":       {"N":(60,100), "P":(35,60),  "K":(15,26),  "t":(20,26), "h":(55,75),  "ph":(5.8,7.0), "r":(60,110)},
    "chickpea":    {"N":(30,50),  "P":(55,80),  "K":(70,90),  "t":(17,22), "h":(13,21),  "ph":(7.0,7.8), "r":(60,100)},
    "kidneybeans": {"N":(15,26),  "P":(55,80),  "K":(15,26),  "t":(17,22), "h":(18,26),  "ph":(5.3,6.2), "r":(80,130)},
    "pigeonpeas":  {"N":(15,26),  "P":(55,80),  "K":(15,26),  "t":(26,30), "h":(43,54),  "ph":(5.3,6.3), "r":(120,175)},
    "mothbeans":   {"N":(15,26),  "P":(40,55),  "K":(15,26),  "t":(26,31), "h":(47,59),  "ph":(6.6,7.3), "r":(36,65)},
    "mungbean":    {"N":(15,26),  "P":(40,55),  "K":(15,26),  "t":(26,31), "h":(81,90),  "ph":(6.4,7.1), "r":(36,65)},
    "blackgram":   {"N":(32,48),  "P":(55,80),  "K":(15,26),  "t":(28,32), "h":(60,70),  "ph":(6.8,7.5), "r":(55,80)},
    "lentil":      {"N":(15,24),  "P":(55,80),  "K":(15,24),  "t":(22,27), "h":(60,70),  "ph":(6.6,7.3), "r":(36,55)},
    "pomegranate": {"N":(14,22),  "P":(14,22),  "K":(34,46),  "t":(19,24), "h":(86,94),  "ph":(5.6,6.6), "r":(82,130)},
    "banana":      {"N":(82,118), "P":(65,98),  "K":(42,58),  "t":(26,29), "h":(76,85),  "ph":(5.6,6.5), "r":(80,130)},
    "mango":       {"N":(15,25),  "P":(20,34),  "K":(24,36),  "t":(29,33), "h":(45,56),  "ph":(5.6,6.5), "r":(75,115)},
    "grapes":      {"N":(18,28),  "P":(115,150),"K":(174,224),"t":(22,26), "h":(78,86),  "ph":(5.8,6.5), "r":(55,82)},
    "watermelon":  {"N":(82,118), "P":(14,22),  "K":(42,58),  "t":(24,28), "h":(81,89),  "ph":(6.2,7.0), "r":(40,62)},
    "muskmelon":   {"N":(82,118), "P":(14,22),  "K":(42,58),  "t":(27,31), "h":(89,96),  "ph":(6.2,6.8), "r":(18,32)},
    "apple":       {"N":(17,25),  "P":(115,152),"K":(174,224),"t":(20,24), "h":(89,96),  "ph":(5.5,6.3), "r":(88,135)},
    "orange":      {"N":(15,25),  "P":(12,20),  "K":(7,13),   "t":(21,25), "h":(89,96),  "ph":(6.7,7.4), "r":(88,130)},
    "papaya":      {"N":(40,60),  "P":(48,70),  "K":(42,58),  "t":(32,36), "h":(89,96),  "ph":(6.4,7.1), "r":(112,170)},
    "coconut":     {"N":(18,26),  "P":(12,20),  "K":(24,36),  "t":(26,29), "h":(91,98),  "ph":(5.5,6.3), "r":(140,210)},
    "cotton":      {"N":(100,136),"P":(38,54),  "K":(15,25),  "t":(22,27), "h":(74,86),  "ph":(6.6,7.4), "r":(60,100)},
    "jute":        {"N":(62,92),  "P":(38,54),  "K":(32,46),  "t":(23,27), "h":(75,85),  "ph":(6.4,7.1), "r":(140,210)},
    "coffee":      {"N":(84,118), "P":(22,34),  "K":(24,34),  "t":(24,27), "h":(54,63),  "ph":(6.5,7.2), "r":(130,190)},
}


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _gaussian_score(value, lo, hi):
    """Score 0-1: 1.0 when inside [lo,hi], decays as Gaussian outside."""
    mid   = (lo + hi) / 2
    width = (hi - lo) / 2 or 1
    dist  = max(0, abs(value - mid) - width)
    return math.exp(-0.5 * (dist / width) ** 2)


def yield_index(crop, N, P, K, temp, humid, ph, rain):
    """Compute yield_index 0-100 from agronomic proximity to ideal ranges."""
    ideal = IDEAL[crop]
    scores = [
        _gaussian_score(N,    *ideal["N"]),
        _gaussian_score(P,    *ideal["P"]),
        _gaussian_score(K,    *ideal["K"]),
        _gaussian_score(temp, *ideal["t"]),
        _gaussian_score(humid,*ideal["h"]),
        _gaussian_score(ph,   *ideal["ph"]),
        _gaussian_score(rain, *ideal["r"]),
    ]
    avg = sum(scores) / len(scores)
    # Scale to 20-95 range (realistic: even bad conditions get ≥20)
    raw = 20 + avg * 75
    # Add small noise
    raw += random.gauss(0, 2)
    return round(_clamp(raw, 5, 98), 1)


def rng(mean, std, lo=None, hi=None, decimals=1):
    v = random.gauss(mean, std)
    if lo is not None: v = max(lo, v)
    if hi is not None: v = min(hi, v)
    return round(v, decimals)


ROWS_PER_CROP = 100

# For each crop we generate three tiers so the model sees the full yield spectrum:
#  Tier A (~40 rows): near-ideal conditions  → yield 72-95
#  Tier B (~35 rows): moderate stress         → yield 45-72
#  Tier C (~25 rows): severe stress           → yield 15-45
# This prevents the model from seeing only high-yield rows and failing to learn gradients.

def _tier_sample(crop, tier):
    """
    Generate one row for a given crop and stress tier.
    tier: 'A' (near-ideal), 'B' (moderate stress), 'C' (severe stress)
    """
    Nm,Ns,Pm,Ps,Km,Ks,tm,ts,hm,hs,phm,phs,rm,rs = CROPS[crop]
    ideal = IDEAL[crop]

    if tier == "A":
        # Sample tightly around crop ideal means (low variance)
        N    = rng(Nm, Ns * 0.5,  0, 140, 0)
        P    = rng(Pm, Ps * 0.5,  5, 145, 0)
        K    = rng(Km, Ks * 0.5,  5, 205, 0)
        temp = rng(tm, ts * 0.5,  8,  44, 1)
        hum  = rng(hm, hs * 0.5, 14, 100, 1)
        ph   = rng(phm, phs * 0.5, 3.5, 9.5, 2)
        rain = rng(rm, rs * 0.5, 10, 300, 1)
    elif tier == "B":
        # Moderate offset: pull some features outside ideal range
        N    = rng(Nm * random.choice([0.55, 1.45]), Ns, 0, 140, 0)
        P    = rng(Pm * random.choice([0.55, 1.45]), Ps, 5, 145, 0)
        K    = rng(Km * random.choice([0.55, 1.45]), Ks, 5, 205, 0)
        temp = rng(tm + random.choice([-5, 5]),      ts, 8,  44, 1)
        hum  = rng(hm + random.choice([-15, 15]),    hs, 14, 100, 1)
        ph   = rng(phm + random.choice([-0.8, 0.8]), phs, 3.5, 9.5, 2)
        rain = rng(rm * random.choice([0.4, 1.7]),   rs, 10, 300, 1)
    else:  # tier C — severe stress
        # Pick values well outside ideal, drawn from global extremes
        N    = rng(random.choice([10, 130]),  20,  0, 140, 0)
        P    = rng(random.choice([8,  140]),  20,  5, 145, 0)
        K    = rng(random.choice([8,  200]),  20,  5, 205, 0)
        temp = rng(random.choice([10, 42]),   2,   8,  44, 1)
        hum  = rng(random.choice([15, 98]),   5,  14, 100, 1)
        ph   = rng(random.choice([4.0, 8.5]), 0.3, 3.5, 9.5, 2)
        rain = rng(random.choice([15, 280]),  20,  10, 300, 1)

    wind  = rng(12, 5, 2, 35, 1)
    moist = rng(50, 15, 10, 90, 1)
    yi    = yield_index(crop, N, P, K, temp, hum, ph, rain)
    return [N, P, K, temp, hum, ph, rain, wind, moist, crop, yi]


rows = []
for crop in CROPS:
    for _ in range(40):  # Tier A — near-ideal
        rows.append(_tier_sample(crop, "A"))
    for _ in range(35):  # Tier B — moderate stress
        rows.append(_tier_sample(crop, "B"))
    for _ in range(25):  # Tier C — severe stress
        rows.append(_tier_sample(crop, "C"))

random.shuffle(rows)

out_path = os.path.join(os.path.dirname(__file__), "crop_data.csv")
with open(out_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["N", "P", "K", "temperature", "humidity", "ph",
                     "rainfall", "wind_speed", "soil_moisture", "crop_type", "yield_index"])
    writer.writerows(rows)

print(f"[OK] Generated {len(rows)} rows -> {out_path}")
print(f"     Crops: {len(CROPS)}, rows/crop: 100 (40A + 35B + 25C)")

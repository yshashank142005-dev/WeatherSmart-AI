"""
model.py — Machine Learning models for WeatherSmart AI.

Models:
  1. CropYieldPredictor  — RandomForestRegressor → yield_index (0-100)
  2. CropSuitabilityRanker — ranks all crops for given conditions

Both are wrapped in a single ModelManager that handles
training, persistence (joblib), and inference.
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble        import GradientBoostingRegressor
from sklearn.preprocessing   import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics         import r2_score, mean_absolute_error
from sklearn.pipeline        import Pipeline
from sklearn.preprocessing   import StandardScaler

from config import DATA_PATH, MODEL_PATH, SUPPORTED_CROPS, CROP_CONDITIONS


# ── Feature columns used for training ────────────────────────────────────────
# Matches the Kaggle-style 2200-row dataset columns (minus crop_type / yield_index)
FEATURE_COLS = [
    "N", "P", "K",                                    # soil nutrients (kg/ha)
    "temperature", "humidity", "ph", "rainfall",       # climate + soil pH
    "wind_speed", "soil_moisture",                     # additional agro features
    "crop_encoded",                                    # label-encoded crop
]

TARGET_COL   = "yield_index"


# ── Model Manager ─────────────────────────────────────────────────────────────

class ModelManager:
    """
    Singleton-style manager that owns both the yield predictor
    and the label encoder.  Call .load_or_train() on startup.
    """

    def __init__(self):
        self.model                 = None
        self.encoder               = LabelEncoder().fit(SUPPORTED_CROPS)
        self.feature_importances_  = {}
        self.train_r2              = 0.0
        self.train_mae             = 0.0

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def load_or_train(self):
        """Load saved model from disk, or train from scratch if absent/corrupted."""
        if os.path.exists(MODEL_PATH):
            print("[ML] Loading model from disk …")
            try:
                bundle = joblib.load(MODEL_PATH)
                # Validate all expected keys are present (guards against schema changes)
                required = {"model", "encoder", "importances", "r2", "mae"}
                missing  = required - bundle.keys()
                if missing:
                    raise KeyError(f"Bundle is missing keys: {missing}")

                self.model                = bundle["model"]
                self.encoder              = bundle["encoder"]
                self.feature_importances_ = bundle["importances"]
                self.train_r2             = bundle["r2"]
                self.train_mae            = bundle["mae"]
                print(f"[ML] Model loaded — R²={self.train_r2:.3f}, MAE={self.train_mae:.2f}")

            except Exception as e:
                print(f"[ML] WARNING: Failed to load model from {MODEL_PATH} — {e}")
                print("[ML] Deleting corrupted file and retraining from scratch …")
                try:
                    os.remove(MODEL_PATH)
                except OSError as rm_err:
                    print(f"[ML] Could not delete corrupted model file: {rm_err}")
                self.train()
        else:
            print("[ML] No saved model found — training now …")
            self.train()

    def train(self):
        """Train RandomForest on crop_data.csv and persist to disk."""
        df = pd.read_csv(DATA_PATH)

        # Drop rows where crop_type isn't in SUPPORTED_CROPS (e.g. legacy aliases)
        df = df[df["crop_type"].isin(self.encoder.classes_)].reset_index(drop=True)

        # Encode crop type
        df["crop_encoded"] = self.encoder.transform(df["crop_type"])

        X = df[FEATURE_COLS].values
        y = df[TARGET_COL].values

        # Stratify by crop so all 22 crops appear in both train & test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42,
            stratify=df["crop_encoded"].values,
        )

        # GradientBoosting handles non-linear multi-crop yield curves well
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("gb",     GradientBoostingRegressor(
                n_estimators=400,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                min_samples_leaf=3,
                random_state=42,
            )),
        ])

        pipeline.fit(X_train, y_train)
        preds = pipeline.predict(X_test)

        self.model     = pipeline
        self.train_r2  = round(r2_score(y_test, preds), 4)
        self.train_mae = round(mean_absolute_error(y_test, preds), 3)

        # Extract feature importances from the GB inside the pipeline
        gb_step     = pipeline.named_steps["gb"]
        importances = gb_step.feature_importances_
        self.feature_importances_ = {
            col: round(float(imp), 4)
            for col, imp in zip(FEATURE_COLS, importances)
        }

        print(f"[ML] Training complete — R²={self.train_r2}, MAE={self.train_mae}")
        print(f"[ML] Feature importances: {self.feature_importances_}")

        # Save bundle
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        joblib.dump({
            "model":       self.model,
            "encoder":     self.encoder,
            "importances": self.feature_importances_,
            "r2":          self.train_r2,
            "mae":         self.train_mae,
        }, MODEL_PATH)
        print(f"[ML] Model saved to {MODEL_PATH}")

    # ── Inference ─────────────────────────────────────────────────────────

    def predict_yield(self, crop: str, weather: dict, soil: dict) -> dict:
        """
        Predict crop yield index for the given inputs.

        Parameters
        ----------
        weather : dict  Keys: temperature, humidity, rainfall, wind_speed
        soil    : dict  Keys: moisture, ph, N, P, K  (NPK default to crop midpoint)

        Returns dict: yield_index, confidence, feature_importances, interpretation
        """
        if self.model is None:
            self.load_or_train()

        crop_enc = self._encode_crop(crop)

        # Resolve NPK defaults from CROP_CONDITIONS if not supplied
        cond = CROP_CONDITIONS.get(crop, {})
        def _npk_mid(key, fallback):
            rng = cond.get(key)
            return soil.get(key, (rng[0] + rng[1]) / 2 if rng else fallback)

        features = np.array([[
            _npk_mid("N", 80),
            _npk_mid("P", 40),
            _npk_mid("K", 40),
            weather.get("temperature",  25),
            weather.get("humidity",     65),
            soil.get("ph",              6.5),
            weather.get("rainfall",     5),
            weather.get("wind_speed",   10),
            soil.get("moisture",        50),
            crop_enc,
        ]])

        raw_yield   = float(self.model.predict(features)[0])
        yield_index = round(max(0, min(100, raw_yield)), 1)

        # Confidence: use std-dev across individual GB stage predictions (proper uncertainty).
        # GradientBoosting doesn't have .estimators_ the same way — use staged_predict std.
        # Fallback: use train R² scaled confidence clamped to [0, 98].
        try:
            gb_step  = self.model.named_steps["gb"]
            scaler   = self.model.named_steps["scaler"]
            X_scaled = scaler.transform(features)
            # staged_predict gives cumulative predictions per boosting round
            staged   = np.array(list(gb_step.staged_predict(X_scaled)))
            std_dev  = float(staged.std())
            confidence = round(max(0, min(98, 100 - std_dev * 3)), 1)
        except Exception:
            confidence = round(max(0, min(98, self.train_r2 * 100 - abs(yield_index - 50) * 0.2)), 1)

        interpretation = (
            "Excellent yield expected"   if yield_index >= 80 else
            "Good yield expected"        if yield_index >= 65 else
            "Moderate yield expected"    if yield_index >= 50 else
            "Below-average yield risk"   if yield_index >= 35 else
            "Poor yield — action needed"
        )

        return {
            "yield_index":         yield_index,
            "confidence":          confidence,
            "interpretation":      interpretation,
            "feature_importances": self.feature_importances_,
            "model_r2":            self.train_r2,
        }

    def rank_crop_suitability(self, weather: dict, soil: dict) -> list:
        """
        Predict yield index for ALL supported crops under the same conditions.
        Returns a ranked list from best to worst.
        """
        if self.model is None:
            self.load_or_train()

        results = []
        for crop in SUPPORTED_CROPS:
            pred = self.predict_yield(crop, weather, soil)
            results.append({
                "crop":        crop,
                "yield_index": pred["yield_index"],
                "suitability": _suitability_label(pred["yield_index"]),
            })

        results.sort(key=lambda x: x["yield_index"], reverse=True)

        for i, r in enumerate(results, 1):
            r["rank"] = i

        return results

    # ── Helpers ───────────────────────────────────────────────────────────

    def _encode_crop(self, crop: str) -> int:
        """Encode crop name to integer, defaulting to 0 for unknown crops."""
        crop = crop.lower()
        if crop in self.encoder.classes_:
            return int(self.encoder.transform([crop])[0])
        return 0


def _suitability_label(yield_index: float) -> str:
    if yield_index >= 80: return "Excellent"
    if yield_index >= 65: return "Good"
    if yield_index >= 50: return "Moderate"
    if yield_index >= 35: return "Poor"
    return "Not Suitable"


# ── Module-level singleton ────────────────────────────────────────────────────
model_manager = ModelManager()

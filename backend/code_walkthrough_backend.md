# WeatherSmart AI — Backend Code Walkthrough

> [!TIP]
> Read this file by file, top to bottom. Each code block is explained in plain English.

---

## 1. [config.py](file:///C:/sem4/antigravity/demo/backend/config.py) — App Settings

```python
from dotenv import load_dotenv
load_dotenv()
```
**What it does:** Loads variables from a `.env` file (if it exists) into the environment. This lets you store secrets like API keys outside your code.

```python
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
```
**What it does:** Reads the weather API key from environment. If not set, defaults to empty string `""` — the app will then use **mock data** instead of real weather.

```python
DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
PORT  = int(os.getenv("PORT", 5000))
```
**What it does:** Flask debug mode (auto-reload on code changes) and port number. Defaults: debug=on, port=5000.

```python
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_PATH  = os.path.join(BASE_DIR, "data", "crop_data.csv")
MODEL_PATH = os.path.join(BASE_DIR, "ml", "model.pkl")
```
**What it does:** Builds absolute file paths relative to this file's location. `__file__` is the current file, `abspath` makes it absolute, `dirname` gets the folder. This ensures paths work regardless of where you run `python` from.

```python
CROP_CONDITIONS = {
    "wheat": {"temp": (10, 25), "rain": (60, 120), "ph": (6.0, 7.5), "water_need": 450},
    ...
}
```
**What it does:** A dictionary defining ideal growing conditions for each crop. Used throughout the app for rule-based recommendations. For example, wheat grows best at 10-25°C with 60-120mm rain/month.

---

## 2. [main.py](file:///C:/sem4/antigravity/demo/backend/main.py) — App Entry Point

```python
from flask import Flask
from flask_cors import CORS
```
**What it does:** Imports Flask (the web framework) and CORS (Cross-Origin Resource Sharing — allows the React frontend on port 5173 to call the API on port 5000).

```python
def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
```
**What it does:** Factory function that creates the Flask app. `CORS` allows any origin (`*`) to access `/api/*` routes. Without this, the browser would block frontend→backend requests.

```python
    app.register_blueprint(weather_bp)
    app.register_blueprint(predictions_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(chatbot_bp)
```
**What it does:** Blueprints are Flask's way of organizing routes into modules. Each blueprint file defines its own routes, and `register_blueprint` plugs them into the main app.

```python
model_manager.load_or_train()
```
**What it does:** Runs ONCE at startup. Checks if a trained model file (`model.pkl`) exists on disk — if yes, loads it; if no, trains a new model from the CSV data. This is why you see "Training complete" in the console the first time.

```python
app.run(debug=DEBUG, port=PORT, host="0.0.0.0")
```
**What it does:** Starts the server. `0.0.0.0` means listen on all network interfaces (not just localhost), so other devices on your network can access it too.

---

## 3. [ml/model.py](file:///C:/sem4/antigravity/demo/backend/ml/model.py) — ML Brain

### The ModelManager Class

```python
class ModelManager:
    def __init__(self):
        self.model = None
        self.encoder = LabelEncoder().fit(SUPPORTED_CROPS)
```
**What it does:** `LabelEncoder` converts crop names (strings) into numbers: wheat→6, rice→3, maize→2, etc. ML models can only work with numbers, not text.

### Training

```python
def train(self):
    df = pd.read_csv(DATA_PATH)
    df["crop_encoded"] = self.encoder.transform(df["crop_type"])
```
**What it does:** Reads the CSV dataset into a Pandas DataFrame. Then adds a new column `crop_encoded` — converting crop names like "wheat" into numbers.

```python
    X = df[FEATURE_COLS].values   # Input features (7 columns)
    y = df[TARGET_COL].values     # Target: yield_index (0-100)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
```
**What it does:** `X` = the input data (temperature, humidity, rainfall, wind, moisture, pH, crop). `y` = what we want to predict (yield index). `train_test_split` keeps 80% for training, 20% for testing. `random_state=42` makes the split reproducible.

```python
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("rf", RandomForestRegressor(n_estimators=200, max_depth=10, ...)),
    ])
```
**What it does:** A Pipeline chains two steps:
1. **StandardScaler** — normalizes features so they're all on the same scale (e.g., temperature ~30 vs humidity ~70)
2. **RandomForestRegressor** — 200 decision trees vote together. `max_depth=10` prevents overfitting. `n_jobs=-1` uses all CPU cores.

```python
    pipeline.fit(X_train, y_train)        # Train the model
    preds = pipeline.predict(X_test)      # Test predictions
    self.train_r2 = r2_score(y_test, preds)   # How good? (1.0 = perfect)
    self.train_mae = mean_absolute_error(...)  # Average error in units
```
**What it does:** `.fit()` trains the model. `.predict()` runs it on unseen test data. R²=0.99 means the model explains 99% of the variance. MAE=1.15 means predictions are off by ~1.15 points on average.

```python
    joblib.dump({...}, MODEL_PATH)
```
**What it does:** Saves the trained model to disk as `model.pkl` so you don't have to retrain every time the server restarts.

### Prediction

```python
def predict_yield(self, crop, weather, soil):
    features = np.array([[temp, humidity, rainfall, wind, moisture, ph, crop_enc]])
    raw_yield = float(self.model.predict(features)[0])
    yield_index = round(max(0, min(100, raw_yield)), 1)
```
**What it does:** Assembles the 7 input features into a numpy array, feeds it to the model, and clamps the result between 0-100.

### Suitability Ranking

```python
def rank_crop_suitability(self, weather, soil):
    for crop in SUPPORTED_CROPS:
        pred = self.predict_yield(crop, weather, soil)
        results.append(...)
    results.sort(key=lambda x: x["yield_index"], reverse=True)
```
**What it does:** Runs yield prediction for ALL 7 crops under the same conditions, then sorts best→worst. This tells the farmer "given today's weather and your soil, rice is best, wheat is second..."

---

## 4. [utils/weather_api.py](file:///C:/sem4/antigravity/demo/backend/utils/weather_api.py) — Weather Data

```python
def get_current_weather(city):
    if not WEATHER_API_KEY:
        return _mock_current(city)
```
**What it does:** If no API key is configured, returns realistic fake data. This is why the app works without any setup.

```python
    resp = requests.get(url, params=params, timeout=8)
    resp.raise_for_status()
```
**What it does:** Makes an HTTP GET to OpenWeatherMap. `timeout=8` gives up after 8 seconds. `raise_for_status()` throws an error if the API returns 4xx/5xx.

### Mock Data System

```python
_CITY_PROFILES = {
    "delhi":  {"base_temp": 32, "base_rain": 3, "base_humid": 55},
    "mumbai": {"base_temp": 30, "base_rain": 15, "base_humid": 85},
    ...
}
```
**What it does:** Each city has a "personality" — Mumbai is hotter/wetter than Delhi. Mock data adds random noise around these baselines so it feels realistic.

```python
def _mock_forecast(city):
    wave = math.sin(i * 0.9) * 2.5  # Gentle temperature variation
```
**What it does:** Uses a sine wave to create natural-looking temperature variation across the 7-day forecast instead of random noise.

---

## 5. [utils/risk_scorer.py](file:///C:/sem4/antigravity/demo/backend/utils/risk_scorer.py) — Risk Engine

```python
RISK_RULES = {
    "extreme_heat": {"condition": lambda t, **_: t > 40, "weight": 3, "label": "Extreme heat stress"},
    ...
}
```
**What it does:** Each rule is a lambda function that checks one condition. `**_` means "accept and ignore any extra keyword arguments". Weight determines severity (3=critical, 1=minor).

```python
score = min(100, round(total_weight / max_possible * 100))
level = "high" if score > 55 else ("medium" if score > 25 else "low")
```
**What it does:** Adds up weights of all triggered rules, normalizes to 0-100, then classifies as low/medium/high.

### Pest Risk

```python
if h > 80 and t > 20:
    threats.append("Fungal blight / leaf spot")
```
**What it does:** Rule-based pest prediction. Warm + humid = fungal diseases. Hot + dry = insect pests. These are real agricultural heuristics.

---

## 6. [utils/irrigation.py](file:///C:/sem4/antigravity/demo/backend/utils/irrigation.py) — Water Scheduler

```python
weekly_water_need = cond["water_need"] / 52  # mm/week from annual need
et_factor = max(0.8, 1 + (avg_temp - 20) * 0.03 + (wind - 10) * 0.01)
adjusted_need = weekly_water_need * et_factor
```
**What it does:** Converts annual water need to weekly. Then adjusts for evapotranspiration — hotter/windier conditions mean more water evaporates, so the crop needs more irrigation.

```python
net_need = max(0, adjusted_need - forecast_rain)
moisture_factor = max(0.2, 1 - (soil_moisture / 100) * 0.6)
final_need = round(net_need * moisture_factor, 1)
```
**What it does:** Subtracts expected rainfall (why irrigate if it's going to rain?). Then reduces further if soil is already moist. The result is the **actual** irrigation needed.

```python
sorted_days = sorted(day_rains, key=lambda x: x[1])  # Sort by rainfall
irrigate_days = set(d[0] for d in sorted_days[:sessions])
```
**What it does:** Picks the driest days of the week for irrigation. No point irrigating on a rainy day.

---

## 7. Route Files

### [routes/weather.py](file:///C:/sem4/antigravity/demo/backend/routes/weather.py)
Simple pass-through routes: takes `?city=Delhi` query param, calls `get_current_weather()` or `get_forecast()`, returns JSON.

### [routes/predictions.py](file:///C:/sem4/antigravity/demo/backend/routes/predictions.py)
Takes POST body `{city, crop, soil_moisture, soil_ph}`, fetches weather, runs ML prediction + risk scoring, returns everything as JSON.

### [routes/recommendations.py](file:///C:/sem4/antigravity/demo/backend/routes/recommendations.py)
The `_generate_recommendations()` function checks ~10 conditions (temp too high? pH wrong? pests likely?) and builds a list of actionable advice cards, sorted by priority.

### [routes/chatbot.py](file:///C:/sem4/antigravity/demo/backend/routes/chatbot.py)
```python
INTENTS = [
    {"patterns": [r"wheat|gehu|गेहूँ"], "responses": {"en": "...", "hi": "..."}},
    ...
]
```
**What it does:** Pattern-matching chatbot. Each intent has regex patterns and bilingual responses. `re.search(pattern, msg)` checks if the user's message matches. First match wins. If nothing matches, returns a fallback message.

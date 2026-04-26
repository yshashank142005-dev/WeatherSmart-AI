"""
chatbot.py — Keyword + pattern-based agricultural chatbot.

POST /api/chatbot
Body: { message: str, lang: "en" | "hi" }
"""

import re
from flask import Blueprint, request, jsonify

chatbot_bp = Blueprint("chatbot", __name__)

INTENTS = [
    {
        "patterns": [r"hello|hi|hey|namaste"],
        "responses": {
            "en": "👋 Hello! I'm WeatherSmart AI. Ask me about crops, weather, irrigation, or pests!",
            "hi": "👋 नमस्ते! मैं WeatherSmart AI हूँ। फसल, मौसम, सिंचाई के बारे में पूछें!",
        },
    },
    {
        "patterns": [r"wheat|gehu|गेहूँ"],
        "responses": {
            "en": "🌾 **Wheat:** Ideal temp 10–25°C, needs ~450 mm water/season. Sow Oct–Nov. Apply 120:60:40 NPK/ha. Watch for rust disease in humid conditions.",
            "hi": "🌾 **गेहूँ:** आदर्श तापमान 10–25°C, ~450 मिमी पानी/सीज़न। अक्टूबर–नवंबर में बुवाई। नम परिस्थितियों में रतुआ रोग से सावधान।",
        },
    },
    {
        "patterns": [r"rice|paddy|dhan|धान|chawal"],
        "responses": {
            "en": "🌾 **Rice:** Ideal temp 20–38°C, needs ~1200 mm/season. Transplant June–July. Maintain 5 cm standing water. Watch for blast disease.",
            "hi": "🌾 **धान:** आदर्श तापमान 20–38°C, ~1200 मिमी/सीज़न। जून–जुलाई में रोपाई। 5 सेमी खड़ा पानी बनाए रखें। ब्लास्ट रोग से सावधान।",
        },
    },
    {
        "patterns": [r"maize|corn|makka|मक्का"],
        "responses": {
            "en": "🌽 **Maize:** Ideal temp 18–32°C, ~600 mm/season. Sow June–July. Space rows 60–75 cm. Risk: Fall Armyworm in warm/humid weather.",
            "hi": "🌽 **मक्का:** आदर्श तापमान 18–32°C, ~600 मिमी/सीज़न। जून–जुलाई में बुवाई। पंक्तियाँ 60–75 सेमी की दूरी पर।",
        },
    },
    {
        "patterns": [r"cotton|kapas|कपास"],
        "responses": {
            "en": "🪴 **Cotton:** Ideal temp 22–35°C, ~700 mm/season. Sow April–May. Sensitive to waterlogging. Watch for bollworm and whitefly.",
            "hi": "🪴 **कपास:** आदर्श तापमान 22–35°C, ~700 मिमी/सीज़न। अप्रैल–मई में बुवाई। जलजमाव से संवेदनशील।",
        },
    },
    {
        "patterns": [r"irrigation|water|sinchai|सिंचाई|pani|पानी"],
        "responses": {
            "en": "💧 **Irrigation Tips:**\n• Irrigate early morning (5–7 AM)\n• Drip irrigation saves 40–60% water\n• Check soil moisture first — ideal: 40–70%\n• Skip if ≥10 mm rain expected",
            "hi": "💧 **सिंचाई सुझाव:**\n• सुबह जल्दी सिंचाई करें (5–7 बजे)\n• ड्रिप सिंचाई 40–60% पानी बचाती है\n• पहले मिट्टी की नमी जांचें — आदर्श: 40–70%",
        },
    },
    {
        "patterns": [r"pest|insect|disease|keet|कीट|rog|बीमारी"],
        "responses": {
            "en": "🐛 **Pest Management:**\n• Scout fields weekly\n• Use neem oil for mild infestations\n• Rotate crops yearly\n• High humidity (>80%) → apply preventive fungicide\n• IPM reduces chemical use by 40%",
            "hi": "🐛 **कीट प्रबंधन:**\n• साप्ताहिक खेतों का सर्वेक्षण करें\n• हल्के संक्रमण के लिए नीम का तेल\n• फसल चक्र अपनाएं\n• उच्च आर्द्रता (>80%) → फफूंदनाशक लगाएं",
        },
    },
    {
        "patterns": [r"soil|mitti|मिट्टी|ph"],
        "responses": {
            "en": "🌱 **Soil Health:**\n• Ideal pH for most crops: 6.0–7.0\n• Add lime to raise pH (acidic)\n• Add sulphur to lower pH (alkaline)\n• Aim for >2% organic matter\n• Deep plough every 3 years",
            "hi": "🌱 **मिट्टी स्वास्थ्य:**\n• अधिकांश फसलों के लिए आदर्श pH: 6.0–7.0\n• pH बढ़ाने के लिए चूना मिलाएं\n• pH कम करने के लिए सल्फर\n• >2% जैविक पदार्थ का लक्ष्य",
        },
    },
    {
        "patterns": [r"fertilizer|fertiliser|khad|खाद|urea|यूरिया"],
        "responses": {
            "en": "🧴 **Fertiliser Tips:**\n• Test soil before applying\n• Split N: 50% sowing, 25% tillering, 25% heading\n• Avoid before heavy rain\n• Compost improves water retention\n• Typical cereal NPK ratio: 4:2:1",
            "hi": "🧴 **उर्वरक सुझाव:**\n• पहले मिट्टी परीक्षण करें\n• नाइट्रोजन विभाजित करें: 50% बुवाई, 25% कल्ले, 25% शीर्षारोहण\n• भारी बारिश से पहले न डालें",
        },
    },
    {
        "patterns": [r"weather|forecast|mausam|मौसम|baarish|बारिश"],
        "responses": {
            "en": "🌤️ Use the **Weather** and **Forecast** panels for live conditions and 7-day predictions. Select your city in the sidebar.",
            "hi": "🌤️ लाइव मौसम और 7-दिन पूर्वानुमान के लिए **मौसम** और **पूर्वानुमान** पैनल देखें।",
        },
    },
    {
        "patterns": [r"yield|production|upaj|उत्पाद|paidavar"],
        "responses": {
            "en": "📊 The **Predictions** tab uses a Random Forest ML model to predict yield index (0–100). Score >75 = excellent conditions!",
            "hi": "📊 **पूर्वानुमान** टैब Random Forest ML मॉडल का उपयोग करके उपज सूचकांक (0-100) की भविष्यवाणी करता है। 75 से अधिक = उत्कृष्ट!",
        },
    },
    {
        "patterns": [r"help|features|madad|मदद|sahayata|सहायता"],
        "responses": {
            "en": "🤖 I can help with:\n• 🌾 Crop advice (wheat, rice, maize, cotton, soybean…)\n• 💧 Irrigation scheduling\n• 🐛 Pest & disease management\n• 🧪 Soil health & fertilisers\n• 🌤️ Weather interpretation\n• 📊 Yield predictions\n\nJust ask!",
            "hi": "🤖 मैं मदद कर सकता हूँ:\n• 🌾 फसल सलाह\n• 💧 सिंचाई\n• 🐛 कीट प्रबंधन\n• 🧪 मिट्टी स्वास्थ्य\n• 🌤️ मौसम\n• 📊 उपज पूर्वानुमान\n\nबस पूछें!",
        },
    },
    {
        "patterns": [r"thank|thanks|धन्यवाद|shukriya"],
        "responses": {
            "en": "😊 You're welcome! Happy farming!",
            "hi": "😊 आपका स्वागत है! खुशहाल खेती!",
        },
    },
]

FALLBACK = {
    "en": "🤔 I'm not sure about that. Try asking about crops, irrigation, pests, soil, or weather. Type **help** for all topics!",
    "hi": "🤔 मुझे इसके बारे में निश्चित नहीं है। फसलों, सिंचाई, कीट, मिट्टी के बारे में पूछें। सभी विषय देखने के लिए **help** टाइप करें!",
}


def match_intent(message: str, lang: str) -> str:
    msg = message.lower().strip()
    for intent in INTENTS:
        for pattern in intent["patterns"]:
            if re.search(pattern, msg, re.IGNORECASE):
                r = intent["responses"]
                return r.get(lang, r.get("en", ""))
    return FALLBACK.get(lang, FALLBACK["en"])


@chatbot_bp.route("/api/chatbot", methods=["POST"])
def chatbot():
    body    = request.get_json(force=True) or {}
    message = body.get("message", "").strip()
    lang    = body.get("lang", "en")
    if not message:
        return jsonify({"error": "message is required"}), 400
    return jsonify({"success": True, "response": match_intent(message, lang), "lang": lang})

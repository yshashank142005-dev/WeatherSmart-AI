"""
main.py — WeatherSmart AI Flask application entry point.

Run with:
    python backend/main.py
    # or for development with auto-reload:
    flask --app backend.main run --debug
"""

from flask import Flask
from flask_cors import CORS

from config import DEBUG, PORT
from routes.weather         import weather_bp
from routes.predictions     import predictions_bp
from routes.recommendations import recommendations_bp
from routes.chatbot         import chatbot_bp
from ml.model               import model_manager


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register route blueprints
    app.register_blueprint(weather_bp)
    app.register_blueprint(predictions_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(chatbot_bp)

    # Health-check / root
    @app.route("/")
    def index():
        return {
            "service": "WeatherSmart AI API",
            "version": "1.0.0",
            "status":  "running",
            "endpoints": [
                "GET  /api/weather?city=<city>",
                "GET  /api/forecast?city=<city>",
                "POST /api/predict",
                "POST /api/suitability",
                "POST /api/recommend",
                "POST /api/irrigation",
                "POST /api/alert",
                "POST /api/chatbot",
            ],
        }

    return app


# Load / train the ML model once at startup
model_manager.load_or_train()

app = create_app()

if __name__ == "__main__":
    app.run(debug=DEBUG, port=PORT, host="0.0.0.0")

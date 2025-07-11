import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from transformers import pipeline
from config import Config
from collections import defaultdict
from datetime import datetime, timedelta
import hashlib

# ===== Environment Setup =====
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force CPU usage
os.environ['PYTHONWARNINGS'] = 'ignore'

# ===== App Initialization =====
app = Flask(__name__)
app.config.from_object(Config)
CORS(app,
     origins=getattr(Config, 'ALLOWED_ORIGINS', ['http://localhost:3000']),
     methods=['GET', 'POST'],
     allow_headers=['Content-Type', 'X-API-KEY'])

# ===== Security Headers =====
@app.after_request
def after_request(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# ===== Logging Configuration =====
def configure_logging():
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    file_handler = RotatingFileHandler(os.path.join(logs_dir, 'app.log'), maxBytes=1024*1024, backupCount=5)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    if not app.logger.handlers:
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)

configure_logging()

# ===== Swagger Setup =====
swaggerui_blueprint = get_swaggerui_blueprint(
    Config.SWAGGER_URL,
    Config.API_URL,
    config={'app_name': "Sentiment Analysis API"},
)
app.register_blueprint(swaggerui_blueprint, url_prefix=Config.SWAGGER_URL)

# ===== Model Loading =====
def load_model():
    try:
        model_path = os.path.join(Config.MODEL_PATH, "distilbert")
        if not os.path.exists(model_path):
            analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
            analyzer.save_pretrained(model_path)
            app.logger.info("Downloaded and saved model")
        else:
            analyzer = pipeline("sentiment-analysis", model=model_path)
            app.logger.info("Loaded model from saved directory")
        return analyzer
    except Exception as e:
        app.logger.critical(f"Model loading failed: {e}")
        return None

sentiment_analyzer = load_model()
request_counts = defaultdict(list)
prediction_cache = {}

# ===== Helper Functions =====
def validate_input(req):
    if not req.is_json:
        return {"error": "Content-Type must be application/json"}, 400
    data = req.get_json()
    if not data or not data.get('text', '').strip():
        return {"error": "Text cannot be empty"}, 400
    if len(data['text']) > 5000:
        return {"error": "Text too long (max 5000 characters)"}, 400
    return {"text": data['text'].strip()}, None

def check_rate_limit(api_key, max_requests=100, window_minutes=60):
    now = datetime.now()
    window_start = now - timedelta(minutes=window_minutes)
    request_counts[api_key] = [t for t in request_counts[api_key] if t > window_start]
    if len(request_counts[api_key]) >= max_requests:
        return False
    request
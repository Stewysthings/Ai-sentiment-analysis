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
import warnings

# ===== Environment Setup =====
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force CPU usage
os.environ['PYTHONWARNINGS'] = 'ignore'
warnings.simplefilter("ignore", FutureWarning)

# ===== App Initialization =====
app = Flask(__name__)
app.config.from_object(Config)
CORS(app,
     origins=getattr(Config, 'ALLOWED_ORIGINS', ['http://localhost:3000']),
     methods=['GET', 'POST'],
     allow_headers=['Content-Type', 'X-API-KEY'])

app.logger.info("🚀 Flask app initialized. Starting configuration...")

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
            app.logger.info("📦 Downloading sentiment model from Hugging Face...")
            analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
            analyzer.save_pretrained(model_path)
            app.logger.info("✅ Model downloaded and saved successfully")
        else:
            app.logger.info("📂 Loading sentiment model from local directory...")
            analyzer = pipeline("sentiment-analysis", model=model_path)
            app.logger.info("✅ Model loaded from saved directory")
        return analyzer
    except Exception as e:
        app.logger.critical(f"❌ Model loading failed: {e}")
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
    request_counts[api_key].append(now)
    return True

def get_cached_prediction(text):
    text_hash = hashlib.md5(text.encode()).hexdigest()
    if text_hash in prediction_cache:
        return prediction_cache[text_hash]
    result = sentiment_analyzer(text)
    prediction = {
        'sentiment': result[0]['label'].lower().replace("positive", "1").replace("negative", "0"),
        'confidence': float(result[0]['score'])
    }
    if len(prediction_cache) > 1000:
        prediction_cache.clear()
    prediction_cache[text_hash] = prediction
    return prediction

# ===== API Routes =====
@app.route('/')
def home():
    return "Sentiment Analysis API is running. Visit /docs for Swagger UI"

@app.route('/predict', methods=['POST'])
def predict():
    api_key = request.headers.get('X-API-KEY')
    if not api_key or api_key not in Config.API_KEYS:
        app.logger.warning(f"❌ Invalid API key: {api_key}")
        return jsonify({"error": "Unauthorized"}), 401
    if sentiment_analyzer is None:
        return jsonify({"error": "Model not available"}), 503

    validation_result, error = validate_input(request)
    if error:
        return jsonify(validation_result), error

    if not check_rate_limit(api_key):
        return jsonify({"error": "Rate limit exceeded"}), 429

    prediction = get_cached_prediction(validation_result['text'])

    app.logger.info(f"🧠 Prediction made for: {validation_result['text'][:50]}...")
    return jsonify({
        'sentiment': prediction['sentiment'],
        'confidence': prediction['confidence'],
        'model_version': "distilbert",
        'status': 'success'
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "OK",
        "model_loaded": sentiment_analyzer is not None,
        "version": "distilbert"
    })

@app.route('/swagger.json')
def serve_swagger():
    return send_from_directory(Config.STATIC_FOLDER, 'swagger.json')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(Config.STATIC_FOLDER, filename)

# ===== Server Startup =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.logger.info(f"📡 Launching server on port {port} via Waitress")
    try:
        from waitress import serve
        serve(app, host="0.0.0.0", port=port)
    except Exception as e:
        app.logger.error(f"⚠️ Waitress failed, falling back to Flask server: {e}")
        app.run(host="0.0.0.0", port=port)

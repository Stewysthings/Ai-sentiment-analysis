import os
import time
import hashlib
from collections import defaultdict
from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline

# Global variables
sentiment_analyzer = None  # Will be loaded on demand

app = Flask(__name__)

# Configure CORS
CORS(app, origins=['http://localhost:3000', 'http://localhost:5173'])

# Ensure Config is imported or defined
try:
    from config import Config
except ImportError:
    class Config:
        MODEL_PATH = "./models"
        API_KEYS = {"your_api_key_here"}

request_counts = defaultdict(list)
prediction_cache = {}

# ===== Helper Functions =====
def get_analyzer():
    global sentiment_analyzer
    if sentiment_analyzer is None:
        try:
            model_path = os.path.join(Config.MODEL_PATH, "distilbert")
            if not os.path.exists(model_path):
                app.logger.info("📦 Lazy-load: downloading model...")
                sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
                sentiment_analyzer.save_pretrained(model_path)
                app.logger.info("✅ Model downloaded and cached")
            else:
                app.logger.info("📂 Lazy-load: loading model from saved directory...")
                sentiment_analyzer = pipeline("sentiment-analysis", model=model_path)
                app.logger.info("✅ Model loaded from disk")
        except Exception as e:
            app.logger.critical(f"❌ Lazy model load failed: {e}")
            sentiment_analyzer = None
    return sentiment_analyzer

def validate_input(req):
    data = req.get_json(silent=True)
    if not data or 'text' not in data or not isinstance(data['text'], str) or not data['text'].strip():
        return {"error": "Invalid input. 'text' field is required."}, 400
    return {"text": data['text'].strip()}, None

def check_rate_limit(api_key, max_requests=100, window_minutes=60):
    now = time.time()
    window_start = now - window_minutes * 60
    # Remove outdated requests
    request_counts[api_key] = [t for t in request_counts[api_key] if t > window_start]
    if len(request_counts[api_key]) >= max_requests:
        return False
    request_counts[api_key].append(now)
    return True

def get_cached_prediction(text):
    analyzer = get_analyzer()
    if analyzer is None:
        return None
    text_hash = hashlib.md5(text.encode()).hexdigest()
    if text_hash in prediction_cache:
        return prediction_cache[text_hash]
    result = analyzer(text)
    prediction = {
        'sentiment': result[0]['label'].lower().replace("positive", "1").replace("negative", "0"),
        'confidence': float(result[0]['score'])
    }
    if len(prediction_cache) > 1000:
        prediction_cache.clear()
    prediction_cache[text_hash] = prediction
    return prediction

# ===== API Routes =====
@app.route('/predict', methods=['POST'])
def predict():
    api_key = request.headers.get('X-API-KEY')
    if not api_key or api_key not in set(Config.API_KEYS):
        return jsonify({"error": "Unauthorized"}), 401

    validation_result, error = validate_input(request)
    if error:
        return jsonify(validation_result), error

    if not check_rate_limit(api_key):
        return jsonify({"error": "Rate limit exceeded"}), 429

    prediction = get_cached_prediction(validation_result['text'])
    if prediction is None:
        return jsonify({"error": "Model not available"}), 503

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

@app.route('/')
def index():
    """Serve the main application page"""
    return jsonify({
        "message": "AI Sentiment Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "predict": "/predict",
            "health": "/health",
            "docs": "/docs"
        }
    })

if __name__ == '__main__':
    # Initialize configuration
    config = Config()
    
    # Validate configuration in development
    if not config.IS_PRODUCTION:
        try:
            config.validate_config()
        except ValueError as e:
            app.logger.warning(f"Configuration validation failed: {e}")
    
    # Set Flask configuration
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=config.PORT,
        debug=not config.IS_PRODUCTION
    )

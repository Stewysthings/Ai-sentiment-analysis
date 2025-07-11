import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
import os
from transformers import pipeline  # type: ignore

# Add pip install transformers to requirements.txt or run:
# pip install transformers
from config import Config
from flask_cors import CORS  # type: ignore
# pip install flask-cors

try:
    from waitress import serve  # type: ignore
except ImportError:
    pass

app = Flask(__name__)
app.config.from_object(Config)
# Replace the simple CORS(app) with more specific configuration
CORS(app, 
     origins=Config.ALLOWED_ORIGINS if hasattr(Config, 'ALLOWED_ORIGINS') else ['http://localhost:3000'],
     methods=['GET', 'POST'],
     allow_headers=['Content-Type', 'X-API-KEY'])

# Add security headers
@app.after_request
def after_request(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# ===== Logging Configuration =====
def configure_logging():
    """Sets up logging with both file and console output"""
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'app.log'),
        maxBytes=1024*1024,
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    if not app.logger.handlers:
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)

configure_logging()

# ===== Swagger UI Setup =====
swaggerui_blueprint = get_swaggerui_blueprint(
    Config.SWAGGER_URL,
    Config.API_URL,
    config={'app_name': "Sentiment Analysis API"},
)
app.register_blueprint(swaggerui_blueprint, url_prefix=Config.SWAGGER_URL)

# ===== Model Loading =====
def load_model():
    """Load sentiment analysis model with proper error handling"""
    try:
        model_path = os.path.join(Config.MODEL_PATH, "distilbert")
        if not os.path.exists(model_path):
            sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
            sentiment_analyzer.save_pretrained(model_path)
            app.logger.info("Pre-trained transformer model downloaded and saved successfully")
        else:
            sentiment_analyzer = pipeline("sentiment-analysis", model=model_path)
            app.logger.info("Transformer model loaded from saved directory")
        return sentiment_analyzer
    except Exception as e:
        app.logger.critical(f"Model loading failed: {e}")
        return None

sentiment_analyzer = load_model()

# ===== API Endpoints =====
@app.route('/')
def home():
    """Main endpoint that shows API status"""
    return "Sentiment Analysis API is running. Visit /docs for Swagger UI"

@app.route('/predict', methods=['POST'])
def predict():
    """Endpoint for sentiment analysis predictions"""
    import hashlib
    
    api_key = request.headers.get('X-API-KEY')
    if not api_key or api_key not in Config.API_KEYS:
        app.logger.warning(f"Unauthorized access attempt with key: {api_key}")
        return jsonify({"error": "Invalid API key"}), 401

    try:
        # Enhanced input validation
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400
            
        text = data.get('text', '').strip()
        if not text:
            return jsonify({"error": "Text cannot be empty"}), 400
            
        # Add text length validation
        if len(text) > 5000:  # Reasonable limit
            return jsonify({"error": "Text too long (max 5000 characters)"}), 400

        # Check if model is available
        if sentiment_analyzer is None:
            return jsonify({"error": "Model not available"}), 503

        text_hash = hashlib.md5(text.encode()).hexdigest()
        result = sentiment_analyzer(text)
        prediction = result[0]['label'].lower().replace("positive", "1").replace("negative", "0")
        confidence = float(result[0]['score'])

        app.logger.info(f"Successful prediction for text: {text[:50]}...")

        return jsonify({
            'sentiment': prediction,
            'confidence': confidence,
            'model_version': "distilbert",
            'status': 'success'
        })
    except Exception as e:
        app.logger.error(f"Prediction error: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Prediction failed',
            'message': str(e),
            'status': 'error'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        "status": "OK",
        "model_loaded": True,
        "version": "distilbert"
    }), 200

@app.route('/swagger.json')
def serve_swagger():
    """Serves the Swagger/OpenAPI specification"""
    return send_from_directory(Config.STATIC_FOLDER, 'swagger.json')



@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serves static files from the configured static folder"""
    return send_from_directory(Config.STATIC_FOLDER, filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
﻿import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
import joblib
import sklearn
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# ===== Logging Configuration =====
def configure_logging():
    """Sets up logging with both file and console output"""
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # File handler (rotating logs)
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'app.log'),
        maxBytes=1024*1024,  # 1MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Apply handlers
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)

configure_logging()

# ===== Swagger UI Setup =====
swaggerui_blueprint = get_swaggerui_blueprint(
    Config.SWAGGER_URL,
    Config.API_URL,
    config={
        'app_name': "Sentiment Analysis API",
        'validatorUrl': None
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=Config.SWAGGER_URL)

# ===== Model Loading =====
try:
    model = joblib.load(Config.MODEL_PATH)
    vectorizer = joblib.load(Config.VECTORIZER_PATH)
    app.logger.info(f"Models loaded successfully (scikit-learn v{sklearn.__version__})")
except Exception as e:
    app.logger.critical(f"Model loading failed: {e}")
    raise

# ===== API Endpoints =====
@app.route('/')
def home():
    """Main endpoint that shows API status"""
    return "Sentiment Analysis API is running. Visit /docs for Swagger UI"

@app.route('/predict', methods=['POST'])
def predict():
    """Endpoint for sentiment analysis predictions"""
    # Authentication
    api_key = request.headers.get('X-API-KEY')
    if not api_key or api_key not in Config.API_KEYS:
        app.logger.warning(f"Unauthorized access attempt with key: {api_key}")
        return jsonify({"error": "Invalid API key"}), 401
    
    # Prediction logic
    try:
        text = request.json.get('text', '').strip()
        if not text:
            return jsonify({"error": "Text cannot be empty"}), 400
            
        features = vectorizer.transform([text])
        prediction = model.predict(features)[0]
        confidence = float(model.predict_proba(features).max())
        
        app.logger.info(f"Successful prediction for text: {text[:50]}...")
        
        return jsonify({
            'sentiment': str(prediction),
            'confidence': confidence,
            'model_version': f"scikit-learn={sklearn.__version__}",
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
        "version": f"scikit-learn={sklearn.__version__}"
    }), 200

@app.route('/swagger.json')
def serve_swagger():
    """Serves the Swagger/OpenAPI specification"""
    return send_from_directory(Config.STATIC_FOLDER, 'swagger.json')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)
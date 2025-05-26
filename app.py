from flask import Flask, request, jsonify, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
import joblib
import sklearn
import os

# Initialize Flask app
app = Flask(__name__)

# ===== Configuration =====
MODEL_PATH = r"C:\Users\cella\Ai-sentiment-analysis\models\model.pkl"
VECTORIZER_PATH = r"C:\Users\cella\Ai-sentiment-analysis\models\vectorizer.pkl"
API_KEYS = {"your-secret-key-123"}  # Change this in production!
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

# ===== Swagger UI Setup =====
SWAGGER_URL = '/docs'
API_URL = '/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Sentiment Analysis API",
        'validatorUrl': None
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# ===== API Documentation =====
@app.route('/swagger.json')
def swagger():
    return jsonify({
        "openapi": "3.0.0",
        "info": {
            "title": "Sentiment Analysis API",
            "version": "1.0",
            "description": "Predicts text sentiment using ML model"
        },
        "servers": [{"url": "http://localhost:5000", "description": "Local development"}],
        "paths": {
            "/": {
                "get": {
                    "summary": "API status",
                    "responses": {"200": {"description": "API is running"}}
                }
            },
            "/predict": {
                "post": {
                    "summary": "Analyze text sentiment",
                    "security": [{"APIKey": []}],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "text": {"type": "string"}
                                    },
                                    "example": {"text": "This product is amazing!"}
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Successful prediction",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "sentiment": {"type": "string"},
                                            "model_version": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "APIKey": {
                    "type": "apiKey",
                    "name": "X-API-KEY",
                    "in": "header"
                }
            }
        },
        "security": [{"APIKey": []}]
    })

# ===== Model Loading =====
try:
    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    print(f"✅ Models loaded successfully (scikit-learn v{sklearn.__version__})")
except Exception as e:
    print(f"❌ Model loading failed: {e}")
    raise

# ===== API Endpoints =====
@app.route('/')
def home():
    return "Sentiment Analysis API is running. Visit /docs for Swagger UI"

@app.route('/predict', methods=['POST'])
def predict():
    # Authentication
    if request.headers.get('X-API-KEY') not in API_KEYS:
        return jsonify({"error": "Invalid API key"}), 401
    
    # Prediction logic
    try:
        text = request.json['text']
        features = vectorizer.transform([text])
        prediction = model.predict(features)[0]
        return jsonify({
            'sentiment': str(prediction),
            'model_version': f"scikit-learn={sklearn.__version__}",
            'status': 'success'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 400

# ===== Main Execution =====
if __name__ == '__main__':
    # Create static directory if needed
    if not os.path.exists(STATIC_DIR):
        os.makedirs(STATIC_DIR)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
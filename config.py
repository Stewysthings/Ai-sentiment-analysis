import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Config:
    """Centralized configuration for the Flask application"""
    
    # ===== Required Core Configurations =====
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())
    
    # ===== Model and File Paths =====
    MODEL_PATH = os.getenv('MODEL_PATH', 'static_models')
    STATIC_FOLDER = os.getenv('STATIC_FOLDER', 'static')
    
    # ===== API Security =====
    API_KEYS = [
        key.strip() 
        for key in os.getenv('API_KEYS', 'default_key').split(',')
        if key.strip()
    ]
    
    # ===== Swagger UI Configuration =====
    SWAGGER_URL = '/docs'  # Endpoint for Swagger UI
    API_URL = '/swagger.json'  # Your OpenAPI spec file
    
    # ===== CORS Settings =====
    ALLOWED_ORIGINS = [
        origin.strip()
        for origin in os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
        if origin.strip()
    ]
    
    # ===== Performance Optimizations =====
    MODEL_CACHE_DIR = os.path.join(MODEL_PATH, 'cache')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB upload limit
    
    # ===== Render-Specific Defaults =====
    @property
    def PORT(self):
        return int(os.getenv('PORT', 10000))
    
    @property
    def IS_PRODUCTION(self):
        return os.getenv('FLASK_ENV', 'development').lower() == 'production'
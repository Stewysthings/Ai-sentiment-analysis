import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Config:
    """Centralized configuration for the Flask application"""
    
    # ===== Required Core Configurations =====
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        import warnings
        warnings.warn("SECRET_KEY not set! Using random key - sessions will not persist across restarts")
        SECRET_KEY = os.urandom(24).hex()
    
    # ===== Model and File Paths =====
    MODEL_PATH = os.getenv('MODEL_PATH', 'static_models')
    STATIC_FOLDER = os.getenv('STATIC_FOLDER', 'static')
    
    # ===== API Security =====
    API_KEYS = [
        key.strip() 
        for key in os.getenv('API_KEYS', 'default_key').split(',')
        if key.strip()
    ]  # List of valid API keys for authentication (comma-separated in env)
    
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
    DEFAULT_PORT = 10000
    DEFAULT_MAX_UPLOAD_SIZE_MB = 16
    MAX_CONTENT_LENGTH = DEFAULT_MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    # ===== Render-Specific Defaults =====
    def __init__(self):
        self._port = None
        self._is_production = None

    @property
    def PORT(self):
        if self._port is None:
            self._port = int(os.getenv('PORT', 10000))
        return self._port
    
    @property
    def IS_PRODUCTION(self):
        return os.getenv('FLASK_ENV', 'development').lower() == 'production'

    def validate_config(self):
        """Validate all configuration values are properly set"""
        errors = []
        
        if 'default_key' in self.API_KEYS:
            errors.append("API_KEYS contains default value - update for production")
        
        if not os.path.exists(self.MODEL_PATH):
            errors.append(f"MODEL_PATH directory does not exist: {self.MODEL_PATH}")
        
        if errors:
            raise ValueError("Configuration errors: " + "; ".join(errors))
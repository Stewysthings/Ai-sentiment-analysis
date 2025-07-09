import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Config:
    # Required configuration with validation
    MODEL_PATH = Path(os.getenv('MODEL_PATH', 'models'))  # Default to 'models' directory
    VECTORIZER_PATH = Path(os.getenv('VECTORIZER_PATH'))  # Still required for backward compatibility
    SECRET_KEY = os.getenv('SECRET_KEY')

    # API Keys (with empty set fallback)
    API_KEYS = set(os.getenv('API_KEYS', '').split(',')) if os.getenv('API_KEYS') else set()

    # Optional configurations with defaults
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    SWAGGER_URL = '/docs'         # URL to access Swagger UI
    API_URL = '/swagger.json'     # URL to the swagger spec served by Flask
    STATIC_FOLDER = 'static'      # folder where swagger.json lives

    @classmethod
    def validate(cls):
        """Validate required configurations"""
        required = {
            'MODEL_PATH': cls.MODEL_PATH,
            'VECTORIZER_PATH': cls.VECTORIZER_PATH,
            'SECRET_KEY': cls.SECRET_KEY
        }

        for name, value in required.items():
            if not value:
                raise ValueError(f"Missing required config: {name}")

        # Check if MODEL_PATH is a directory and create if it doesn't exist
        if not cls.MODEL_PATH.is_dir():
            try:
                cls.MODEL_PATH.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {cls.MODEL_PATH}")
            except Exception as e:
                raise FileNotFoundError(f"Cannot create directory {cls.MODEL_PATH}: {e}")

        # Optional: Remove VECTORIZER_PATH validation if no longer needed
        # if not cls.VECTORIZER_PATH.exists():
        #     raise FileNotFoundError(f"Vectorizer file not found at {cls.VECTORIZER_PATH}")

        if not cls.API_KEYS:
            print("Warning: No API keys configured - authentication disabled")

# Validate configuration on import
Config.validate()
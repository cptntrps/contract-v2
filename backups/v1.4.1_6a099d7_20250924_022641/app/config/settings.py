"""
Configuration management for Contract Analyzer

Handles environment variables with sensible defaults and environment-specific configurations.
"""

import os
from pathlib import Path
from typing import Type, Union
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class BaseConfig:
    """Base configuration class with common settings"""
    
    # === APPLICATION METADATA ===
    APP_NAME = "Contract Analyzer"
    APP_VERSION = "1.2.0"
    
    # === FLASK CONFIGURATION ===
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', '5000'))
    
    # === DIRECTORY PATHS ===
    BASE_DIR = Path(__file__).parent.parent.parent  # Project root
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'data/uploads')
    TEMPLATES_FOLDER = os.getenv('TEMPLATES_FOLDER', 'data/templates')
    REPORTS_FOLDER = os.getenv('REPORTS_FOLDER', 'data/reports')
    STATIC_FOLDER = os.getenv('STATIC_FOLDER', 'static')
    TEMPLATE_FOLDER = os.getenv('TEMPLATE_FOLDER', 'templates')
    PROMPTS_FOLDER = os.getenv('PROMPTS_FOLDER', 'data/prompts')
    
    # === FILE UPLOAD LIMITS ===
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '16777216'))  # 16MB
    ALLOWED_EXTENSIONS = os.getenv('ALLOWED_EXTENSIONS', 'docx').split(',')
    MAX_FILENAME_LENGTH = int(os.getenv('MAX_FILENAME_LENGTH', '255'))
    
    # === LLM PROVIDER CONFIGURATION ===
    LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')
    
    # === OPENAI CONFIGURATION ===
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')
    OPENAI_TIMEOUT = int(os.getenv('OPENAI_TIMEOUT', '30'))
    OPENAI_MAX_RETRIES = int(os.getenv('OPENAI_MAX_RETRIES', '3'))
    OPENAI_RETRY_DELAY = int(os.getenv('OPENAI_RETRY_DELAY', '2'))
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    
    # === LLM PARAMETERS ===
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.1'))
    LLM_TOP_P = float(os.getenv('LLM_TOP_P', '0.9'))
    LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', '512'))
    
    # === PERFORMANCE OPTIMIZATIONS ===
    LLM_BATCH_SIZE = int(os.getenv('LLM_BATCH_SIZE', '15'))
    LLM_USE_FAST_MODEL = os.getenv('LLM_USE_FAST_MODEL', 'true').lower() == 'true'
    LLM_FAST_MODEL = os.getenv('LLM_FAST_MODEL', 'gpt-4o-mini')
    LLM_TIMEOUT_OPTIMIZED = int(os.getenv('LLM_TIMEOUT_OPTIMIZED', '15'))
    LLM_MAX_WORKERS = int(os.getenv('LLM_MAX_WORKERS', '5'))
    
    # === SECURITY SETTINGS ===
    SECURE_FILENAME_ENABLED = os.getenv('SECURE_FILENAME_ENABLED', 'true').lower() == 'true'
    PATH_TRAVERSAL_PROTECTION = os.getenv('PATH_TRAVERSAL_PROTECTION', 'true').lower() == 'true'
    FILE_VALIDATION_ENABLED = os.getenv('FILE_VALIDATION_ENABLED', 'true').lower() == 'true'
    CONTENT_TYPE_VALIDATION = os.getenv('CONTENT_TYPE_VALIDATION', 'true').lower() == 'true'
    
    # === LOGGING CONFIGURATION ===
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'output/logs/dashboard.log')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # === ANALYSIS SETTINGS ===
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.5'))
    SIGNIFICANT_CHANGES_THRESHOLD = int(os.getenv('SIGNIFICANT_CHANGES_THRESHOLD', '10'))
    ANALYSIS_TIMEOUT = int(os.getenv('ANALYSIS_TIMEOUT', '300'))
    
    # === PERFORMANCE SETTINGS ===
    CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', '3600'))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
    CONNECTION_POOL_SIZE = int(os.getenv('CONNECTION_POOL_SIZE', '10'))
    
    # === MONITORING ===
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '30'))
    METRICS_ENABLED = os.getenv('METRICS_ENABLED', 'true').lower() == 'true'
    
    # === DASHBOARD SETTINGS ===
    DASHBOARD_TITLE = os.getenv('DASHBOARD_TITLE', 'Contract Analyzer Dashboard')
    AUTO_REFRESH_INTERVAL = int(os.getenv('AUTO_REFRESH_INTERVAL', '30000'))
    PAGINATION_SIZE = int(os.getenv('PAGINATION_SIZE', '20'))

    @classmethod
    def validate_config(cls) -> list:
        """Validate configuration settings and return list of errors."""
        errors = []
        
        # Validate required settings
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
        
        if not cls.SECRET_KEY:
            errors.append("FLASK_SECRET_KEY is required and must be set in environment")
        elif cls.SECRET_KEY == 'dev-key-change-in-production':
            errors.append("FLASK_SECRET_KEY cannot use default development key in production")
        elif len(cls.SECRET_KEY) < 32:
            errors.append("FLASK_SECRET_KEY must be at least 32 characters long")
        
        if cls.LLM_BATCH_SIZE < 1:
            errors.append("LLM_BATCH_SIZE must be at least 1")
            
        if cls.MAX_CONTENT_LENGTH < 1:
            errors.append("MAX_CONTENT_LENGTH must be positive")
            
        return errors

    @classmethod
    def get_summary(cls) -> dict:
        """Get configuration summary for logging."""
        return {
            'flask_host': cls.HOST,
            'flask_port': cls.PORT,
            'debug': cls.DEBUG,
            'llm_provider': cls.LLM_PROVIDER,
            'upload_folder': cls.UPLOAD_FOLDER,
            'max_file_size': f"{cls.MAX_CONTENT_LENGTH // (1024*1024)}MB",
            'allowed_extensions': cls.ALLOWED_EXTENSIONS,
            'log_level': cls.LOG_LEVEL,
            'openai_model': cls.OPENAI_MODEL,
            'openai_api_key': 'configured' if cls.OPENAI_API_KEY else 'missing'
        }


def get_config(config_name: str = None) -> Type[BaseConfig]:
    """
    Get configuration class based on environment name.
    
    Args:
        config_name: Environment name (development, production, testing)
        
    Returns:
        Configuration class
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    config_mapping = {
        'development': 'app.config.environments.development.DevelopmentConfig',
        'production': 'app.config.environments.production.ProductionConfig', 
        'testing': 'app.config.environments.testing.TestingConfig'
    }
    
    config_path = config_mapping.get(config_name.lower())
    if not config_path:
        # Fallback to base config
        return BaseConfig
    
    try:
        module_path, class_name = config_path.rsplit('.', 1)
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    except (ImportError, AttributeError):
        # Fallback to base config
        return BaseConfig


# Export the main configuration getter
__all__ = ['BaseConfig', 'get_config']
"""
Testing environment configuration
"""

from ..settings import BaseConfig


class TestingConfig(BaseConfig):
    """Testing-specific configuration"""
    
    ENV = 'testing'
    DEBUG = True
    TESTING = True
    
    # Testing directories
    UPLOAD_FOLDER = 'tests/data/uploads'
    TEMPLATES_FOLDER = 'tests/data/templates' 
    REPORTS_FOLDER = 'tests/data/reports'
    PROMPTS_FOLDER = 'tests/data/prompts'
    
    # Testing settings
    LOG_LEVEL = 'DEBUG'
    METRICS_ENABLED = False
    CACHE_TIMEOUT = 0  # No caching in tests
    
    # Fast testing
    LLM_BATCH_SIZE = 5
    LLM_TIMEOUT_OPTIMIZED = 10
    LLM_MAX_WORKERS = 2
    
    # Testing security (relaxed)
    FILE_VALIDATION_ENABLED = True
    SECURE_FILENAME_ENABLED = True
    
    # Use mock providers in testing
    LLM_PROVIDER = 'mock'
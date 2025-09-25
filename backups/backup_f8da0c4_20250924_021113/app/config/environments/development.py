"""
Development environment configuration
"""

from ..settings import BaseConfig


class DevelopmentConfig(BaseConfig):
    """Development-specific configuration"""
    
    ENV = 'development'
    DEBUG = True
    
    # Development-friendly settings
    LOG_LEVEL = 'DEBUG'
    HOT_RELOAD = True
    PROFILING_ENABLED = False
    
    # Relaxed security for development
    SECURE_FILENAME_ENABLED = True
    FILE_VALIDATION_ENABLED = True
    
    # Development optimizations
    LLM_TIMEOUT_OPTIMIZED = 20  # Longer timeout for debugging
    CACHE_TIMEOUT = 300  # Shorter cache for development
    
    # Development monitoring
    METRICS_ENABLED = True
    HEALTH_CHECK_INTERVAL = 60
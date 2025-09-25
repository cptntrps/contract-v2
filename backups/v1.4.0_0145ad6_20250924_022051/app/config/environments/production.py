"""
Production environment configuration
"""

from ..settings import BaseConfig


class ProductionConfig(BaseConfig):
    """Production-specific configuration"""
    
    ENV = 'production'
    DEBUG = False
    
    # Production security
    SECURE_FILENAME_ENABLED = True
    PATH_TRAVERSAL_PROTECTION = True
    FILE_VALIDATION_ENABLED = True
    CONTENT_TYPE_VALIDATION = True
    
    # Production logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = '/var/log/contract-analyzer/app.log'
    
    # Production performance
    LLM_TIMEOUT_OPTIMIZED = 15
    CACHE_TIMEOUT = 3600
    CONNECTION_POOL_SIZE = 20
    
    # Production monitoring
    METRICS_ENABLED = True
    HEALTH_CHECK_INTERVAL = 30
    
    # Production optimizations
    LLM_BATCH_SIZE = 20  # Larger batches in production
    LLM_MAX_WORKERS = 10  # More workers in production
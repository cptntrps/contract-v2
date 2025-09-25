"""
Logging configuration for Contract Analyzer

Provides centralized logging setup with environment-specific configurations.
"""

import logging
import logging.config
import os
from pathlib import Path
from typing import Dict, Any


def setup_logging(config) -> None:
    """
    Setup application logging configuration
    
    Args:
        config: Application configuration object
    """
    log_level = getattr(config, 'LOG_LEVEL', 'INFO')
    log_file = getattr(config, 'LOG_FILE', 'output/logs/dashboard.log')
    log_format = getattr(config, 'LOG_FORMAT', 
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Logging configuration
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': log_format
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
            },
            'json': {
                'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
                'class': 'pythonjsonlogger.jsonlogger.JsonFormatter'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'standard',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': log_level,
                'formatter': 'detailed',
                'filename': log_file,
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf8'
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'detailed',
                'filename': log_file.replace('.log', '_errors.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 3,
                'encoding': 'utf8'
            }
        },
        'loggers': {
            '': {  # Root logger
                'level': log_level,
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'app': {
                'level': log_level,
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'app.services.llm': {
                'level': log_level,
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'app.core': {
                'level': log_level,
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'app.api': {
                'level': log_level,
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'security_audit': {
                'level': 'INFO',
                'handlers': ['file'],
                'propagate': False
            },
            'werkzeug': {
                'level': 'WARNING' if config.ENV == 'production' else 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'urllib3': {
                'level': 'WARNING',
                'handlers': ['console'],
                'propagate': False
            },
            'requests': {
                'level': 'WARNING',
                'handlers': ['console'],
                'propagate': False
            }
        }
    }
    
    # Apply environment-specific modifications
    if config.ENV == 'production':
        # Production: Only file logging, higher thresholds
        logging_config['handlers']['console']['level'] = 'WARNING'
        logging_config['loggers']['']['handlers'] = ['file', 'error_file']
        
    elif config.ENV == 'testing':
        # Testing: Console only, suppress most output
        logging_config['handlers']['console']['level'] = 'ERROR'
        logging_config['loggers']['']['handlers'] = ['console']
        
        # Suppress third-party logging in tests
        logging_config['loggers']['werkzeug']['level'] = 'ERROR'
        logging_config['loggers']['urllib3']['level'] = 'ERROR'
        logging_config['loggers']['requests']['level'] = 'ERROR'
    
    # Apply configuration
    logging.config.dictConfig(logging_config)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Environment: {config.ENV}, Level: {log_level}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_performance(func):
    """
    Decorator to log function performance
    
    Usage:
        @log_performance
        def my_function():
            pass
    """
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    
    return wrapper


def log_exception(func):
    """
    Decorator to log exceptions with context
    
    Usage:
        @log_exception
        def my_function():
            pass
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Exception in {func.__name__}: {e}")
            raise
    
    return wrapper


__all__ = [
    'setup_logging',
    'get_logger', 
    'log_performance',
    'log_exception'
]
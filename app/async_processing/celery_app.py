"""
Celery application configuration for async contract analysis processing
"""
import os
from celery import Celery
from kombu import Queue

# Create Celery instance
celery_app = Celery('contract_analyzer')

def configure_celery(app=None):
    """Configure Celery with Flask app context"""
    
    # Broker configuration
    broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    celery_app.conf.update(
        broker_url=broker_url,
        result_backend=result_backend,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        
        # Task routing
        task_routes={
            'app.async_processing.tasks.analyze_contract': {'queue': 'analysis'},
            'app.async_processing.tasks.generate_report': {'queue': 'reports'},
            'app.async_processing.tasks.batch_analysis': {'queue': 'batch'},
        },
        
        # Queue definitions
        task_create_missing_queues=True,
        task_default_queue='default',
        task_queues=(
            Queue('default'),
            Queue('analysis', routing_key='analysis'),
            Queue('reports', routing_key='reports'),
            Queue('batch', routing_key='batch'),
        ),
        
        # Task execution settings
        task_time_limit=1800,  # 30 minutes
        task_soft_time_limit=1500,  # 25 minutes
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        worker_max_tasks_per_child=100,
        
        # Results settings
        result_expires=3600,  # 1 hour
        task_ignore_result=False,
        task_store_eager_result=True,
    )
    
    if app:
        # Flask integration
        class ContextTask(celery_app.Task):
            """Make celery tasks work with Flask app context."""
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        
        celery_app.Task = ContextTask
    
    return celery_app

# Configure with default settings
configure_celery()
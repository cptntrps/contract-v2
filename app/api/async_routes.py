"""
API routes for async processing operations
"""
import logging
from typing import Dict, Any, List

from flask import Blueprint, request, jsonify, current_app
from marshmallow import Schema, fields, ValidationError

from ..async_processing.task_manager import TaskManager
from ..utils.errors.exceptions import TaskError, ValidationError as CustomValidationError
from ..utils.errors.responses import create_error_response

logger = logging.getLogger(__name__)

# Create blueprint
async_bp = Blueprint('async', __name__, url_prefix='/api/async')

# Validation schemas
class AnalysisTaskSchema(Schema):
    """Schema for analysis task submission"""
    contract_id = fields.Str(required=True)
    template_id = fields.Str(required=True)
    analysis_options = fields.Dict(missing=dict)

class ReportTaskSchema(Schema):
    """Schema for report generation task submission"""
    analysis_id = fields.Str(required=True)
    output_formats = fields.List(fields.Str(), required=True)
    output_options = fields.Dict(missing=dict)

class BatchAnalysisTaskSchema(Schema):
    """Schema for batch analysis task submission"""
    contract_ids = fields.List(fields.Str(), required=True, validate=lambda x: len(x) > 0)
    template_id = fields.Str(required=True)
    batch_options = fields.Dict(missing=dict)

# Initialize schemas
analysis_task_schema = AnalysisTaskSchema()
report_task_schema = ReportTaskSchema()
batch_analysis_task_schema = BatchAnalysisTaskSchema()

# Routes
@async_bp.route('/analysis', methods=['POST'])
def submit_analysis_task():
    """
    Submit contract analysis task for async processing
    
    Request body:
    {
        "contract_id": "contract_123",
        "template_id": "template_456",
        "analysis_options": {
            "include_semantic_analysis": true,
            "detail_level": "high"
        }
    }
    
    Returns:
    {
        "task_id": "celery_task_id",
        "status": "PENDING",
        "message": "Analysis task submitted successfully"
    }
    """
    try:
        # Validate request data
        data = analysis_task_schema.load(request.json or {})
        
        logger.info(f"Submitting analysis task for contract {data['contract_id']}")
        
        # Submit task
        task_manager = TaskManager()
        task_id = task_manager.submit_analysis(
            contract_id=data['contract_id'],
            template_id=data['template_id'],
            analysis_options=data['analysis_options']
        )
        
        return jsonify({
            'task_id': task_id,
            'status': 'PENDING',
            'message': 'Analysis task submitted successfully',
            'estimated_duration': '5-10 minutes'
        }), 202
        
    except ValidationError as e:
        return create_error_response(CustomValidationError("Invalid request data", details=e.messages), 400)
    except TaskError as e:
        return create_error_response(e, 500)
    except Exception as e:
        logger.error(f"Unexpected error in submit_analysis_task: {str(e)}")
        return create_error_response(TaskError("submit_analysis", f"Failed to submit analysis task: {str(e)}"), 500)


@async_bp.route('/reports', methods=['POST'])
def submit_report_task():
    """
    Submit report generation task for async processing
    
    Request body:
    {
        "analysis_id": "analysis_123",
        "output_formats": ["excel", "pdf", "docx"],
        "output_options": {
            "include_track_changes": true,
            "template_style": "professional"
        }
    }
    
    Returns:
    {
        "task_id": "celery_task_id",
        "status": "PENDING",
        "message": "Report generation task submitted successfully"
    }
    """
    try:
        # Validate request data
        data = report_task_schema.load(request.json or {})
        
        logger.info(f"Submitting report task for analysis {data['analysis_id']}")
        
        # Submit task
        task_manager = TaskManager()
        task_id = task_manager.submit_report_generation(
            analysis_id=data['analysis_id'],
            output_formats=data['output_formats'],
            output_options=data['output_options']
        )
        
        return jsonify({
            'task_id': task_id,
            'status': 'PENDING',
            'message': 'Report generation task submitted successfully',
            'estimated_duration': '2-5 minutes'
        }), 202
        
    except ValidationError as e:
        return create_error_response(CustomValidationError("Invalid request data", details=e.messages), 400)
    except TaskError as e:
        return create_error_response(e, 500)
    except Exception as e:
        logger.error(f"Unexpected error in submit_report_task: {str(e)}")
        return create_error_response(TaskError("submit_report", f"Failed to submit report task: {str(e)}"), 500)


@async_bp.route('/batch-analysis', methods=['POST'])
def submit_batch_analysis_task():
    """
    Submit batch analysis task for async processing
    
    Request body:
    {
        "contract_ids": ["contract_1", "contract_2", "contract_3"],
        "template_id": "template_456",
        "batch_options": {
            "parallel_processing": true,
            "failure_tolerance": 0.1
        }
    }
    
    Returns:
    {
        "task_id": "celery_task_id",
        "status": "PENDING",
        "message": "Batch analysis task submitted successfully"
    }
    """
    try:
        # Validate request data
        data = batch_analysis_task_schema.load(request.json or {})
        
        contract_count = len(data['contract_ids'])
        logger.info(f"Submitting batch analysis task for {contract_count} contracts")
        
        # Submit task
        task_manager = TaskManager()
        task_id = task_manager.submit_batch_analysis(
            contract_ids=data['contract_ids'],
            template_id=data['template_id'],
            batch_options=data['batch_options']
        )
        
        estimated_time = f"{contract_count * 5}-{contract_count * 10} minutes"
        
        return jsonify({
            'task_id': task_id,
            'status': 'PENDING',
            'message': f'Batch analysis task submitted successfully for {contract_count} contracts',
            'contract_count': contract_count,
            'estimated_duration': estimated_time
        }), 202
        
    except ValidationError as e:
        return create_error_response(CustomValidationError("Invalid request data", details=e.messages), 400)
    except TaskError as e:
        return create_error_response(e, 500)
    except Exception as e:
        logger.error(f"Unexpected error in submit_batch_analysis_task: {str(e)}")
        return create_error_response(TaskError("submit_batch_analysis", f"Failed to submit batch analysis task: {str(e)}"), 500)


@async_bp.route('/tasks/<task_id>/status', methods=['GET'])
def get_task_status(task_id: str):
    """
    Get status of an async task
    
    Returns:
    {
        "task_id": "celery_task_id",
        "state": "PROGRESS",
        "ready": false,
        "info": {
            "current": 50,
            "total": 100,
            "status": "Processing document comparison..."
        }
    }
    """
    try:
        logger.debug(f"Getting status for task {task_id}")
        
        task_manager = TaskManager()
        status = task_manager.get_task_status(task_id)
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in get_task_status: {str(e)}")
        return create_error_response(TaskError("get_task_status", f"Failed to get task status: {str(e)}"), 500)


@async_bp.route('/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id: str):
    """
    Cancel a running async task
    
    Returns:
    {
        "task_id": "celery_task_id",
        "cancelled": true,
        "message": "Task cancelled successfully"
    }
    """
    try:
        logger.info(f"Cancelling task {task_id}")
        
        task_manager = TaskManager()
        cancelled = task_manager.cancel_task(task_id)
        
        if cancelled:
            return jsonify({
                'task_id': task_id,
                'cancelled': True,
                'message': 'Task cancelled successfully'
            }), 200
        else:
            return jsonify({
                'task_id': task_id,
                'cancelled': False,
                'message': 'Task could not be cancelled (may already be completed)'
            }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error in cancel_task: {str(e)}")
        return create_error_response(TaskError("cancel_task", f"Failed to cancel task: {str(e)}"), 500)


@async_bp.route('/tasks/active', methods=['GET'])
def get_active_tasks():
    """
    Get list of currently active tasks
    
    Returns:
    {
        "active_tasks": [
            {
                "task_id": "task_123",
                "name": "analyze_contract_async",
                "worker": "worker1@hostname",
                "time_start": 1234567890
            }
        ],
        "count": 1
    }
    """
    try:
        logger.debug("Getting active tasks")
        
        task_manager = TaskManager()
        active_tasks = task_manager.get_active_tasks()
        
        return jsonify({
            'active_tasks': active_tasks,
            'count': len(active_tasks)
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in get_active_tasks: {str(e)}")
        return create_error_response(TaskError("get_active_tasks", f"Failed to get active tasks: {str(e)}"), 500)


@async_bp.route('/tasks/history', methods=['GET'])
def get_task_history():
    """
    Get task execution history
    
    Query parameters:
    - limit: Maximum number of tasks (default 50)
    - task_type: Filter by task type (optional)
    
    Returns:
    {
        "task_history": [],
        "count": 0,
        "limit": 50
    }
    """
    try:
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100
        task_type = request.args.get('task_type')
        
        logger.debug(f"Getting task history (limit: {limit}, type: {task_type})")
        
        task_manager = TaskManager()
        history = task_manager.get_task_history(limit=limit, task_type=task_type)
        
        return jsonify({
            'task_history': history,
            'count': len(history),
            'limit': limit
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in get_task_history: {str(e)}")
        return create_error_response(TaskError("get_task_history", f"Failed to get task history: {str(e)}"), 500)


@async_bp.route('/queues/status', methods=['GET'])
def get_queue_status():
    """
    Get status of task queues
    
    Returns:
    {
        "queues": {...},
        "workers": {...},
        "stats": {...}
    }
    """
    try:
        logger.debug("Getting queue status")
        
        task_manager = TaskManager()
        status = task_manager.get_queue_status()
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in get_queue_status: {str(e)}")
        return create_error_response(TaskError("get_queue_status", f"Failed to get queue status: {str(e)}"), 500)


@async_bp.route('/health', methods=['GET'])
def async_health_check():
    """
    Perform health check on async processing system
    
    Returns:
    {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00",
        "workers": 2,
        "queues": ["default", "analysis", "reports", "batch"]
    }
    """
    try:
        logger.debug("Performing async system health check")
        
        task_manager = TaskManager()
        health = task_manager.health_check()
        
        status_code = 200 if health['status'] == 'healthy' else 503
        return jsonify(health), status_code
        
    except Exception as e:
        logger.error(f"Unexpected error in async_health_check: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503


@async_bp.route('/cleanup', methods=['POST'])
def schedule_cleanup():
    """
    Schedule cleanup of old results
    
    Returns:
    {
        "task_id": "cleanup_task_id",
        "message": "Cleanup task scheduled successfully"
    }
    """
    try:
        logger.info("Scheduling cleanup task")
        
        task_manager = TaskManager()
        task_id = task_manager.schedule_cleanup()
        
        return jsonify({
            'task_id': task_id,
            'message': 'Cleanup task scheduled successfully'
        }), 202
        
    except Exception as e:
        logger.error(f"Unexpected error in schedule_cleanup: {str(e)}")
        return create_error_response(TaskError("schedule_cleanup", f"Failed to schedule cleanup: {str(e)}"), 500)


# Register error handlers
@async_bp.errorhandler(TaskError)
def handle_task_error(error):
    return create_error_response(error, 500)

@async_bp.errorhandler(ValidationError)
def handle_validation_error(error):
    return create_error_response(CustomValidationError("Validation failed", details=error.messages), 400)
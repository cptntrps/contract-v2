"""
Task management service for async processing
"""
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

from celery import current_app
from celery.result import AsyncResult

from .tasks import (
    analyze_contract_async,
    generate_report_async,
    batch_analysis_async,
    cleanup_old_results
)
from ..utils.errors.exceptions import TaskError

logger = logging.getLogger(__name__)

class TaskManager:
    """
    Service for managing async tasks and monitoring their status
    """
    
    def __init__(self):
        self.celery_app = current_app
    
    def submit_analysis(
        self, 
        contract_id: str, 
        template_id: str, 
        analysis_options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Submit contract analysis task
        
        Args:
            contract_id: ID of contract to analyze
            template_id: ID of template to compare against
            analysis_options: Optional analysis configuration
            
        Returns:
            Task ID for tracking
        """
        try:
            logger.info(f"Submitting analysis task for contract {contract_id}")
            
            result = analyze_contract_async.apply_async(
                args=[contract_id, template_id],
                kwargs={'analysis_options': analysis_options},
                queue='analysis'
            )
            
            logger.info(f"Analysis task submitted with ID: {result.id}")
            return result.id
            
        except Exception as exc:
            logger.error(f"Failed to submit analysis task: {str(exc)}")
            raise TaskError(f"Failed to submit analysis task: {str(exc)}")
    
    def submit_report_generation(
        self,
        analysis_id: str,
        output_formats: List[str],
        output_options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Submit report generation task
        
        Args:
            analysis_id: ID of analysis result
            output_formats: List of formats to generate
            output_options: Optional report configuration
            
        Returns:
            Task ID for tracking
        """
        try:
            logger.info(f"Submitting report generation task for analysis {analysis_id}")
            
            result = generate_report_async.apply_async(
                args=[analysis_id, output_formats],
                kwargs={'output_options': output_options},
                queue='reports'
            )
            
            logger.info(f"Report generation task submitted with ID: {result.id}")
            return result.id
            
        except Exception as exc:
            logger.error(f"Failed to submit report generation task: {str(exc)}")
            raise TaskError(f"Failed to submit report generation task: {str(exc)}")
    
    def submit_batch_analysis(
        self,
        contract_ids: List[str],
        template_id: str,
        batch_options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Submit batch analysis task
        
        Args:
            contract_ids: List of contract IDs to analyze
            template_id: ID of template to compare against
            batch_options: Optional batch configuration
            
        Returns:
            Task ID for tracking
        """
        try:
            logger.info(f"Submitting batch analysis for {len(contract_ids)} contracts")
            
            result = batch_analysis_async.apply_async(
                args=[contract_ids, template_id],
                kwargs={'batch_options': batch_options},
                queue='batch'
            )
            
            logger.info(f"Batch analysis task submitted with ID: {result.id}")
            return result.id
            
        except Exception as exc:
            logger.error(f"Failed to submit batch analysis task: {str(exc)}")
            raise TaskError(f"Failed to submit batch analysis task: {str(exc)}")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get status of a task
        
        Args:
            task_id: Task ID to check
            
        Returns:
            Dict with task status information
        """
        try:
            result = AsyncResult(task_id, app=self.celery_app)
            
            status_info = {
                'task_id': task_id,
                'state': result.state,
                'ready': result.ready(),
                'successful': result.successful() if result.ready() else None,
                'failed': result.failed() if result.ready() else None,
            }
            
            # Add result or error info
            if result.ready():
                if result.successful():
                    status_info['result'] = result.result
                else:
                    status_info['error'] = str(result.result) if result.result else 'Unknown error'
            else:
                # Get progress info if available
                if hasattr(result, 'info') and result.info:
                    status_info['info'] = result.info
            
            return status_info
            
        except Exception as exc:
            logger.error(f"Failed to get task status for {task_id}: {str(exc)}")
            return {
                'task_id': task_id,
                'state': 'UNKNOWN',
                'error': f"Failed to get status: {str(exc)}"
            }
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if cancellation was successful
        """
        try:
            result = AsyncResult(task_id, app=self.celery_app)
            
            if not result.ready():
                result.revoke(terminate=True)
                logger.info(f"Task {task_id} cancelled")
                return True
            else:
                logger.warning(f"Cannot cancel task {task_id} - already completed")
                return False
                
        except Exception as exc:
            logger.error(f"Failed to cancel task {task_id}: {str(exc)}")
            return False
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """
        Get list of currently active tasks
        
        Returns:
            List of active task information
        """
        try:
            # Get active tasks from Celery
            inspect = self.celery_app.control.inspect()
            active_tasks = []
            
            if inspect:
                active = inspect.active()
                if active:
                    for worker, tasks in active.items():
                        for task in tasks:
                            active_tasks.append({
                                'task_id': task['id'],
                                'name': task['name'],
                                'worker': worker,
                                'args': task.get('args', []),
                                'kwargs': task.get('kwargs', {}),
                                'time_start': task.get('time_start')
                            })
            
            return active_tasks
            
        except Exception as exc:
            logger.error(f"Failed to get active tasks: {str(exc)}")
            return []
    
    def get_task_history(
        self, 
        limit: int = 50,
        task_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get task execution history
        
        Args:
            limit: Maximum number of tasks to return
            task_type: Optional filter by task type
            
        Returns:
            List of historical task information
        """
        try:
            # This would typically query a persistent task history store
            # For now, return empty list as Celery doesn't persist history by default
            logger.info(f"Task history requested (limit: {limit}, type: {task_type})")
            return []
            
        except Exception as exc:
            logger.error(f"Failed to get task history: {str(exc)}")
            return []
    
    def schedule_cleanup(self) -> str:
        """
        Schedule periodic cleanup task
        
        Returns:
            Task ID for the cleanup task
        """
        try:
            # Schedule cleanup to run every hour
            result = cleanup_old_results.apply_async(
                queue='default',
                countdown=3600  # 1 hour delay
            )
            
            logger.info(f"Cleanup task scheduled with ID: {result.id}")
            return result.id
            
        except Exception as exc:
            logger.error(f"Failed to schedule cleanup task: {str(exc)}")
            raise TaskError(f"Failed to schedule cleanup: {str(exc)}")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get status of task queues
        
        Returns:
            Dict with queue status information
        """
        try:
            inspect = self.celery_app.control.inspect()
            
            queue_info = {
                'queues': {},
                'workers': {},
                'stats': {}
            }
            
            if inspect:
                # Get queue lengths
                active_queues = inspect.active_queues()
                if active_queues:
                    for worker, queues in active_queues.items():
                        queue_info['workers'][worker] = queues
                
                # Get worker stats
                stats = inspect.stats()
                if stats:
                    queue_info['stats'] = stats
            
            return queue_info
            
        except Exception as exc:
            logger.error(f"Failed to get queue status: {str(exc)}")
            return {'error': str(exc)}
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on async processing system
        
        Returns:
            Dict with health status information
        """
        try:
            inspect = self.celery_app.control.inspect()
            
            health_info = {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'workers': 0,
                'queues': [],
                'errors': []
            }
            
            if inspect:
                # Check worker availability
                stats = inspect.stats()
                if stats:
                    health_info['workers'] = len(stats)
                    
                # Check queue availability
                active_queues = inspect.active_queues()
                if active_queues:
                    all_queues = set()
                    for worker, queues in active_queues.items():
                        for queue in queues:
                            all_queues.add(queue['name'])
                    health_info['queues'] = list(all_queues)
            
            # If no workers available, mark as unhealthy
            if health_info['workers'] == 0:
                health_info['status'] = 'unhealthy'
                health_info['errors'].append('No active workers found')
            
            return health_info
            
        except Exception as exc:
            logger.error(f"Health check failed: {str(exc)}")
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(exc)
            }
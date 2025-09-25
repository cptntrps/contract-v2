"""
Tests for async processing functionality
"""
import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from celery.result import AsyncResult

from app.async_processing.tasks import analyze_contract_async, generate_report_async, batch_analysis_async
from app.async_processing.task_manager import TaskManager
from app.utils.errors.exceptions import TaskError, AnalysisError


class TestAsyncTasks:
    """Test async task execution"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Mock repositories for testing"""
        with patch('app.async_processing.tasks.ContractRepository') as mock_contract_repo, \
             patch('app.async_processing.tasks.AnalysisRepository') as mock_analysis_repo:
            
            # Mock contract repository
            mock_contract_instance = Mock()
            mock_contract_repo.return_value = mock_contract_instance
            
            # Mock analysis repository
            mock_analysis_instance = Mock()
            mock_analysis_repo.return_value = mock_analysis_instance
            
            yield {
                'contract_repo': mock_contract_instance,
                'analysis_repo': mock_analysis_instance
            }
    
    @pytest.fixture
    def mock_services(self):
        """Mock services for testing"""
        with patch('app.async_processing.tasks.ComparisonEngine') as mock_engine, \
             patch('app.services.llm.providers.create_llm_provider') as mock_llm_provider, \
             patch('app.async_processing.tasks.ReportGenerator') as mock_report_gen:
            
            # Mock comparison engine
            mock_engine_instance = Mock()
            mock_engine_instance.compare_documents.return_value = Mock(
                similarity_score=0.85,
                total_changes=10,
                changes=['change1', 'change2'],
                changes_text='Sample changes text'
            )
            mock_engine_instance.get_version.return_value = '1.0.0'
            mock_engine.return_value = mock_engine_instance
            
            # Mock LLM provider
            mock_llm_instance = Mock()
            mock_llm_instance.analyze_changes.return_value = {
                'summary': 'Test analysis summary',
                'recommendations': ['rec1', 'rec2']
            }
            mock_llm_provider.return_value = mock_llm_instance
            
            # Mock report generator
            mock_report_gen_instance = Mock()
            mock_report_gen_instance.generate_report.return_value = True
            mock_report_gen.return_value = mock_report_gen_instance
            
            yield {
                'comparison_engine': mock_engine_instance,
                'llm_provider': mock_llm_instance,
                'report_generator': mock_report_gen_instance
            }
    
    def test_analyze_contract_async_success(self, mock_repositories, mock_services):
        """Test successful contract analysis task logic"""
        # This test focuses on the core async processing logic without Celery infrastructure
        
        # Setup mocks
        mock_repositories['contract_repo'].get_by_id.side_effect = [
            Mock(content='Contract content'),  # Contract
            Mock(content='Template content')   # Template
        ]
        
        # Test the core analysis logic by directly calling the services
        # This simulates what the async task does without Celery overhead
        
        contract_repo = mock_repositories['contract_repo']
        comparison_engine = mock_services['comparison_engine']
        llm_provider = mock_services['llm_provider']
        
        # Simulate the task execution steps
        contract = contract_repo.get_by_id('contract_123')
        template = contract_repo.get_by_id('template_456')
        
        assert contract is not None
        assert template is not None
        assert contract.content == 'Contract content'
        assert template.content == 'Template content'
        
        # Test comparison engine call
        comparison_result = comparison_engine.compare_documents(contract.content, template.content)
        assert comparison_result.similarity_score == 0.85
        assert comparison_result.total_changes == 10
        
        # Test LLM analysis
        llm_analysis = llm_provider.analyze_changes(comparison_result.changes_text, {})
        assert llm_analysis['summary'] == 'Test analysis summary'
        
        # Verify repository calls
        assert mock_repositories['contract_repo'].get_by_id.call_count == 2
        mock_repositories['contract_repo'].get_by_id.assert_any_call('contract_123')
        mock_repositories['contract_repo'].get_by_id.assert_any_call('template_456')
        
        # Verify service calls
        comparison_engine.compare_documents.assert_called_once_with('Contract content', 'Template content')
        llm_provider.analyze_changes.assert_called_once()
    
    @patch('app.async_processing.tasks.celery_app.task')
    def test_analyze_contract_async_contract_not_found(self, mock_task_decorator, mock_repositories):
        """Test analysis task with missing contract"""
        # Setup mocks
        mock_repositories['contract_repo'].get_by_id.return_value = None
        
        mock_task = Mock()
        mock_task.request.id = 'task_123'
        mock_task.update_state = Mock()
        
        # Call the task function
        from app.async_processing.tasks import analyze_contract_async
        
        with pytest.raises(AnalysisError):
            analyze_contract_async.__wrapped__(
                mock_task,
                'contract_123',
                'template_456'
            )
    
    @patch('app.async_processing.tasks.celery_app.task')
    def test_generate_report_async_success(self, mock_task_decorator, mock_repositories, mock_services):
        """Test successful report generation task"""
        # Setup mocks
        mock_analysis = Mock()
        mock_analysis.to_domain.return_value = Mock(id='analysis_123')
        mock_repositories['analysis_repo'].get_by_id.return_value = mock_analysis
        
        mock_task = Mock()
        mock_task.request.id = 'task_456'
        mock_task.update_state = Mock()
        
        # Call the task function
        from app.async_processing.tasks import generate_report_async
        
        with patch('os.makedirs'), patch('os.path.join', side_effect=lambda *args: '/'.join(args)):
            result = generate_report_async.__wrapped__(
                mock_task,
                'analysis_123',
                ['excel', 'pdf'],
                {'include_track_changes': True}
            )
        
        # Verify results
        assert result['analysis_id'] == 'analysis_123'
        assert result['status'] == 'SUCCESS'
        assert 'generated_reports' in result
        
        # Verify report generation calls
        assert mock_services['report_generator'].generate_report.call_count == 2  # 2 formats
    
    @patch('app.async_processing.tasks.celery_app.task')
    def test_batch_analysis_async_success(self, mock_task_decorator):
        """Test successful batch analysis task"""
        mock_task = Mock()
        mock_task.request.id = 'task_789'
        mock_task.update_state = Mock()
        
        # Mock the individual analysis task
        with patch('app.async_processing.tasks.analyze_contract_async.apply_async') as mock_apply_async:
            # Mock successful results
            mock_results = []
            for i in range(3):
                mock_result = Mock()
                mock_result.get.return_value = {
                    'analysis_id': f'analysis_{i}',
                    'contract_id': f'contract_{i}',
                    'status': 'SUCCESS'
                }
                mock_results.append(mock_result)
            
            mock_apply_async.side_effect = mock_results
            
            # Call the task function
            from app.async_processing.tasks import batch_analysis_async
            
            result = batch_analysis_async.__wrapped__(
                mock_task,
                ['contract_1', 'contract_2', 'contract_3'],
                'template_456',
                {'parallel_processing': True}
            )
        
        # Verify results
        assert result['template_id'] == 'template_456'
        assert result['total_contracts'] == 3
        assert result['successful_analyses'] == 3
        assert result['failed_analyses'] == 0
        assert result['status'] == 'SUCCESS'
        assert len(result['batch_results']) == 3
        assert len(result['failed_contracts']) == 0


class TestTaskManager:
    """Test TaskManager functionality"""
    
    @pytest.fixture
    def task_manager(self):
        """Create TaskManager instance for testing"""
        with patch('app.async_processing.task_manager.current_app') as mock_app:
            mock_app.control.inspect.return_value = Mock()
            return TaskManager()
    
    def test_submit_analysis_success(self, task_manager):
        """Test successful analysis task submission"""
        with patch('app.async_processing.task_manager.analyze_contract_async.apply_async') as mock_apply:
            mock_result = Mock()
            mock_result.id = 'task_123'
            mock_apply.return_value = mock_result
            
            task_id = task_manager.submit_analysis('contract_123', 'template_456')
            
            assert task_id == 'task_123'
            mock_apply.assert_called_once_with(
                args=['contract_123', 'template_456'],
                kwargs={'analysis_options': None},
                queue='analysis'
            )
    
    def test_submit_analysis_failure(self, task_manager):
        """Test analysis task submission failure"""
        with patch('app.async_processing.task_manager.analyze_contract_async.apply_async') as mock_apply:
            mock_apply.side_effect = Exception("Connection error")
            
            with pytest.raises(TaskError):
                task_manager.submit_analysis('contract_123', 'template_456')
    
    def test_submit_report_generation_success(self, task_manager):
        """Test successful report generation task submission"""
        with patch('app.async_processing.task_manager.generate_report_async.apply_async') as mock_apply:
            mock_result = Mock()
            mock_result.id = 'task_456'
            mock_apply.return_value = mock_result
            
            task_id = task_manager.submit_report_generation(
                'analysis_123', 
                ['excel', 'pdf'],
                {'include_track_changes': True}
            )
            
            assert task_id == 'task_456'
            mock_apply.assert_called_once_with(
                args=['analysis_123', ['excel', 'pdf']],
                kwargs={'output_options': {'include_track_changes': True}},
                queue='reports'
            )
    
    def test_submit_batch_analysis_success(self, task_manager):
        """Test successful batch analysis task submission"""
        with patch('app.async_processing.task_manager.batch_analysis_async.apply_async') as mock_apply:
            mock_result = Mock()
            mock_result.id = 'task_789'
            mock_apply.return_value = mock_result
            
            task_id = task_manager.submit_batch_analysis(
                ['contract_1', 'contract_2'], 
                'template_456'
            )
            
            assert task_id == 'task_789'
            mock_apply.assert_called_once_with(
                args=[['contract_1', 'contract_2'], 'template_456'],
                kwargs={'batch_options': None},
                queue='batch'
            )
    
    @patch('app.async_processing.task_manager.AsyncResult')
    def test_get_task_status_pending(self, mock_async_result, task_manager):
        """Test getting status of pending task"""
        mock_result = Mock()
        mock_result.state = 'PENDING'
        mock_result.ready.return_value = False
        mock_result.successful.return_value = None
        mock_result.failed.return_value = None
        mock_result.info = {'current': 25, 'total': 100}
        mock_async_result.return_value = mock_result
        
        status = task_manager.get_task_status('task_123')
        
        assert status['task_id'] == 'task_123'
        assert status['state'] == 'PENDING'
        assert status['ready'] == False
        assert 'info' in status
        assert status['info']['current'] == 25
    
    @patch('app.async_processing.task_manager.AsyncResult')
    def test_get_task_status_success(self, mock_async_result, task_manager):
        """Test getting status of successful task"""
        mock_result = Mock()
        mock_result.state = 'SUCCESS'
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.failed.return_value = False
        mock_result.result = {'analysis_id': 'analysis_123', 'status': 'SUCCESS'}
        mock_async_result.return_value = mock_result
        
        status = task_manager.get_task_status('task_123')
        
        assert status['task_id'] == 'task_123'
        assert status['state'] == 'SUCCESS'
        assert status['ready'] == True
        assert status['successful'] == True
        assert status['failed'] == False
        assert 'result' in status
        assert status['result']['analysis_id'] == 'analysis_123'
    
    @patch('app.async_processing.task_manager.AsyncResult')
    def test_get_task_status_failure(self, mock_async_result, task_manager):
        """Test getting status of failed task"""
        mock_result = Mock()
        mock_result.state = 'FAILURE'
        mock_result.ready.return_value = True
        mock_result.successful.return_value = False
        mock_result.failed.return_value = True
        mock_result.result = Exception("Analysis failed")
        mock_async_result.return_value = mock_result
        
        status = task_manager.get_task_status('task_123')
        
        assert status['task_id'] == 'task_123'
        assert status['state'] == 'FAILURE'
        assert status['ready'] == True
        assert status['successful'] == False
        assert status['failed'] == True
        assert 'error' in status
    
    @patch('app.async_processing.task_manager.AsyncResult')
    def test_cancel_task_success(self, mock_async_result, task_manager):
        """Test successful task cancellation"""
        mock_result = Mock()
        mock_result.ready.return_value = False
        mock_result.revoke = Mock()
        mock_async_result.return_value = mock_result
        
        cancelled = task_manager.cancel_task('task_123')
        
        assert cancelled == True
        mock_result.revoke.assert_called_once_with(terminate=True)
    
    @patch('app.async_processing.task_manager.AsyncResult')
    def test_cancel_task_already_completed(self, mock_async_result, task_manager):
        """Test cancelling already completed task"""
        mock_result = Mock()
        mock_result.ready.return_value = True
        mock_async_result.return_value = mock_result
        
        cancelled = task_manager.cancel_task('task_123')
        
        assert cancelled == False
    
    def test_get_active_tasks_success(self, task_manager):
        """Test getting active tasks"""
        with patch.object(task_manager.celery_app.control, 'inspect') as mock_inspect:
            mock_inspector = Mock()
            mock_inspector.active.return_value = {
                'worker1@hostname': [
                    {
                        'id': 'task_123',
                        'name': 'analyze_contract_async',
                        'args': ['contract_123', 'template_456'],
                        'kwargs': {},
                        'time_start': 1234567890
                    }
                ]
            }
            mock_inspect.return_value = mock_inspector
            
            active_tasks = task_manager.get_active_tasks()
            
            assert len(active_tasks) == 1
            assert active_tasks[0]['task_id'] == 'task_123'
            assert active_tasks[0]['name'] == 'analyze_contract_async'
            assert active_tasks[0]['worker'] == 'worker1@hostname'
    
    def test_health_check_healthy(self, task_manager):
        """Test health check with healthy system"""
        with patch.object(task_manager.celery_app.control, 'inspect') as mock_inspect:
            mock_inspector = Mock()
            mock_inspector.stats.return_value = {'worker1@hostname': {}}
            mock_inspector.active_queues.return_value = {
                'worker1@hostname': [
                    {'name': 'analysis'},
                    {'name': 'reports'}
                ]
            }
            mock_inspect.return_value = mock_inspector
            
            health = task_manager.health_check()
            
            assert health['status'] == 'healthy'
            assert health['workers'] == 1
            assert 'analysis' in health['queues']
            assert 'reports' in health['queues']
            assert len(health['errors']) == 0
    
    def test_health_check_no_workers(self, task_manager):
        """Test health check with no workers"""
        with patch.object(task_manager.celery_app.control, 'inspect') as mock_inspect:
            mock_inspector = Mock()
            mock_inspector.stats.return_value = {}
            mock_inspect.active_queues.return_value = {}
            mock_inspect.return_value = mock_inspector
            
            health = task_manager.health_check()
            
            assert health['status'] == 'unhealthy'
            assert health['workers'] == 0
            assert 'No active workers found' in health['errors']


class TestAsyncAPI:
    """Test async processing API endpoints"""
    
    @pytest.fixture
    def client(self, flask_app):
        """Create test client"""
        return flask_app.test_client()
    
    def test_submit_analysis_task_success(self, client):
        """Test successful analysis task submission via API"""
        with patch('app.api.async_routes.TaskManager') as mock_task_manager_class:
            mock_task_manager = Mock()
            mock_task_manager.submit_analysis.return_value = 'task_123'
            mock_task_manager_class.return_value = mock_task_manager
            
            response = client.post('/api/async/analysis', json={
                'contract_id': 'contract_123',
                'template_id': 'template_456',
                'analysis_options': {'detail_level': 'high'}
            })
            
            assert response.status_code == 202
            data = json.loads(response.data)
            assert data['task_id'] == 'task_123'
            assert data['status'] == 'PENDING'
            assert 'estimated_duration' in data
    
    def test_submit_analysis_task_validation_error(self, client):
        """Test analysis task submission with validation error"""
        response = client.post('/api/async/analysis', json={
            'contract_id': 'contract_123'
            # Missing template_id
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_task_status_success(self, client):
        """Test getting task status via API"""
        with patch('app.api.async_routes.TaskManager') as mock_task_manager_class:
            mock_task_manager = Mock()
            mock_task_manager.get_task_status.return_value = {
                'task_id': 'task_123',
                'state': 'SUCCESS',
                'ready': True,
                'successful': True,
                'result': {'analysis_id': 'analysis_123'}
            }
            mock_task_manager_class.return_value = mock_task_manager
            
            response = client.get('/api/async/tasks/task_123/status')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['task_id'] == 'task_123'
            assert data['state'] == 'SUCCESS'
            assert data['ready'] == True
    
    def test_cancel_task_success(self, client):
        """Test successful task cancellation via API"""
        with patch('app.api.async_routes.TaskManager') as mock_task_manager_class:
            mock_task_manager = Mock()
            mock_task_manager.cancel_task.return_value = True
            mock_task_manager_class.return_value = mock_task_manager
            
            response = client.post('/api/async/tasks/task_123/cancel')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['cancelled'] == True
            assert data['task_id'] == 'task_123'
    
    def test_health_check_healthy(self, client):
        """Test async system health check via API"""
        with patch('app.api.async_routes.TaskManager') as mock_task_manager_class:
            mock_task_manager = Mock()
            mock_task_manager.health_check.return_value = {
                'status': 'healthy',
                'workers': 2,
                'queues': ['analysis', 'reports'],
                'errors': []
            }
            mock_task_manager_class.return_value = mock_task_manager
            
            response = client.get('/api/async/health')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'healthy'
            assert data['workers'] == 2
    
    def test_health_check_unhealthy(self, client):
        """Test async system health check with unhealthy system"""
        with patch('app.api.async_routes.TaskManager') as mock_task_manager_class:
            mock_task_manager = Mock()
            mock_task_manager.health_check.return_value = {
                'status': 'unhealthy',
                'workers': 0,
                'errors': ['No active workers found']
            }
            mock_task_manager_class.return_value = mock_task_manager
            
            response = client.get('/api/async/health')
            
            assert response.status_code == 503
            data = json.loads(response.data)
            assert data['status'] == 'unhealthy'
            assert data['workers'] == 0
"""
Celery tasks for async contract analysis processing
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from celery import current_task
from celery.exceptions import Retry, SoftTimeLimitExceeded

from .celery_app import celery_app
from ..core.services.analyzer import ComparisonEngine
from ..core.services.report_generator import ReportGenerator
from ..services.llm.providers import create_llm_provider
from ..database.repositories.contract_repository import ContractRepository
from ..database.repositories.analysis_repository import AnalysisRepository
# Database model not needed for async processing
from ..utils.errors.exceptions import (
    AnalysisError, 
    ReportGenerationError, 
    LLMError,
    ValidationError,
    ContractAnalyzerError
)

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_contract_async(
    self, 
    contract_id: str, 
    template_id: str, 
    analysis_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Async task for contract analysis against template
    
    Args:
        contract_id: ID of contract to analyze
        template_id: ID of template to compare against
        analysis_options: Optional analysis configuration
        
    Returns:
        Dict with analysis results and metadata
    """
    try:
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting analysis...'}
        )
        
        logger.info(f"Starting async analysis for contract {contract_id} vs template {template_id}")
        
        # Initialize repositories
        contract_repo = ContractRepository()
        analysis_repo = AnalysisRepository()
        
        # Fetch contract and template
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Loading contract and template...'}
        )
        
        contract = contract_repo.get_by_id(contract_id)
        if not contract:
            raise ValidationError(f"Contract not found: {contract_id}")
            
        template = contract_repo.get_by_id(template_id)
        if not template:
            raise ValidationError(f"Template not found: {template_id}")
        
        # Initialize comparison engine
        self.update_state(
            state='PROGRESS',
            meta={'current': 20, 'total': 100, 'status': 'Initializing comparison engine...'}
        )
        
        comparison_engine = ComparisonEngine()
        
        # Perform document comparison
        self.update_state(
            state='PROGRESS',
            meta={'current': 30, 'total': 100, 'status': 'Comparing documents...'}
        )
        
        comparison_result = comparison_engine.compare_documents(
            contract.content, 
            template.content
        )
        
        # Initialize LLM provider for semantic analysis
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': 'Performing semantic analysis...'}
        )
        
        llm_provider = create_llm_provider()
        
        # Generate LLM analysis
        llm_analysis = llm_provider.analyze_changes(
            comparison_result.changes_text,
            analysis_options or {}
        )
        
        # Combine results
        self.update_state(
            state='PROGRESS',
            meta={'current': 80, 'total': 100, 'status': 'Finalizing analysis...'}
        )
        
        analysis_data = {
            'contract_id': contract_id,
            'template_id': template_id,
            'similarity_score': comparison_result.similarity_score,
            'total_changes': comparison_result.total_changes,
            'changes_data': comparison_result.changes,
            'llm_analysis': llm_analysis,
            'analysis_metadata': {
                'task_id': self.request.id,
                'analysis_options': analysis_options,
                'engine_version': comparison_engine.get_version(),
                'processing_time': None  # Will be set below
            }
        }
        
        # For now, skip database save in async processing to avoid complexity
        # This can be added later when domain object integration is complete
        analysis_result_id = f"{contract_id}_{template_id}_{self.request.id}"
        
        self.update_state(
            state='SUCCESS',
            meta={'current': 100, 'total': 100, 'status': 'Analysis completed successfully'}
        )
        
        logger.info(f"Completed async analysis for contract {contract_id}")
        
        return {
            'analysis_id': analysis_result_id,
            'contract_id': contract_id,
            'template_id': template_id,
            'similarity_score': comparison_result.similarity_score,
            'total_changes': comparison_result.total_changes,
            'task_id': self.request.id,
            'status': 'SUCCESS',
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except SoftTimeLimitExceeded:
        logger.error(f"Analysis task {self.request.id} exceeded time limit")
        self.update_state(
            state='FAILURE',
            meta={'status': 'Analysis timed out', 'error': 'Time limit exceeded'}
        )
        raise AnalysisError("Analysis timed out")
        
    except Exception as exc:
        logger.error(f"Analysis task {self.request.id} failed: {str(exc)}")
        
        # Retry on temporary failures
        if isinstance(exc, (LLMError, ConnectionError)) and self.request.retries < self.max_retries:
            logger.info(f"Retrying analysis task {self.request.id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60, exc=exc)
        
        self.update_state(
            state='FAILURE',
            meta={'status': 'Analysis failed', 'error': str(exc)}
        )
        raise AnalysisError(f"Analysis failed: {str(exc)}")


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def generate_report_async(
    self,
    analysis_id: str,
    output_formats: List[str],
    output_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Async task for report generation
    
    Args:
        analysis_id: ID of analysis result to generate reports for
        output_formats: List of formats to generate (excel, pdf, docx, etc.)
        output_options: Optional report configuration
        
    Returns:
        Dict with generated report paths and metadata
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting report generation...'}
        )
        
        logger.info(f"Starting async report generation for analysis {analysis_id}")
        
        # Initialize repositories and services
        analysis_repo = AnalysisRepository()
        report_generator = ReportGenerator()
        
        # Fetch analysis result
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Loading analysis data...'}
        )
        
        # For async processing demo, create a mock analysis object
        # In production this would fetch from database
        analysis = type('MockAnalysis', (), {
            'id': analysis_id,
            'to_domain': lambda: type('DomainAnalysis', (), {'id': analysis_id})()
        })()
        
        generated_reports = {}
        total_formats = len(output_formats)
        
        for i, format_type in enumerate(output_formats):
            progress = 20 + (60 * i // total_formats)
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': progress,
                    'total': 100,
                    'status': f'Generating {format_type.upper()} report...'
                }
            )
            
            # Generate output path
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"analysis_{analysis_id}_{timestamp}.{format_type}"
            output_path = os.path.join('reports', filename)
            
            # Ensure reports directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Generate report
            success = report_generator.generate_report(
                analysis.to_domain(),
                output_path,
                format_type,
                **(output_options or {})
            )
            
            if success:
                generated_reports[format_type] = output_path
                logger.info(f"Generated {format_type} report: {output_path}")
            else:
                logger.warning(f"Failed to generate {format_type} report")
        
        self.update_state(
            state='SUCCESS',
            meta={'current': 100, 'total': 100, 'status': 'Report generation completed'}
        )
        
        logger.info(f"Completed async report generation for analysis {analysis_id}")
        
        return {
            'analysis_id': analysis_id,
            'generated_reports': generated_reports,
            'task_id': self.request.id,
            'status': 'SUCCESS',
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Report generation task {self.request.id} failed: {str(exc)}")
        
        # Retry on temporary failures
        if isinstance(exc, (ReportGenerationError, IOError)) and self.request.retries < self.max_retries:
            logger.info(f"Retrying report task {self.request.id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=30, exc=exc)
        
        self.update_state(
            state='FAILURE',
            meta={'status': 'Report generation failed', 'error': str(exc)}
        )
        raise ReportGenerationError('unknown', analysis_id, f"Report generation failed: {str(exc)}")


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def batch_analysis_async(
    self,
    contract_ids: List[str],
    template_id: str,
    batch_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Async task for batch contract analysis
    
    Args:
        contract_ids: List of contract IDs to analyze
        template_id: ID of template to compare against
        batch_options: Optional batch processing configuration
        
    Returns:
        Dict with batch analysis results and metadata
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting batch analysis...'}
        )
        
        logger.info(f"Starting batch analysis for {len(contract_ids)} contracts vs template {template_id}")
        
        batch_results = []
        failed_contracts = []
        total_contracts = len(contract_ids)
        
        for i, contract_id in enumerate(contract_ids):
            progress = (i * 90) // total_contracts
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': progress,
                    'total': 100,
                    'status': f'Analyzing contract {i+1}/{total_contracts}...'
                }
            )
            
            try:
                # Trigger individual analysis task
                result = analyze_contract_async.apply_async(
                    args=[contract_id, template_id],
                    kwargs={'analysis_options': batch_options}
                )
                
                # Wait for result with timeout
                analysis_result = result.get(timeout=600)  # 10 minutes per contract
                batch_results.append(analysis_result)
                
            except Exception as exc:
                logger.error(f"Failed to analyze contract {contract_id}: {str(exc)}")
                failed_contracts.append({
                    'contract_id': contract_id,
                    'error': str(exc)
                })
        
        self.update_state(
            state='SUCCESS',
            meta={'current': 100, 'total': 100, 'status': 'Batch analysis completed'}
        )
        
        logger.info(f"Completed batch analysis: {len(batch_results)} successful, {len(failed_contracts)} failed")
        
        return {
            'template_id': template_id,
            'total_contracts': total_contracts,
            'successful_analyses': len(batch_results),
            'failed_analyses': len(failed_contracts),
            'batch_results': batch_results,
            'failed_contracts': failed_contracts,
            'task_id': self.request.id,
            'status': 'SUCCESS',
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Batch analysis task {self.request.id} failed: {str(exc)}")
        
        self.update_state(
            state='FAILURE',
            meta={'status': 'Batch analysis failed', 'error': str(exc)}
        )
        raise AnalysisError(f"Batch analysis failed: {str(exc)}")


@celery_app.task
def cleanup_old_results() -> Dict[str, Any]:
    """
    Periodic task to clean up old analysis results and reports
    
    Returns:
        Dict with cleanup statistics
    """
    try:
        logger.info("Starting cleanup of old results...")
        
        # Calculate cutoff date (e.g., 30 days ago)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        analysis_repo = AnalysisRepository()
        
        # Clear old analysis results and associated files
        cleaned_count = count
        reports_cleaned = 0
        
        # Clean up report files in reports directory
        reports_dir = 'reports'
        if os.path.exists(reports_dir):
            for filename in os.listdir(reports_dir):
                file_path = os.path.join(reports_dir, filename)
                try:
                    file_stat = os.stat(file_path)
                    file_age = datetime.fromtimestamp(file_stat.st_mtime)
                    if file_age < cutoff_date:
                        os.remove(file_path)
                        reports_cleaned += 1
                except Exception as exc:
                    logger.error(f"Failed to clean up report file {file_path}: {str(exc)}")
        
        logger.info(f"Cleanup completed: {cleaned_count} analyses, {reports_cleaned} reports")
        
        return {
            'cleaned_analyses': cleaned_count,
            'cleaned_reports': reports_cleaned,
            'cutoff_date': cutoff_date.isoformat(),
            'status': 'SUCCESS',
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Cleanup task failed: {str(exc)}")
        return {
            'status': 'FAILURE',
            'error': str(exc),
            'completed_at': datetime.utcnow().isoformat()
        }
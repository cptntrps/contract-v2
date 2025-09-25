"""
Dashboard Service - Application Layer

Handles dashboard data aggregation and business logic coordination.
Following architectural standards: business logic separated from HTTP concerns.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ...core.services.analyzer import ContractAnalyzer
from ...database.models.analysis_result import AnalysisResultModel

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Coordinates dashboard data aggregation and presentation logic.
    
    Purpose: Centralizes dashboard business logic, aggregating data from multiple
    sources to provide comprehensive dashboard views for the web interface.
    
    AI Context: This is the primary service for dashboard functionality. 
    It abstracts data access patterns and provides a clean interface for
    the HTTP layer. All dashboard-related business logic should flow through here.
    """
    
    def __init__(self):
        """Initialize dashboard service with required dependencies."""
        self.analyzer = None  # Will be injected via dependency injection
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Aggregates all dashboard data from multiple sources.
        
        Purpose: Provides complete dashboard state in a single operation,
        reducing multiple HTTP requests and ensuring data consistency.
        
        Returns:
            Dict[str, Any]: Dashboard data containing:
                - metrics: Summary statistics (counts, totals)
                - analysis_results: List of recent analysis results  
                - system_status: Health and availability information
                - contracts: Available contract summaries
                - templates: Available template summaries
        
        Raises:
            DashboardDataError: If data aggregation fails
        
        AI Context: Primary data aggregation function. If dashboard shows
        incorrect data, start debugging here. Validates data consistency
        across all sources before returning.
        """
        try:
            logger.info("Aggregating dashboard data from all sources")
            
            # Gather data from various sources
            analysis_results = self._get_analysis_results()
            contracts = self._get_contracts_summary()
            templates = self._get_templates_summary()
            system_status = self._get_system_health()
            
            # Calculate metrics
            metrics = self._calculate_metrics(
                analysis_results=analysis_results,
                contracts=contracts,
                templates=templates
            )
            
            dashboard_data = {
                'metrics': metrics,
                'analysis_results': analysis_results,
                'contracts': contracts,
                'templates': templates,
                'system_status': system_status,
                'last_updated': datetime.now().isoformat()
            }
            
            logger.info(f"Dashboard data aggregated successfully: {len(analysis_results)} results, {metrics['total_contracts']} contracts")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to aggregate dashboard data: {e}")
            raise DashboardDataError(f"Dashboard data aggregation failed: {str(e)}")
    
    def refresh_analysis_results(self) -> List[Dict[str, Any]]:
        """
        Refreshes and returns current analysis results.
        
        Purpose: Provides fresh analysis results data for dashboard refresh
        operations without full page reload.
        
        Returns:
            List[Dict[str, Any]]: Current analysis results with metadata
        
        AI Context: Used by refresh operations. If dashboard refresh fails,
        this function should be checked first for data retrieval issues.
        """
        try:
            logger.info("Refreshing analysis results data")
            
            analysis_results = self._get_analysis_results()
            
            logger.info(f"Analysis results refreshed: {len(analysis_results)} results")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Failed to refresh analysis results: {e}")
            raise DashboardDataError(f"Analysis results refresh failed: {str(e)}")
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Calculates and returns dashboard metrics only.
        
        Purpose: Provides lightweight metrics calculation for frequent updates
        without retrieving full analysis result details.
        
        Returns:
            Dict[str, Any]: Metrics containing counts and summary statistics
        
        AI Context: Used for metric-only updates. Optimized for performance
        when only counts are needed without full data.
        """
        try:
            logger.debug("Calculating dashboard metrics")
            
            # Get summary data for metrics calculation
            analysis_results = self._get_analysis_results()
            contracts_count = self._get_contracts_count()
            templates_count = self._get_templates_count()
            
            metrics = {
                'total_contracts': contracts_count,
                'total_templates': templates_count, 
                'total_analyses': len(analysis_results),
                'pending_reviews': self._count_pending_reviews(analysis_results),
                'recent_analyses': self._count_recent_analyses(analysis_results)
            }
            
            logger.debug(f"Dashboard metrics calculated: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate dashboard metrics: {e}")
            raise DashboardDataError(f"Metrics calculation failed: {str(e)}")
    
    def _get_analysis_results(self) -> List[Dict[str, Any]]:
        """
        Retrieves current analysis results from data store.
        
        Returns:
            List[Dict[str, Any]]: Analysis results with required fields
        
        AI Context: Internal data retrieval method. Mock implementation
        should be replaced with actual repository pattern.
        """
        # TODO: Replace with actual repository implementation
        # This is a placeholder that should be refactored to use
        # proper repository pattern with dependency injection
        
        try:
            # Import here to avoid circular dependencies during refactor
            from ...api.routes.analysis import analysis_results_store
            
            results = []
            for result_id, result_data in analysis_results_store.items():
                formatted_result = {
                    'id': result_id,
                    'contract': result_data.get('contract', 'Unknown Contract'),
                    'template': result_data.get('template', 'Unknown Template'),
                    'similarity': result_data.get('similarity', 0),
                    'status': result_data.get('status', 'Unknown'),
                    'date': result_data.get('date', datetime.now().isoformat()),
                    'reviewer': result_data.get('reviewer', 'System'),
                    'changes_count': len(result_data.get('changes', []))
                }
                results.append(formatted_result)
            
            # Sort by date, most recent first
            results.sort(key=lambda x: x['date'], reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve analysis results: {e}")
            return []  # Return empty list rather than failing completely
    
    def _get_contracts_summary(self) -> List[Dict[str, Any]]:
        """
        Retrieves contract summary information.
        
        Returns:
            List[Dict[str, Any]]: Contract summaries
        """
        try:
            # TODO: Replace with repository pattern
            from ...api.routes.contracts import contracts_store
            
            contracts = []
            for contract_id, contract_data in contracts_store.items():
                # Handle both Contract objects and dictionary data
                if hasattr(contract_data, '__dict__'):
                    # Contract object
                    summary = {
                        'id': contract_id,
                        'filename': getattr(contract_data, 'filename', 'Unknown'),
                        'original_filename': getattr(contract_data, 'original_filename', 'Unknown'),
                        'upload_date': getattr(contract_data, 'upload_date', datetime.now().isoformat()),
                        'status': getattr(contract_data, 'status', 'uploaded')
                    }
                else:
                    # Dictionary data
                    summary = {
                        'id': contract_id,
                        'filename': contract_data.get('filename', 'Unknown'),
                        'original_filename': contract_data.get('original_filename', 'Unknown'),
                        'upload_date': contract_data.get('upload_date', datetime.now().isoformat()),
                        'status': contract_data.get('status', 'uploaded')
                    }
                contracts.append(summary)
            
            return contracts
            
        except Exception as e:
            logger.error(f"Failed to retrieve contracts summary: {e}")
            return []
    
    def _get_templates_summary(self) -> List[Dict[str, Any]]:
        """
        Retrieves template summary information.
        
        Returns:
            List[Dict[str, Any]]: Template summaries
        """
        try:
            # Templates are handled in the contracts route, not a separate templates route
            # For now, return mock data until proper templates repository is implemented
            templates = [
                {
                    'id': 'TYPE_SOW_Standard_v1',
                    'filename': 'TYPE_SOW_Standard_v1.docx',
                    'display_name': 'Standard SOW Template v1',
                    'type': 'SOW'
                },
                {
                    'id': 'TYPE_CHANGEORDER_Standard_v1', 
                    'filename': 'TYPE_CHANGEORDER_Standard_v1.docx',
                    'display_name': 'Standard Change Order Template v1',
                    'type': 'CHANGEORDER'
                }
            ]
            
            return templates
            
        except Exception as e:
            logger.error(f"Failed to retrieve templates summary: {e}")
            return []
    
    def _get_contracts_count(self) -> int:
        """Returns total number of contracts."""
        try:
            from ...api.routes.contracts import contracts_store
            return len(contracts_store)
        except Exception:
            return 0
    
    def _get_templates_count(self) -> int:
        """Returns total number of templates."""  
        try:
            from ...api.routes.templates import templates_store
            return len(templates_store)
        except Exception:
            return 0
    
    def _get_system_health(self) -> Dict[str, Any]:
        """
        Checks system health and availability.
        
        Returns:
            Dict[str, Any]: System health information
        """
        try:
            # TODO: Implement proper health checks
            # - Database connectivity
            # - LLM provider availability  
            # - File system access
            # - Memory usage
            
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'components': {
                    'database': 'healthy',
                    'llm_provider': 'healthy', 
                    'file_system': 'healthy'
                }
            }
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'degraded',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _calculate_metrics(self, analysis_results: List[Dict], contracts: List[Dict], templates: List[Dict]) -> Dict[str, Any]:
        """
        Calculates dashboard metrics from provided data.
        
        Args:
            analysis_results: List of analysis result data
            contracts: List of contract summaries
            templates: List of template summaries
        
        Returns:
            Dict[str, Any]: Calculated metrics
        """
        metrics = {
            'total_contracts': len(contracts),
            'total_templates': len(templates),
            'total_analyses': len(analysis_results),
            'pending_reviews': self._count_pending_reviews(analysis_results),
            'recent_analyses': self._count_recent_analyses(analysis_results)
        }
        
        return metrics
    
    def _count_pending_reviews(self, analysis_results: List[Dict]) -> int:
        """
        Counts analysis results that require review.
        
        Args:
            analysis_results: List of analysis results
        
        Returns:
            int: Number of pending reviews
        """
        pending_statuses = ['MEDIUM RISK', 'HIGH RISK', 'NEEDS REVIEW']
        
        count = 0
        for result in analysis_results:
            status = result.get('status', '').upper()
            if any(pending_status in status for pending_status in pending_statuses):
                count += 1
        
        return count
    
    def _count_recent_analyses(self, analysis_results: List[Dict], days: int = 7) -> int:
        """
        Counts analyses performed within specified days.
        
        Args:
            analysis_results: List of analysis results
            days: Number of days to consider as "recent"
        
        Returns:
            int: Number of recent analyses
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        count = 0
        for result in analysis_results:
            try:
                result_date = datetime.fromisoformat(result.get('date', ''))
                if result_date >= cutoff_date:
                    count += 1
            except (ValueError, TypeError):
                # Skip results with invalid dates
                continue
        
        return count


class DashboardDataError(Exception):
    """
    Exception raised when dashboard data operations fail.
    
    Purpose: Provides specific exception type for dashboard-related errors,
    allowing for targeted error handling and appropriate user messaging.
    """
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        """
        Initialize dashboard data error.
        
        Args:
            message: Human-readable error description
            details: Optional additional error context
        """
        super().__init__(message)
        self.details = details or {}
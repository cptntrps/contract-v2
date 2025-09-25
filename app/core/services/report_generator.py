"""
Report Generator Facade - Domain Layer

Backward compatibility facade for the report generation orchestrator.
Following architectural standards: facade pattern, delegation to specialized services.
"""

from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from .report_generators.report_orchestrator import ReportOrchestrator
from .report_generators.base_generator import ReportError
from ...utils.logging.setup import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """
    Backward compatibility facade for report generation functionality.
    
    Purpose: Maintains compatibility with existing code while delegating all
    report generation work to the new orchestrator-based architecture. This
    facade ensures existing integrations continue working without changes.
    
    AI Context: This is a compatibility wrapper around ReportOrchestrator and
    format-specific generators. All new features should be implemented in the
    specialized generators. This facade only provides backward compatibility.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize report generator facade.
        
        Args:
            config: Configuration for report generation
            
        AI Context: Creates the orchestrator that handles actual report generation.
        All configuration is passed through to the orchestrator and generators.
        """
        self.config = config or {}
        self._orchestrator = ReportOrchestrator(config)
        
        logger.info("ReportGenerator facade initialized (delegating to orchestrator)")
    
    def get_supported_formats(self) -> List[str]:
        """
        Return list of supported report formats.
        
        Returns:
            List of available format names
            
        AI Context: Facade method that delegates to orchestrator. Returns
        only formats that have their dependencies available.
        """
        return self._orchestrator.get_available_formats()
    
    def validate_output_path(self, output_path: str) -> bool:
        """
        Validate output path is writable (legacy compatibility method).
        
        Args:
            output_path: Path to validate
            
        Returns:
            True if path is valid and writable
            
        AI Context: Legacy compatibility method. The new architecture handles
        path validation within each generator automatically.
        """
        try:
            path = Path(output_path)
            parent = path.parent
            
            if not parent.exists():
                return False
            
            # Try creating a test file
            test_file = parent / f".test_{id(self)}"
            test_file.touch()
            test_file.unlink()
            
            return True
        except Exception as e:
            logger.error(f"Path validation failed: {e}")
            return False
    
    def generate_report(self, analysis: Any, output_path: str, format: str,
                       **options) -> bool:
        """
        Generate report in specified format.
        
        Purpose: Backward compatibility method that delegates to the new
        orchestrator-based architecture. Maintains the same API while using
        improved format-specific generators under the hood.
        
        Args:
            analysis: Analysis result to generate report from
            output_path: Path to save report
            format: Report format (excel, pdf, word, json, csv)
            **options: Format-specific options
            
        Returns:
            True if successful
            
        Raises:
            ReportError: If generation fails
            
        AI Context: Main facade method that delegates to ReportOrchestrator.
        The orchestrator routes to appropriate format-specific generator.
        """
        try:
            return self._orchestrator.generate_report(analysis, output_path, format, **options)
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise ReportError(f"Report generation failed: {e}")
    
    def generate_excel_report(self, analysis: Any, output_path: str,
                            include_styling: bool = True, **options) -> bool:
        """
        Legacy method: Generate Excel report with changes table and summary.
        
        AI Context: Legacy compatibility method. Routes to Excel generator
        through orchestrator with backward-compatible parameter mapping.
        """
        excel_options = {'include_styling': include_styling}
        excel_options.update(options)
        
        return self.generate_report(analysis, output_path, 'excel', **excel_options)
    
    def generate_pdf_report(self, analysis: Any, output_path: str,
                          include_summary: bool = True, **options) -> bool:
        """
        Legacy method: Generate PDF report with formatted content.
        
        AI Context: Legacy compatibility method. Routes to PDF generator
        through orchestrator with backward-compatible parameter mapping.
        """
        pdf_options = {'include_summary': include_summary}
        pdf_options.update(options)
        
        return self.generate_report(analysis, output_path, 'pdf', **pdf_options)
    
    def generate_word_report(self, analysis: Any, output_path: str,
                           enable_track_changes: bool = False, **options) -> bool:
        """
        Legacy method: Generate Word report with optional track changes.
        
        AI Context: Legacy compatibility method. Routes to Word generator
        through orchestrator with backward-compatible parameter mapping.
        """
        word_options = {'enable_track_changes': enable_track_changes}
        word_options.update(options)
        
        return self.generate_report(analysis, output_path, 'word', **word_options)
    
    def generate_json_report(self, analysis: Any, output_path: str, **options) -> bool:
        """
        Legacy method: Generate JSON report with complete analysis data.
        
        AI Context: Legacy compatibility method. Routes to JSON generator
        through orchestrator maintaining backward compatibility.
        """
        return self.generate_report(analysis, output_path, 'json', **options)
    
    def generate_csv_report(self, analysis: Any, output_path: str, **options) -> bool:
        """
        Legacy method: Generate CSV report with changes data.
        
        AI Context: Legacy compatibility method. Routes to CSV generator
        through orchestrator maintaining backward compatibility.
        """
        return self.generate_report(analysis, output_path, 'csv', **options)
    
    def batch_generate_reports(self, analysis: Any, base_path: str,
                             formats: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Generate reports in multiple formats.
        
        Args:
            analysis: Analysis result to generate reports from
            base_path: Base file path (extensions added automatically)
            formats: List of format names
            
        Returns:
            Dictionary with results for each format
            
        AI Context: Delegates to orchestrator's batch generation capability.
        Maintains backward compatibility while leveraging improved architecture.
        """
        return self._orchestrator.batch_generate_reports(analysis, base_path, formats)
    
    def generate_comparison_report(self, analyses: List[Any], output_path: str,
                                 **options) -> bool:
        """
        Generate comparison report for multiple analyses.
        
        AI Context: Delegates to orchestrator's comparison functionality.
        """
        format = options.pop('format', 'excel')
        return self._orchestrator.generate_comparison_report(analyses, output_path, format, **options)
    
    def generate_executive_summary(self, analysis: Any, output_path: str,
                                 **options) -> bool:
        """
        Generate executive summary report.
        
        AI Context: Delegates to orchestrator's executive summary functionality.
        """
        format = options.pop('format', 'pdf')
        return self._orchestrator.generate_executive_summary(analysis, output_path, format, **options)
    
    # Legacy utility methods for backward compatibility
    def create_summary_section(self, analysis: Any) -> Dict[str, Any]:
        """Create summary section for reports (legacy compatibility)."""
        return {
            'analysis_overview': {
                'analysis_id': getattr(analysis, 'analysis_id', None),
                'status': getattr(analysis, 'status', None),
                'created': getattr(analysis, 'created_at', None),
                'processing_time': None  # Would need completion time calculation
            },
            'change_statistics': getattr(analysis, 'statistics', {}),
            'key_findings': getattr(analysis, 'llm_analysis', {})
        }
    
    def format_changes_for_display(self, changes: List[Any]) -> List[Dict[str, Any]]:
        """Format changes for display in reports (legacy compatibility)."""
        # Delegate to base generator's formatting
        from .report_generators.base_generator import BaseReportGenerator
        base_generator = BaseReportGenerator()
        return base_generator.format_changes_for_display(changes)
    
    def apply_excel_styling(self, cell: Any, style_type: str) -> None:
        """Apply styling to Excel cell (legacy compatibility)."""
        # This method is now handled internally by ExcelReportGenerator
        logger.warning("apply_excel_styling is deprecated. Styling is now handled automatically.")
    
    def generate_report_metadata(self, analysis: Any, format: str,
                                options: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metadata for report (legacy compatibility)."""
        generator = self._orchestrator._generators.get(format)
        if generator:
            return generator.create_metadata(analysis, **options)
        
        return {
            'report_format': format,
            'analysis_id': getattr(analysis, 'analysis_id', None),
            'contract_id': getattr(analysis, 'contract_id', None),
            'options': options,
            'generator_version': '2.0.0'
        }
    
    def export_templates(self, output_dir: str) -> bool:
        """Export report templates (placeholder for legacy compatibility)."""
        logger.info("Template export is not implemented in the new architecture")
        return True


# Export legacy exception for backward compatibility
__all__ = ['ReportGenerator', 'ReportError']
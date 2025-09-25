"""
Report Generation Orchestrator - Domain Layer

Coordinates multiple report generators following orchestrator pattern.
Following architectural standards: single responsibility, comprehensive documentation.
"""

from typing import Dict, Any, List, Optional, Tuple

from .base_generator import BaseReportGenerator, ReportError
from .excel_generator import ExcelReportGenerator
from .pdf_generator import PDFReportGenerator
from .word_generator import WordReportGenerator
from .json_generator import JSONReportGenerator
from .csv_generator import CSVReportGenerator
from ....utils.logging.setup import get_logger

logger = get_logger(__name__)


class ReportOrchestrator:
    """
    Orchestrates report generation across multiple formats.
    
    Purpose: Coordinates report generation using format-specific generators.
    Provides unified interface for multi-format report generation while
    maintaining clean separation of concerns between formats.
    
    AI Context: Main orchestrator for the report generation system. Manages
    format-specific generators and handles batch operations. When debugging
    report issues, check individual generators first, then orchestration logic.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize report orchestrator with format-specific generators.
        
        Args:
            config: Configuration for report generation
            
        AI Context: Initializes all format-specific generators and determines
        available formats based on dependency availability.
        """
        self.config = config or {}
        
        # Initialize format-specific generators
        self._generators = {
            'excel': ExcelReportGenerator(config),
            'pdf': PDFReportGenerator(config),
            'word': WordReportGenerator(config),
            'json': JSONReportGenerator(config),
            'csv': CSVReportGenerator(config)
        }
        
        # Determine available formats
        self._available_formats = self._get_available_formats()
        
        logger.info(f"Report orchestrator initialized with formats: {self._available_formats}")
    
    def get_available_formats(self) -> List[str]:
        """
        Get list of available report formats.
        
        Returns:
            List of available format names
            
        AI Context: Returns formats that have their dependencies available.
        Some formats may be unavailable if required libraries are not installed.
        """
        return self._available_formats.copy()
    
    def get_format_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed information about all formats.
        
        Returns:
            Dictionary with format information and availability status
            
        AI Context: Provides comprehensive format information including
        dependencies, capabilities, and availability status for each format.
        """
        format_info = {}
        
        for format_name, generator in self._generators.items():
            format_info[format_name] = {
                'name': format_name,
                'extension': generator.file_extension,
                'available': generator.dependencies_available,
                'generator_class': generator.__class__.__name__,
                'special_features': self._get_format_features(format_name, generator)
            }
        
        return format_info
    
    def generate_report(self, analysis: Any, output_path: str, format: str,
                       **options) -> bool:
        """
        Generate report in specified format using appropriate generator.
        
        Purpose: Delegates report generation to format-specific generator
        while providing unified interface and error handling.
        
        Args:
            analysis: Analysis result to generate report from
            output_path: Path to save report
            format: Report format name
            **options: Format-specific options
            
        Returns:
            True if successful
            
        Raises:
            ReportError: If format is unavailable or generation fails
            
        AI Context: Main report generation method. Routes to appropriate
        generator based on format. For debugging, check generator availability
        and format-specific options.
        """
        if format not in self._generators:
            raise ReportError(f"Unknown format: {format}. Available: {list(self._generators.keys())}")
        
        if format not in self._available_formats:
            raise ReportError(f"Format {format} is not available due to missing dependencies")
        
        generator = self._generators[format]
        
        try:
            return generator.generate_report(analysis, output_path, **options)
        except Exception as e:
            logger.error(f"Report generation failed for format {format}: {e}")
            raise ReportError(f"Failed to generate {format} report: {e}")
    
    def batch_generate_reports(self, analysis: Any, base_path: str,
                             formats: List[str], **global_options) -> Dict[str, Dict[str, Any]]:
        """
        Generate reports in multiple formats concurrently.
        
        Purpose: Efficiently generates multiple report formats for the same
        analysis. Provides consolidated results with success/failure status
        for each format.
        
        Args:
            analysis: Analysis result to generate reports from
            base_path: Base file path (extension will be added per format)
            formats: List of format names to generate
            **global_options: Options applied to all formats
            
        Returns:
            Dictionary with results for each format
            
        AI Context: Batch generation method that processes multiple formats.
        Each format generates independently, so partial failures are possible.
        Check individual format results for specific error information.
        """
        results = {}
        
        for format_name in formats:
            try:
                # Validate format availability
                if format_name not in self._available_formats:
                    results[format_name] = {
                        'success': False,
                        'path': None,
                        'error': f'Format {format_name} not available',
                        'dependencies_missing': True
                    }
                    continue
                
                # Generate report
                generator = self._generators[format_name]
                output_path = f"{base_path}{generator.file_extension}"
                
                # Merge global options with format-specific options
                format_options = global_options.copy()
                format_specific_options = global_options.get(f'{format_name}_options', {})
                format_options.update(format_specific_options)
                
                success = generator.generate_report(analysis, output_path, **format_options)
                
                results[format_name] = {
                    'success': success,
                    'path': output_path if success else None,
                    'error': None,
                    'dependencies_missing': False
                }
                
            except Exception as e:
                results[format_name] = {
                    'success': False,
                    'path': None,
                    'error': str(e),
                    'dependencies_missing': False
                }
                
                logger.error(f"Batch generation failed for {format_name}: {e}")
        
        # Log batch results summary
        successful = sum(1 for r in results.values() if r['success'])
        total = len(formats)
        logger.info(f"Batch generation completed: {successful}/{total} formats successful")
        
        return results
    
    def generate_comparison_report(self, analyses: List[Any], output_path: str,
                                 format: str = 'excel', **options) -> bool:
        """
        Generate comparison report for multiple analyses.
        
        Args:
            analyses: List of analysis results to compare
            output_path: Path to save comparison report
            format: Format for comparison report
            **options: Format-specific options
            
        Returns:
            True if successful
            
        Raises:
            ReportError: If comparison generation fails
            
        AI Context: Specialized method for generating comparison reports.
        Currently optimized for Excel format but can be extended for other
        formats that support comparison features.
        """
        if format not in self._available_formats:
            raise ReportError(f"Format {format} not available for comparison reports")
        
        generator = self._generators[format]
        
        # Check if generator supports comparison reports
        if not hasattr(generator, 'generate_comparison_report'):
            raise ReportError(f"Format {format} does not support comparison reports")
        
        try:
            return generator.generate_comparison_report(analyses, output_path, **options)
        except Exception as e:
            raise ReportError(f"Failed to generate comparison report: {e}")
    
    def generate_executive_summary(self, analysis: Any, output_path: str,
                                 format: str = 'pdf', **options) -> bool:
        """
        Generate executive summary report.
        
        Args:
            analysis: Analysis result data
            output_path: Path to save summary report
            format: Format for summary report
            **options: Format-specific options
            
        Returns:
            True if successful
            
        Raises:
            ReportError: If summary generation fails
        """
        if format not in self._available_formats:
            raise ReportError(f"Format {format} not available for executive summaries")
        
        generator = self._generators[format]
        
        # Check if generator supports executive summaries
        if not hasattr(generator, 'generate_executive_summary'):
            raise ReportError(f"Format {format} does not support executive summaries")
        
        try:
            return generator.generate_executive_summary(analysis, output_path, **options)
        except Exception as e:
            raise ReportError(f"Failed to generate executive summary: {e}")
    
    def validate_format_requirements(self, format: str) -> Tuple[bool, List[str]]:
        """
        Validate requirements for specific format.
        
        Args:
            format: Format name to validate
            
        Returns:
            Tuple of (is_available, missing_dependencies)
            
        AI Context: Validates format availability and identifies missing
        dependencies. Useful for providing user feedback about format
        availability and installation requirements.
        """
        if format not in self._generators:
            return False, [f"Unknown format: {format}"]
        
        generator = self._generators[format]
        is_available = generator.dependencies_available
        
        if is_available:
            return True, []
        
        # Return format-specific dependency information
        dependency_info = {
            'excel': ['openpyxl'],
            'pdf': ['reportlab'],
            'word': ['python-docx'],
            'json': [],  # Always available
            'csv': []    # Always available
        }
        
        missing_deps = dependency_info.get(format, [])
        return False, missing_deps
    
    def _get_available_formats(self) -> List[str]:
        """Get list of formats with available dependencies."""
        available = []
        
        for format_name, generator in self._generators.items():
            if generator.dependencies_available:
                available.append(format_name)
        
        return available
    
    def _get_format_features(self, format_name: str, generator: BaseReportGenerator) -> List[str]:
        """Get special features available for format."""
        features = []
        
        # Check for special methods/capabilities
        if hasattr(generator, 'generate_comparison_report'):
            features.append('comparison_reports')
        
        if hasattr(generator, 'generate_executive_summary'):
            features.append('executive_summary')
        
        # Format-specific features
        if format_name == 'word' and hasattr(generator, 'track_changes_available'):
            if generator.track_changes_available:
                features.append('track_changes')
        
        if format_name == 'excel':
            features.extend(['professional_styling', 'multiple_worksheets'])
        
        if format_name == 'pdf':
            features.extend(['professional_layout', 'pagination'])
        
        if format_name == 'json':
            features.extend(['structured_data', 'api_friendly', 'programmatic_access'])
        
        if format_name == 'csv':
            features.extend(['tabular_data', 'spreadsheet_compatible'])
        
        return features
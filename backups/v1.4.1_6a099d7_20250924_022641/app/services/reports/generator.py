"""
Main Report Generator Service

Orchestrates multi-format report generation for contract analysis.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from .formatters.excel import ExcelReportFormatter
from .formatters.word import WordReportFormatter
from .formatters.pdf import PDFReportFormatter
from ..storage.file_manager import FileManager
from ...utils.logging.setup import get_logger

logger = get_logger(__name__)


class ReportGenerationError(Exception):
    """Exception raised when report generation fails"""
    pass


class ReportGenerator:
    """
    Main report generation service that coordinates multiple output formats.
    
    Supports:
    - Excel reports (.xlsx) with professional styling
    - Word documents (.docx) with track changes simulation
    - PDF reports with structured formatting
    - Windows COM Word integration for native track changes
    """
    
    def __init__(self, reports_dir: str = None, config: Dict[str, Any] = None):
        """
        Initialize report generator
        
        Args:
            reports_dir: Directory to store generated reports
            config: Configuration dictionary
        """
        self.config = config or {}
        self.reports_dir = Path(reports_dir) if reports_dir else Path("data/reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize formatters
        self.excel_formatter = ExcelReportFormatter()
        self.word_formatter = WordReportFormatter()
        self.pdf_formatter = PDFReportFormatter()
        
        # File manager for storage operations
        self.file_manager = FileManager(self.reports_dir)
        
        # Track generated reports
        self.generated_reports = []
        
        logger.info(f"Report generator initialized - Output directory: {self.reports_dir}")
    
    def generate_all_reports(
        self, 
        analysis_data: Dict[str, Any], 
        base_name: str,
        formats: List[str] = None
    ) -> Dict[str, str]:
        """
        Generate all requested report formats
        
        Args:
            analysis_data: Analysis results from contract comparison
            base_name: Base filename for generated reports
            formats: List of formats to generate ['excel', 'word', 'pdf', 'word_com']
            
        Returns:
            Dictionary mapping format names to generated file paths
            
        Raises:
            ReportGenerationError: If any critical report generation fails
        """
        if formats is None:
            formats = ['excel', 'word']  # Default formats
        
        logger.info(f"Generating reports for {base_name} - Formats: {formats}")
        
        generated_files = {}
        errors = []
        
        # Generate each requested format
        for format_name in formats:
            try:
                if format_name == 'excel':
                    file_path = self.generate_excel_report(analysis_data, base_name)
                    generated_files['excel'] = file_path
                    
                elif format_name == 'word':
                    file_path = self.generate_word_report(analysis_data, base_name)
                    generated_files['word'] = file_path
                    
                elif format_name == 'pdf':
                    file_path = self.generate_pdf_report(analysis_data, base_name)
                    generated_files['pdf'] = file_path
                    
                elif format_name == 'word_com':
                    file_path = self.generate_word_com_report(analysis_data, base_name)
                    if file_path:
                        generated_files['word_com'] = file_path
                    else:
                        errors.append(f"Word COM not available on this platform")
                        
                else:
                    errors.append(f"Unknown format: {format_name}")
                    
            except Exception as e:
                error_msg = f"Failed to generate {format_name} report: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Log results
        if generated_files:
            logger.info(f"Successfully generated {len(generated_files)} reports")
            self.generated_reports.extend(generated_files.values())
        
        if errors:
            logger.warning(f"Report generation errors: {errors}")
        
        return generated_files
    
    def generate_excel_report(self, analysis_data: Dict[str, Any], base_name: str) -> str:
        """
        Generate Excel changes table report
        
        Args:
            analysis_data: Analysis results
            base_name: Base filename
            
        Returns:
            Path to generated Excel file
        """
        try:
            output_path = self.reports_dir / f"{base_name}_changes_table.xlsx"
            
            # Use Excel formatter to generate the report
            self.excel_formatter.generate_changes_table(
                analysis_data=analysis_data,
                output_path=str(output_path)
            )
            
            logger.info(f"Excel report generated: {output_path.name}")
            return str(output_path)
            
        except Exception as e:
            raise ReportGenerationError(f"Excel report generation failed: {e}")
    
    def generate_word_report(self, analysis_data: Dict[str, Any], base_name: str) -> str:
        """
        Generate Word redlined document
        
        Args:
            analysis_data: Analysis results
            base_name: Base filename
            
        Returns:
            Path to generated Word file
        """
        try:
            output_path = self.reports_dir / f"{base_name}_redlined_document.docx"
            
            # Use Word formatter to generate the report
            self.word_formatter.generate_redlined_document(
                analysis_data=analysis_data,
                output_path=str(output_path)
            )
            
            logger.info(f"Word report generated: {output_path.name}")
            return str(output_path)
            
        except Exception as e:
            raise ReportGenerationError(f"Word report generation failed: {e}")
    
    def generate_pdf_report(self, analysis_data: Dict[str, Any], base_name: str) -> str:
        """
        Generate PDF summary report
        
        Args:
            analysis_data: Analysis results
            base_name: Base filename
            
        Returns:
            Path to generated PDF file
        """
        try:
            output_path = self.reports_dir / f"{base_name}_summary_report.pdf"
            
            # Use PDF formatter to generate the report
            self.pdf_formatter.generate_summary_report(
                analysis_data=analysis_data,
                output_path=str(output_path)
            )
            
            logger.info(f"PDF report generated: {output_path.name}")
            return str(output_path)
            
        except Exception as e:
            raise ReportGenerationError(f"PDF report generation failed: {e}")
    
    def generate_word_com_report(self, analysis_data: Dict[str, Any], base_name: str) -> Optional[str]:
        """
        Generate Word document with native track changes using COM (Windows only)
        
        Args:
            analysis_data: Analysis results
            base_name: Base filename
            
        Returns:
            Path to generated Word file or None if COM not available
        """
        try:
            output_path = self.reports_dir / f"{base_name}_word_com_redlined.docx"
            
            # Use Word formatter COM functionality
            result_path = self.word_formatter.generate_word_com_redlined(
                analysis_data=analysis_data,
                output_path=str(output_path)
            )
            
            if result_path:
                logger.info(f"Word COM report generated: {Path(result_path).name}")
                return result_path
            else:
                logger.warning("Word COM not available on this platform")
                return None
                
        except Exception as e:
            logger.error(f"Word COM report generation failed: {e}")
            return None
    
    def get_report_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get metadata for a generated report
        
        Args:
            file_path: Path to the report file
            
        Returns:
            Dictionary with report metadata
        """
        path = Path(file_path)
        
        if not path.exists():
            return {}
        
        return {
            'filename': path.name,
            'size_bytes': path.stat().st_size,
            'created': datetime.fromtimestamp(path.stat().st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            'format': path.suffix.lower(),
            'full_path': str(path.resolve())
        }
    
    def cleanup_old_reports(self, max_age_days: int = 30) -> int:
        """
        Clean up old report files
        
        Args:
            max_age_days: Maximum age of reports to keep
            
        Returns:
            Number of files cleaned up
        """
        return self.file_manager.cleanup_old_files(max_age_days)
    
    def list_reports(self) -> List[Dict[str, Any]]:
        """
        List all reports in the reports directory
        
        Returns:
            List of report metadata dictionaries
        """
        reports = []
        
        for file_path in self.reports_dir.glob("*.xlsx"):
            reports.append(self.get_report_metadata(str(file_path)))
        
        for file_path in self.reports_dir.glob("*.docx"):
            reports.append(self.get_report_metadata(str(file_path)))
            
        for file_path in self.reports_dir.glob("*.pdf"):
            reports.append(self.get_report_metadata(str(file_path)))
        
        # Sort by creation time (newest first)
        reports.sort(key=lambda x: x.get('created', ''), reverse=True)
        
        return reports


def create_report_generator(config: Dict[str, Any]) -> ReportGenerator:
    """
    Factory function to create a report generator
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured ReportGenerator instance
    """
    reports_dir = config.get('REPORTS_FOLDER', 'data/reports')
    return ReportGenerator(reports_dir=reports_dir, config=config)


__all__ = ['ReportGenerator', 'ReportGenerationError', 'create_report_generator']
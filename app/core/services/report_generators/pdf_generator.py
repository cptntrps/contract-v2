"""
PDF Report Generator - Domain Layer

Specialized generator for PDF reports with professional formatting.
Following architectural standards: single responsibility, comprehensive documentation.
"""

from datetime import datetime
from typing import Dict, Any, Optional

from .base_generator import BaseReportGenerator, ReportError
from ....utils.logging.setup import get_logger

# PDF handling with graceful fallback
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

logger = get_logger(__name__)


class PDFReportGenerator(BaseReportGenerator):
    """
    Specialized PDF report generator with professional formatting.
    
    Purpose: Generates PDF reports with professional layout, formatted tables,
    and comprehensive analysis content. Handles PDF-specific features like
    page breaks, styling, and document structure.
    
    AI Context: PDF-specific report generator using reportlab. When debugging
    PDF issues, check dependency availability first, then canvas/table creation.
    Provides paginated reports with proper formatting and professional styling.
    """
    
    @property
    def format_name(self) -> str:
        """Return format name for PDF reports."""
        return 'pdf'
    
    @property
    def file_extension(self) -> str:
        """Return file extension for PDF files."""
        return '.pdf'
    
    @property
    def dependencies_available(self) -> bool:
        """Check if reportlab is available."""
        return PDF_AVAILABLE
    
    def generate_report(self, analysis: Any, output_path: str,
                       include_summary: bool = True,
                       page_format: str = 'letter',
                       **options) -> bool:
        """
        Generate PDF report with formatted content and optional summary.
        
        Purpose: Creates a professional PDF report with proper pagination,
        formatted tables, and comprehensive analysis data. Uses reportlab
        for precise layout control and professional appearance.
        
        Args:
            analysis: Analysis result containing changes and metadata
            output_path: Path to save PDF file
            include_summary: Whether to include summary section
            page_format: Page format ('letter' or 'a4')
            **options: Additional PDF-specific options
            
        Returns:
            True if successful
            
        Raises:
            ReportError: If PDF generation fails or dependencies missing
            
        AI Context: Main PDF report generation method. Creates canvas-based
        PDF with multiple sections. For debugging, check canvas operations,
        text positioning, and page break logic.
        """
        # Validate dependencies and path
        self.validate_dependencies()
        normalized_path = self.validate_output_path(output_path)
        
        self.log_generation_start(normalized_path)
        
        try:
            # Set page size
            pagesize = A4 if page_format.lower() == 'a4' else letter
            
            # Create canvas
            c = canvas.Canvas(normalized_path, pagesize=pagesize)
            width, height = pagesize
            
            # Track current y position
            y_position = height - 50
            
            # Generate report sections
            y_position = self._add_title_section(c, analysis, width, y_position)
            y_position = self._add_metadata_section(c, analysis, width, y_position)
            
            if include_summary:
                y_position = self._add_summary_section(c, analysis, width, y_position)
            
            y_position = self._add_statistics_section(c, analysis, width, y_position)
            y_position = self._add_changes_section(c, analysis, width, y_position, height)
            
            # Save PDF
            c.save()
            
            self.log_generation_success(normalized_path)
            return True
            
        except Exception as e:
            self.log_generation_failure(normalized_path, e)
            raise ReportError(f"Failed to generate PDF report: {e}")
    
    def _add_title_section(self, canvas_obj: Any, analysis: Any, 
                          width: float, y_position: float) -> float:
        """
        Add title section to PDF.
        
        Args:
            canvas_obj: PDF canvas object
            analysis: Analysis result data
            width: Page width
            y_position: Current Y position
            
        Returns:
            Updated Y position
            
        AI Context: Creates title section with report header and branding.
        Uses professional typography and layout.
        """
        canvas_obj.setFont("Helvetica-Bold", 24)
        title_text = "Contract Analysis Report"
        text_width = canvas_obj.stringWidth(title_text)
        x_centered = (width - text_width) / 2
        canvas_obj.drawString(x_centered, y_position, title_text)
        
        # Add underline
        canvas_obj.line(50, y_position - 5, width - 50, y_position - 5)
        
        return y_position - 40
    
    def _add_metadata_section(self, canvas_obj: Any, analysis: Any,
                             width: float, y_position: float) -> float:
        """
        Add metadata section with analysis details.
        
        Args:
            canvas_obj: PDF canvas object
            analysis: Analysis result data
            width: Page width
            y_position: Current Y position
            
        Returns:
            Updated Y position
        """
        canvas_obj.setFont("Helvetica-Bold", 12)
        canvas_obj.drawString(50, y_position, "Analysis Details")
        y_position -= 20
        
        canvas_obj.setFont("Helvetica", 10)
        metadata_items = [
            f"Analysis ID: {getattr(analysis, 'analysis_id', 'N/A')}",
            f"Contract ID: {getattr(analysis, 'contract_id', 'N/A')}",
            f"Template ID: {getattr(analysis, 'template_id', 'N/A')}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Status: {getattr(analysis, 'status', 'N/A')}"
        ]
        
        for item in metadata_items:
            canvas_obj.drawString(70, y_position, item)
            y_position -= 15
        
        return y_position - 10
    
    def _add_summary_section(self, canvas_obj: Any, analysis: Any,
                           width: float, y_position: float) -> float:
        """
        Add AI analysis summary section.
        
        Args:
            canvas_obj: PDF canvas object
            analysis: Analysis result data
            width: Page width
            y_position: Current Y position
            
        Returns:
            Updated Y position
        """
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.drawString(50, y_position, "Executive Summary")
        y_position -= 25
        
        canvas_obj.setFont("Helvetica", 11)
        
        llm_analysis = getattr(analysis, 'llm_analysis', None)
        if llm_analysis and 'summary' in llm_analysis:
            summary_text = llm_analysis['summary']
        else:
            summary_text = "No AI analysis summary available for this contract analysis."
        
        # Wrap and display summary text
        wrapped_lines = self.wrap_text(summary_text, 80)
        for line in wrapped_lines:
            # Check if we need a new page
            if y_position < 100:
                canvas_obj.showPage()
                y_position = canvas_obj._pagesize[1] - 50
            
            canvas_obj.drawString(70, y_position, line)
            y_position -= 15
        
        return y_position - 20
    
    def _add_statistics_section(self, canvas_obj: Any, analysis: Any,
                              width: float, y_position: float) -> float:
        """
        Add statistics section with change counts.
        
        Args:
            canvas_obj: PDF canvas object
            analysis: Analysis result data
            width: Page width
            y_position: Current Y position
            
        Returns:
            Updated Y position
        """
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.drawString(50, y_position, "Change Statistics")
        y_position -= 25
        
        canvas_obj.setFont("Helvetica", 11)
        
        statistics = getattr(analysis, 'statistics', {})
        for key, value in statistics.items():
            display_key = key.replace('_', ' ').title()
            canvas_obj.drawString(70, y_position, f"{display_key}: {value}")
            y_position -= 18
        
        return y_position - 20
    
    def _add_changes_section(self, canvas_obj: Any, analysis: Any, width: float,
                           y_position: float, page_height: float) -> float:
        """
        Add detailed changes section.
        
        Args:
            canvas_obj: PDF canvas object
            analysis: Analysis result data
            width: Page width
            y_position: Current Y position
            page_height: Total page height
            
        Returns:
            Updated Y position
        """
        # Check if we need a new page for changes section
        if y_position < 200:
            canvas_obj.showPage()
            y_position = page_height - 50
        
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.drawString(50, y_position, "Detailed Changes")
        y_position -= 30
        
        # Format changes for display
        changes = getattr(analysis, 'changes', [])
        if not changes:
            canvas_obj.setFont("Helvetica", 11)
            canvas_obj.drawString(70, y_position, "No changes detected in this analysis.")
            return y_position - 20
        
        formatted_changes = self.format_changes_for_display(changes)
        
        canvas_obj.setFont("Helvetica", 10)
        change_count = 0
        
        for change in formatted_changes:
            # Check if we need a new page
            if y_position < 120:
                canvas_obj.showPage()
                y_position = page_height - 50
            
            change_count += 1
            
            # Change header
            canvas_obj.setFont("Helvetica-Bold", 10)
            canvas_obj.drawString(50, y_position, f"Change #{change_count}: {change['operation'].title()}")
            y_position -= 15
            
            canvas_obj.setFont("Helvetica", 9)
            
            # Change details
            if change['original_text']:
                canvas_obj.drawString(70, y_position, f"Original: {change['original_text'][:100]}...")
                y_position -= 12
            
            if change['modified_text']:
                canvas_obj.drawString(70, y_position, f"Modified: {change['modified_text'][:100]}...")
                y_position -= 12
            
            if change['context']:
                context_lines = self.wrap_text(f"Context: {change['context']}", 70)
                for line in context_lines[:2]:  # Limit context to 2 lines
                    canvas_obj.drawString(70, y_position, line)
                    y_position -= 12
            
            canvas_obj.drawString(70, y_position, f"Position: Line {change['position']}")
            y_position -= 20
        
        return y_position
    
    def generate_executive_summary(self, analysis: Any, output_path: str,
                                 **options) -> bool:
        """
        Generate executive summary PDF report.
        
        Args:
            analysis: Analysis result data
            output_path: Path to save PDF file
            **options: Additional options
            
        Returns:
            True if successful
            
        Raises:
            ReportError: If generation fails
            
        AI Context: Specialized method for creating executive summary reports.
        Focuses on high-level insights and key findings for management review.
        """
        self.validate_dependencies()
        normalized_path = self.validate_output_path(output_path)
        
        try:
            c = canvas.Canvas(normalized_path, pagesize=letter)
            width, height = letter
            
            # Executive summary title
            c.setFont("Helvetica-Bold", 28)
            title_text = "Executive Summary"
            text_width = c.stringWidth(title_text)
            x_centered = (width - text_width) / 2
            c.drawString(x_centered, height - 100, title_text)
            
            y_position = height - 150
            
            # Contract overview
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, y_position, "Contract Analysis Overview")
            y_position -= 30
            
            c.setFont("Helvetica", 12)
            overview_items = [
                f"Analysis Date: {datetime.now().strftime('%B %d, %Y')}",
                f"Contract ID: {getattr(analysis, 'contract_id', 'N/A')}",
                f"Analysis Status: {getattr(analysis, 'status', 'N/A')}"
            ]
            
            for item in overview_items:
                c.drawString(70, y_position, item)
                y_position -= 20
            
            # Key metrics
            y_position -= 20
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, y_position, "Key Findings")
            y_position -= 30
            
            statistics = getattr(analysis, 'statistics', {})
            total_changes = statistics.get('total_changes', 0)
            
            c.setFont("Helvetica", 12)
            c.drawString(70, y_position, f"Total Changes Identified: {total_changes}")
            y_position -= 25
            
            # Risk assessment if available
            llm_analysis = getattr(analysis, 'llm_analysis', None)
            if llm_analysis and 'risk_assessment' in llm_analysis:
                risk_level = llm_analysis['risk_assessment'].upper()
                c.drawString(70, y_position, f"Risk Level: {risk_level}")
                y_position -= 25
            
            # Summary text
            if llm_analysis and 'summary' in llm_analysis:
                y_position -= 20
                c.setFont("Helvetica-Bold", 14)
                c.drawString(50, y_position, "Analysis Summary")
                y_position -= 25
                
                c.setFont("Helvetica", 11)
                summary_lines = self.wrap_text(llm_analysis['summary'], 70)
                
                for line in summary_lines:
                    if y_position < 100:
                        c.showPage()
                        y_position = height - 50
                    
                    c.drawString(70, y_position, line)
                    y_position -= 15
            
            c.save()
            self.log_generation_success(normalized_path)
            return True
            
        except Exception as e:
            self.log_generation_failure(normalized_path, e)
            raise ReportError(f"Failed to generate executive summary PDF: {e}")
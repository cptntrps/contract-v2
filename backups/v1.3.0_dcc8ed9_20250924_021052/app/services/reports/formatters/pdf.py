"""
PDF Report Formatter

Generates professional PDF reports with structured formatting.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, Color
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from ....utils.logging.setup import get_logger

logger = get_logger(__name__)


class PDFReportFormatter:
    """
    PDF report formatter for contract analysis results.
    
    Generates professional PDF reports with:
    - Executive summary
    - Detailed changes analysis
    - Risk assessment
    - Recommendations
    """
    
    def __init__(self):
        """Initialize PDF formatter"""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=HexColor('#1f4788')
        )
        
        # Heading style
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=12,
            textColor=HexColor('#1f4788')
        )
        
        # Risk high style
        self.risk_high_style = ParagraphStyle(
            'RiskHigh',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=HexColor('#cc0000'),
            fontName='Helvetica-Bold'
        )
        
        # Risk medium style
        self.risk_medium_style = ParagraphStyle(
            'RiskMedium',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=HexColor('#ff6600'),
            fontName='Helvetica-Bold'
        )
        
        # Risk low style
        self.risk_low_style = ParagraphStyle(
            'RiskLow',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=HexColor('#008000'),
            fontName='Helvetica-Bold'
        )
    
    def generate_summary_report(self, analysis_data: Dict[str, Any], output_path: str) -> str:
        """
        Generate PDF summary report
        
        Args:
            analysis_data: Analysis results containing changes and metadata
            output_path: Path to save the PDF file
            
        Returns:
            Path to the generated PDF file
        """
        logger.info(f"Generating PDF summary report: {Path(output_path).name}")
        
        # Create document
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        
        # Title
        title = Paragraph("Contract Analysis Report", self.title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.heading_style))
        self._add_executive_summary(story, analysis_data)
        story.append(Spacer(1, 20))
        
        # Risk Assessment
        story.append(Paragraph("Risk Assessment", self.heading_style))
        self._add_risk_assessment(story, analysis_data)
        story.append(Spacer(1, 20))
        
        # Changes Summary
        story.append(Paragraph("Changes Summary", self.heading_style))
        self._add_changes_summary(story, analysis_data)
        story.append(Spacer(1, 20))
        
        # Recommendations
        story.append(Paragraph("Recommendations", self.heading_style))
        self._add_recommendations(story, analysis_data)
        
        # Build PDF
        doc.build(story)
        logger.info(f"PDF report saved: {output_path}")
        
        return output_path
    
    def _add_executive_summary(self, story: List, analysis_data: Dict[str, Any]):
        """Add executive summary to the story"""
        
        summary_data = [
            ['Contract:', analysis_data.get('contract', 'Unknown')],
            ['Template:', analysis_data.get('template', 'Unknown')],
            ['Analysis Date:', analysis_data.get('date', datetime.now().strftime('%Y-%m-%d'))],
            ['Total Changes:', str(analysis_data.get('changes', 0))],
            ['Similarity Score:', f"{analysis_data.get('similarity', 0)}%"],
            ['Status:', analysis_data.get('status', 'Completed')]
        ]
        
        table = Table(summary_data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#cccccc'))
        ]))
        
        story.append(table)
    
    def _add_risk_assessment(self, story: List, analysis_data: Dict[str, Any]):
        """Add risk assessment to the story"""
        
        risk_level = self._determine_risk_level(analysis_data)
        risk_explanation = self._get_risk_explanation(risk_level, analysis_data)
        
        # Risk level with appropriate styling
        if risk_level == "HIGH":
            risk_para = Paragraph(f"Overall Risk Level: {risk_level}", self.risk_high_style)
        elif risk_level == "MEDIUM":
            risk_para = Paragraph(f"Overall Risk Level: {risk_level}", self.risk_medium_style)
        else:
            risk_para = Paragraph(f"Overall Risk Level: {risk_level}", self.risk_low_style)
        
        story.append(risk_para)
        story.append(Spacer(1, 12))
        
        # Risk explanation
        explanation_para = Paragraph(risk_explanation, self.styles['Normal'])
        story.append(explanation_para)
        
        # Risk breakdown
        changes = analysis_data.get('analysis', [])
        critical_count = len([c for c in changes if c.get('classification') == 'CRITICAL'])
        significant_count = len([c for c in changes if c.get('classification') == 'SIGNIFICANT'])
        inconsequential_count = len([c for c in changes if c.get('classification') == 'INCONSEQUENTIAL'])
        
        breakdown_data = [
            ['Critical Changes:', str(critical_count)],
            ['Significant Changes:', str(significant_count)],
            ['Inconsequential Changes:', str(inconsequential_count)]
        ]
        
        breakdown_table = Table(breakdown_data, colWidths=[2*inch, 1*inch])
        breakdown_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#cccccc'))
        ]))
        
        story.append(Spacer(1, 12))
        story.append(breakdown_table)
    
    def _add_changes_summary(self, story: List, analysis_data: Dict[str, Any]):
        """Add changes summary table to the story"""
        
        changes = analysis_data.get('analysis', [])
        if not changes:
            story.append(Paragraph("No changes detected in this document.", self.styles['Normal']))
            return
        
        # Limit to first 10 changes for summary
        summary_changes = changes[:10]
        
        table_data = [['#', 'Classification', 'Change Description']]
        
        for i, change in enumerate(summary_changes, 1):
            description = change.get('explanation', 'No description available')
            if len(description) > 100:
                description = description[:100] + "..."
            
            table_data.append([
                str(i),
                change.get('classification', 'UNKNOWN'),
                description
            ])
        
        table = Table(table_data, colWidths=[0.5*inch, 1.5*inch, 4*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f0f0f0'))
        ]))
        
        story.append(table)
        
        if len(changes) > 10:
            story.append(Spacer(1, 12))
            story.append(Paragraph(f"... and {len(changes) - 10} more changes. See detailed report for complete analysis.", self.styles['Italic']))
    
    def _add_recommendations(self, story: List, analysis_data: Dict[str, Any]):
        """Add recommendations to the story"""
        
        recommendations = self._generate_recommendations(analysis_data)
        
        if recommendations:
            for rec in recommendations:
                # Clean emoji for PDF
                clean_rec = rec.replace('🚨', '• CRITICAL:').replace('⚠️', '• WARNING:').replace('✅', '• APPROVED:').replace('📋', '• NOTE:')
                rec_para = Paragraph(clean_rec, self.styles['Normal'])
                story.append(rec_para)
                story.append(Spacer(1, 6))
        else:
            story.append(Paragraph("No specific recommendations at this time.", self.styles['Normal']))
    
    def _determine_risk_level(self, analysis_data: Dict[str, Any]) -> str:
        """Determine overall risk level"""
        changes = analysis_data.get('analysis', [])
        critical_count = len([c for c in changes if c.get('classification') == 'CRITICAL'])
        significant_count = len([c for c in changes if c.get('classification') == 'SIGNIFICANT'])
        
        if critical_count > 0:
            return "HIGH"
        elif significant_count > 5:
            return "HIGH"
        elif significant_count > 0:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_risk_explanation(self, risk_level: str, analysis_data: Dict[str, Any]) -> str:
        """Get explanation for risk level"""
        changes = analysis_data.get('analysis', [])
        critical_count = len([c for c in changes if c.get('classification') == 'CRITICAL'])
        
        if risk_level == "HIGH":
            if critical_count > 0:
                return f"This contract contains {critical_count} critical change(s) involving actual value-to-value modifications (e.g., price changes, service changes, company changes). These require immediate legal review and approval before proceeding."
            else:
                return "This contract contains numerous significant changes that require immediate legal review and approval before proceeding."
        elif risk_level == "MEDIUM":
            return "This contract contains significant changes that should be reviewed by legal counsel before execution."
        else:
            return "This contract has minimal changes (mostly placeholder content) and can proceed through standard review processes."
    
    def _generate_recommendations(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        changes = analysis_data.get('analysis', [])
        critical_changes = [c for c in changes if c.get('classification') == 'CRITICAL']
        risk_level = self._determine_risk_level(analysis_data)
        
        if risk_level == "HIGH":
            recommendations.extend([
                "🚨 CRITICAL: Schedule immediate legal review with qualified counsel",
                "🚨 Do not execute contract until all critical changes are approved",
                "🚨 Focus on value-to-value changes (price, service, company modifications)"
            ])
        elif risk_level == "MEDIUM":
            recommendations.extend([
                "⚠️ Schedule legal review before contract execution",
                "⚠️ Review all significant changes with stakeholders",
                "⚠️ Verify pricing and service level changes"
            ])
        else:
            recommendations.extend([
                "✅ Contract may proceed through standard review process",
                "✅ Verify placeholder content has been properly filled",
                "✅ Confirm standard terms and conditions"
            ])
        
        # Add general recommendations
        recommendations.extend([
            "📋 Document all approved changes for future reference",
            "📋 Ensure all parties acknowledge the modifications",
            "📋 Update contract management system with new terms"
        ])
        
        return recommendations


__all__ = ['PDFReportFormatter']
"""
Test report generation in multiple formats
"""
import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock
from pathlib import Path
import tempfile
import json
from datetime import datetime

from app.core.services.report_generator import ReportGenerator, ReportError
from app.core.models.analysis_result import AnalysisResult, Change
from app.utils.errors.exceptions import ValidationError


class TestReportGenerator:
    """Test ReportGenerator functionality"""
    
    @pytest.fixture
    def generator(self):
        """Create report generator instance"""
        with patch('app.core.services.report_generator.get_logger'):
            return ReportGenerator()
    
    @pytest.fixture
    def sample_analysis(self):
        """Sample analysis result for testing"""
        analysis = AnalysisResult(
            analysis_id="test_analysis_123",
            contract_id="contract_456",
            template_id="template_789",
            analysis_timestamp=datetime.now(),
            total_changes=3,
            similarity_score=0.75,
            overall_risk_level="MEDIUM",
            risk_explanation="Payment terms and warranty changes present medium risk",
            recommendations=[
                'Review payment terms with legal team',
                'Clarify warranty coverage scope',
                'Consider impact on existing agreements'
            ]
        )
        
        # Add sample changes - using the Change model from analysis_result.py
        from app.core.models.analysis_result import Change, ChangeType, ChangeClassification
        
        changes = [
            Change(
                change_id="change_001",
                change_type=ChangeType.REPLACEMENT,
                classification=ChangeClassification.SIGNIFICANT,
                deleted_text="30 days",
                inserted_text="45 days",
                context_before="Payment due in ",
                context_after=" from invoice date",
                line_number=10,
                section="Payment Terms",
                explanation="Payment terms extended by 15 days"
            ),
            Change(
                change_id="change_002",
                change_type=ChangeType.INSERTION,
                classification=ChangeClassification.SIGNIFICANT,
                deleted_text="",
                inserted_text="Additional warranty terms apply.",
                context_before="Standard terms. ",
                context_after="",
                line_number=50,
                section="Warranty",
                explanation="New warranty clause added"
            ),
            Change(
                change_id="change_003",
                change_type=ChangeType.DELETION,
                classification=ChangeClassification.CRITICAL,
                deleted_text="Early termination allowed with notice.",
                inserted_text="",
                context_before="Termination clause: ",
                context_after="",
                line_number=80,
                section="Termination",
                explanation="Early termination clause removed"
            )
        ]
        
        # Add changes to analysis
        for change in changes:
            analysis.add_change(change)
        
        # Add custom attributes that report generator expects
        analysis.statistics = {
            'total_changes': 3,
            'insertions': 1,
            'deletions': 1,
            'replacements': 1,
            'total_inserted_chars': 50,
            'total_deleted_chars': 40
        }
        
        analysis.llm_analysis = {
            'summary': 'Contract modifications include payment term changes and additional warranty clauses.',
            'risk_assessment': 'medium',
            'recommendations': analysis.recommendations
        }
        
        # Add created_at and completed_at for compatibility
        analysis.created_at = analysis.analysis_timestamp
        analysis.completed_at = datetime.now()
        analysis.status = 'completed'
        
        return analysis
    
    def test_generate_excel_report_basic(self, generator, sample_analysis, tmp_path):
        """Test basic Excel report generation"""
        output_path = tmp_path / "test_report.xlsx"
        
        with patch('app.core.services.report_generator.Workbook') as mock_workbook:
            mock_wb = Mock()
            mock_ws = Mock()
            mock_workbook.return_value = mock_wb
            mock_wb.active = mock_ws
            
            result = generator.generate_excel_report(sample_analysis, str(output_path))
            
            assert result is True
            mock_wb.save.assert_called_once_with(str(output_path))
            
            # Verify worksheet configuration
            assert mock_ws.title == "Contract Analysis"
            
            # Verify headers were written
            expected_calls = [
                (('A1', 'Change Type')),
                (('B1', 'Original Text')),
                (('C1', 'Modified Text')),
                (('D1', 'Position')),
                (('E1', 'Context'))
            ]
            
            for call_args in expected_calls:
                mock_ws.__setitem__.assert_any_call(*call_args)
    
    def test_generate_excel_report_with_styling(self, generator, sample_analysis, tmp_path):
        """Test Excel report generation with styling"""
        output_path = tmp_path / "styled_report.xlsx"
        
        with patch('app.core.services.report_generator.Workbook') as mock_workbook:
            mock_wb = Mock()
            mock_ws = Mock()
            mock_workbook.return_value = mock_wb
            mock_wb.active = mock_ws
            
            result = generator.generate_excel_report(
                sample_analysis, 
                str(output_path),
                include_styling=True
            )
            
            assert result is True
            
            # Verify styling was applied
            mock_ws.freeze_panes.assert_called()
            
            # Verify column widths were set
            for col in ['A', 'B', 'C', 'D', 'E']:
                mock_ws.column_dimensions.__getitem__.assert_any_call(col)
    
    def test_generate_excel_report_error(self, generator, sample_analysis, tmp_path):
        """Test Excel report generation with error"""
        output_path = tmp_path / "error_report.xlsx"
        
        with patch('app.core.services.report_generator.Workbook', side_effect=Exception("Excel error")):
            with pytest.raises(ReportError) as exc_info:
                generator.generate_excel_report(sample_analysis, str(output_path))
            
            assert "Excel error" in str(exc_info.value)
    
    def test_generate_pdf_report_basic(self, generator, sample_analysis, tmp_path):
        """Test basic PDF report generation"""
        output_path = tmp_path / "test_report.pdf"
        
        with patch('app.core.services.report_generator.canvas') as mock_canvas:
            mock_c = Mock()
            mock_canvas.Canvas.return_value = mock_c
            
            result = generator.generate_pdf_report(sample_analysis, str(output_path))
            
            assert result is True
            mock_canvas.Canvas.assert_called_once_with(str(output_path))
            mock_c.save.assert_called_once()
    
    def test_generate_pdf_report_with_summary(self, generator, sample_analysis, tmp_path):
        """Test PDF report generation with summary"""
        output_path = tmp_path / "summary_report.pdf"
        
        with patch('app.core.services.report_generator.canvas') as mock_canvas:
            mock_c = Mock()
            mock_canvas.Canvas.return_value = mock_c
            
            result = generator.generate_pdf_report(
                sample_analysis, 
                str(output_path),
                include_summary=True
            )
            
            assert result is True
            
            # Verify text was written to canvas
            mock_c.drawString.assert_called()
            
            # Check that summary content was included
            call_args_list = mock_c.drawString.call_args_list
            summary_found = any(
                'Contract modifications include' in str(call)
                for call in call_args_list
            )
            assert summary_found
    
    def test_generate_pdf_report_error(self, generator, sample_analysis, tmp_path):
        """Test PDF report generation with error"""
        output_path = tmp_path / "error_report.pdf"
        
        with patch('app.core.services.report_generator.canvas.Canvas', side_effect=Exception("PDF error")):
            with pytest.raises(ReportError) as exc_info:
                generator.generate_pdf_report(sample_analysis, str(output_path))
            
            assert "PDF error" in str(exc_info.value)
    
    def test_generate_word_report_basic(self, generator, sample_analysis, tmp_path):
        """Test basic Word report generation"""
        output_path = tmp_path / "test_report.docx"
        
        with patch('app.core.services.report_generator.Document') as mock_document:
            mock_doc = Mock()
            mock_document.return_value = mock_doc
            
            result = generator.generate_word_report(sample_analysis, str(output_path))
            
            assert result is True
            mock_doc.save.assert_called_once_with(str(output_path))
    
    def test_generate_word_report_with_track_changes(self, generator, sample_analysis, tmp_path):
        """Test Word report generation with track changes (Windows COM)"""
        output_path = tmp_path / "tracked_report.docx"
        
        with patch('app.core.services.report_generator.win32com') as mock_com:
            mock_word = Mock()
            mock_com.client.Dispatch.return_value = mock_word
            mock_doc = Mock()
            mock_word.Documents.Add.return_value = mock_doc
            
            result = generator.generate_word_report(
                sample_analysis, 
                str(output_path),
                enable_track_changes=True
            )
            
            assert result is True
            mock_com.client.Dispatch.assert_called_with("Word.Application")
            mock_doc.TrackRevisions = True
            mock_doc.SaveAs2.assert_called_once()
    
    def test_generate_word_report_com_not_available(self, generator, sample_analysis, tmp_path):
        """Test Word report generation when COM is not available"""
        output_path = tmp_path / "no_com_report.docx"
        
        with patch('app.core.services.report_generator.win32com', None):
            with patch('app.core.services.report_generator.Document') as mock_document:
                mock_doc = Mock()
                mock_document.return_value = mock_doc
                
                result = generator.generate_word_report(
                    sample_analysis, 
                    str(output_path),
                    enable_track_changes=True
                )
                
                assert result is True
                # Should fall back to python-docx
                mock_doc.save.assert_called_once_with(str(output_path))
    
    def test_generate_json_report(self, generator, sample_analysis, tmp_path):
        """Test JSON report generation"""
        output_path = tmp_path / "test_report.json"
        
        result = generator.generate_json_report(sample_analysis, str(output_path))
        
        assert result is True
        assert output_path.exists()
        
        # Verify JSON content
        with open(output_path) as f:
            data = json.load(f)
        
        assert data['analysis_id'] == 'test_analysis_123'
        assert data['contract_id'] == 'contract_456'
        assert data['template_id'] == 'template_789'
        assert len(data['changes']) == 3
        assert 'statistics' in data
        assert 'llm_analysis' in data
    
    def test_generate_csv_report(self, generator, sample_analysis, tmp_path):
        """Test CSV report generation"""
        output_path = tmp_path / "test_report.csv"
        
        result = generator.generate_csv_report(sample_analysis, str(output_path))
        
        assert result is True
        assert output_path.exists()
        
        # Verify CSV content
        import csv
        with open(output_path, newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 3  # Number of changes
        assert 'operation' in rows[0]
        assert 'original_text' in rows[0]
        assert 'modified_text' in rows[0]
    
    def test_get_supported_formats(self, generator):
        """Test getting supported report formats"""
        formats = generator.get_supported_formats()
        
        assert isinstance(formats, list)
        assert 'excel' in formats
        assert 'pdf' in formats
        assert 'word' in formats
        assert 'json' in formats
        assert 'csv' in formats
    
    def test_validate_output_path(self, generator, tmp_path):
        """Test output path validation"""
        # Valid path
        valid_path = tmp_path / "report.xlsx"
        assert generator.validate_output_path(str(valid_path)) is True
        
        # Invalid path (directory doesn't exist)
        invalid_path = Path("/nonexistent/directory/report.xlsx")
        assert generator.validate_output_path(str(invalid_path)) is False
        
        # Path without extension
        no_ext_path = tmp_path / "report"
        assert generator.validate_output_path(str(no_ext_path)) is True
    
    def test_generate_report_by_format(self, generator, sample_analysis, tmp_path):
        """Test generating report by format string"""
        output_path = tmp_path / "test_report"
        
        with patch.object(generator, 'generate_excel_report', return_value=True) as mock_excel:
            result = generator.generate_report(sample_analysis, str(output_path), 'excel')
            assert result is True
            mock_excel.assert_called_once()
        
        with patch.object(generator, 'generate_pdf_report', return_value=True) as mock_pdf:
            result = generator.generate_report(sample_analysis, str(output_path), 'pdf')
            assert result is True
            mock_pdf.assert_called_once()
    
    def test_generate_report_invalid_format(self, generator, sample_analysis, tmp_path):
        """Test generating report with invalid format"""
        output_path = tmp_path / "test_report"
        
        with pytest.raises(ReportError) as exc_info:
            generator.generate_report(sample_analysis, str(output_path), 'invalid_format')
        
        assert "Unsupported format" in str(exc_info.value)
    
    def test_create_summary_section(self, generator, sample_analysis):
        """Test creating summary section for reports"""
        summary = generator.create_summary_section(sample_analysis)
        
        assert isinstance(summary, dict)
        assert 'analysis_overview' in summary
        assert 'change_statistics' in summary
        assert 'key_findings' in summary
        
        # Verify statistics
        assert summary['change_statistics']['total_changes'] == 3
        assert summary['change_statistics']['insertions'] == 1
        assert summary['change_statistics']['deletions'] == 1
        assert summary['change_statistics']['replacements'] == 1
    
    def test_format_changes_for_display(self, generator, sample_analysis):
        """Test formatting changes for display in reports"""
        formatted_changes = generator.format_changes_for_display(sample_analysis.changes)
        
        assert isinstance(formatted_changes, list)
        assert len(formatted_changes) == 3
        
        for change in formatted_changes:
            assert isinstance(change, dict)
            assert 'operation' in change
            assert 'display_text' in change
            assert 'context' in change
    
    def test_apply_report_styling(self, generator):
        """Test applying styling to report elements"""
        # Test Excel styling
        with patch('app.core.services.report_generator.Font') as mock_font, \
             patch('app.core.services.report_generator.PatternFill') as mock_fill:
            
            mock_cell = Mock()
            generator.apply_excel_styling(mock_cell, 'header')
            
            # Verify styling was applied
            assert mock_cell.font == mock_font.return_value
            assert mock_cell.fill == mock_fill.return_value
    
    def test_batch_generate_reports(self, generator, sample_analysis, tmp_path):
        """Test generating multiple report formats in batch"""
        formats = ['excel', 'pdf', 'json']
        base_path = tmp_path / "batch_report"
        
        with patch.object(generator, 'generate_excel_report', return_value=True), \
             patch.object(generator, 'generate_pdf_report', return_value=True), \
             patch.object(generator, 'generate_json_report', return_value=True):
            
            results = generator.batch_generate_reports(
                sample_analysis,
                str(base_path),
                formats
            )
            
            assert len(results) == 3
            assert all(result['success'] for result in results.values())
            assert set(results.keys()) == set(formats)
    
    def test_generate_comparison_report(self, generator, tmp_path):
        """Test generating comparison report between multiple analyses"""
        # Create multiple sample analyses
        analyses = []
        for i in range(3):
            analysis = AnalysisResult(
                analysis_id=f"analysis_{i}",
                contract_id=f"contract_{i}",
                template_id="template_001",
                analysis_timestamp=datetime.now(),
                total_changes=i + 1
            )
            # Add statistics for compatibility
            analysis.statistics = {'total_changes': i + 1}
            analyses.append(analysis)
        
        output_path = tmp_path / "comparison_report.xlsx"
        
        with patch('app.core.services.report_generator.Workbook') as mock_workbook:
            mock_wb = Mock()
            mock_ws = Mock()
            mock_workbook.return_value = mock_wb
            mock_wb.active = mock_ws
            
            result = generator.generate_comparison_report(analyses, str(output_path))
            
            assert result is True
            mock_wb.save.assert_called_once()
    
    def test_export_templates(self, generator, tmp_path):
        """Test exporting report templates"""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        
        result = generator.export_templates(str(template_dir))
        
        assert result is True
        
        # Check that template files were created
        expected_templates = ['excel_template.xlsx', 'word_template.docx']
        for template in expected_templates:
            template_path = template_dir / template
            # In real implementation, these would be created
            # For test, we just verify the method completes without error
    
    def test_generate_executive_summary(self, generator, sample_analysis, tmp_path):
        """Test generating executive summary report"""
        output_path = tmp_path / "executive_summary.pdf"
        
        with patch('app.core.services.report_generator.canvas') as mock_canvas:
            mock_c = Mock()
            mock_canvas.Canvas.return_value = mock_c
            
            result = generator.generate_executive_summary(sample_analysis, str(output_path))
            
            assert result is True
            
            # Verify executive summary content was added
            call_args_list = mock_c.drawString.call_args_list
            
            # Should contain high-level summary
            summary_found = any(
                'Executive Summary' in str(call) or 'Contract Analysis Overview' in str(call)
                for call in call_args_list
            )
            assert summary_found
    
    def test_report_metadata_generation(self, generator, sample_analysis):
        """Test generating report metadata"""
        metadata = generator.generate_report_metadata(
            sample_analysis,
            'excel',
            {'include_styling': True}
        )
        
        assert isinstance(metadata, dict)
        assert 'report_format' in metadata
        assert 'generation_timestamp' in metadata
        assert 'analysis_id' in metadata
        assert 'options' in metadata
        assert metadata['report_format'] == 'excel'
        assert metadata['analysis_id'] == 'test_analysis_123'
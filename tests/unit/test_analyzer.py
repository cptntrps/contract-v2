"""
Test main ContractAnalyzer orchestration
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
import asyncio

from app.core.services.analyzer import ContractAnalyzer, ContractAnalysisError as AnalysisError
from app.core.models.analysis_result import AnalysisResult, Change
from app.core.models.contract import Contract
from app.utils.errors.exceptions import ValidationError, NotFoundError, LLMError


class TestContractAnalyzer:
    """Test suite for ContractAnalyzer class"""

    def test_init(self):
        """Test analyzer initialization"""
        config = {
            'llm_settings': {
                'provider': 'openai',
                'api_key': 'test-key'
            }
        }
        analyzer = ContractAnalyzer(config)
        assert analyzer is not None
        assert analyzer.config == config

    def test_extract_text_from_docx_success(self, analyzer, test_docx_file):
        """Test successful text extraction from DOCX file"""
        text = analyzer.extract_text_from_docx(str(test_docx_file))
        assert isinstance(text, str)
        assert len(text) > 0
        assert 'Test Contract' in text

    def test_extract_text_from_docx_file_not_found(self, analyzer):
        """Test text extraction with non-existent file"""
        text = analyzer.extract_text_from_docx('nonexistent.docx')
        assert text == ""

    def test_find_changes(self, analyzer, sample_template_text, sample_contract_text):
        """Test change detection between template and contract"""
        changes = analyzer.find_changes(sample_template_text, sample_contract_text)
        assert isinstance(changes, list)
        assert len(changes) > 0
        
        # Check that changes contain delete/insert operations
        operations = [change[0] for change in changes]
        assert 'delete' in operations
        assert 'insert' in operations

    def test_find_changes_identical_texts(self, analyzer):
        """Test change detection with identical texts"""
        text = "This is identical text"
        changes = analyzer.find_changes(text, text)
        assert isinstance(changes, list)
        assert len(changes) == 0

    def test_calculate_similarity_identical(self, analyzer):
        """Test similarity calculation with identical texts"""
        text = "This is identical text"
        similarity = analyzer.calculate_similarity(text, text)
        assert similarity == 1.0

    def test_calculate_similarity_different(self, analyzer):
        """Test similarity calculation with different texts"""
        text1 = "This is the original text"
        text2 = "This is completely different content"
        similarity = analyzer.calculate_similarity(text1, text2)
        assert 0.0 <= similarity <= 1.0
        assert similarity < 1.0

    def test_calculate_similarity_similar(self, analyzer):
        """Test similarity calculation with similar texts"""
        text1 = "This is the original text"
        text2 = "This is the original content"
        similarity = analyzer.calculate_similarity(text1, text2)
        assert 0.5 <= similarity <= 1.0

    def test_create_commented_docx_success(self, analyzer, test_docx_file):
        """Test successful creation of commented document"""
        analysis_results = [
            {
                'classification': 'SIGNIFICANT',
                'explanation': 'Test change explanation',
                'deleted_text': 'original text',
                'inserted_text': 'new text'
            }
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            output_path = tmp.name
        
        try:
            result = analyzer.create_commented_docx(
                str(test_docx_file), 
                analysis_results, 
                output_path
            )
            assert result is True
            assert os.path.exists(output_path)
            
            # Verify the document was created properly
            doc = Document(output_path)
            text = '\n'.join([p.text for p in doc.paragraphs])
            assert 'Contract Analysis Summary' in text
            assert 'Test change explanation' in text
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_create_commented_docx_file_not_found(self, analyzer):
        """Test commented document creation with non-existent input file"""
        analysis_results = [{'classification': 'SIGNIFICANT'}]
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            output_path = tmp.name
        
        try:
            result = analyzer.create_commented_docx(
                'nonexistent.docx', 
                analysis_results, 
                output_path
            )
            assert result is False
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_save_analysis_metadata_success(self, analyzer):
        """Test successful saving of analysis metadata"""
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_results = [
                {
                    'classification': 'SIGNIFICANT',
                    'explanation': 'Test analysis'
                }
            ]
            
            metadata_path = analyzer.save_analysis_metadata(
                'test_contract.docx',
                'test_template.docx',
                analysis_results,
                temp_dir
            )
            
            assert metadata_path is not None
            assert os.path.exists(metadata_path)
            assert metadata_path.endswith('_analysis.json')
            
            # Verify metadata content
            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            assert metadata['uploaded_filename'] == 'test_contract.docx'
            assert metadata['selected_template'] == 'test_template.docx'
            assert metadata['total_changes'] == 1
            assert metadata['significant_changes_count'] == 1
            assert len(metadata['analysis_results']) == 1


class TestAnalyzerFunctions:
    """Test suite for analyzer module functions"""

    def test_extract_text_from_docx_function(self, test_docx_file):
        """Test extract_text_from_docx function"""
        text = extract_text_from_docx(str(test_docx_file))
        assert isinstance(text, str)
        assert len(text) > 0

    def test_extract_text_from_docx_function_error(self):
        """Test extract_text_from_docx function with error"""
        with patch('builtins.print') as mock_print:
            text = extract_text_from_docx('nonexistent.docx')
            assert text == ""
            mock_print.assert_called()

    def test_compare_texts_function(self, sample_template_text, sample_contract_text):
        """Test compare_texts function"""
        changes = compare_texts(sample_template_text, sample_contract_text)
        assert isinstance(changes, list)
        assert len(changes) > 0
        
        # Verify change format
        for change in changes:
            assert isinstance(change, tuple)
            assert len(change) == 2
            assert change[0] in ['delete', 'insert']
            assert isinstance(change[1], str)

    def test_compare_texts_function_no_changes(self):
        """Test compare_texts function with identical texts"""
        text = "This is identical text"
        changes = compare_texts(text, text)
        assert isinstance(changes, list)
        assert len(changes) == 0

    def test_create_commented_docx_function(self, test_docx_file):
        """Test create_commented_docx function"""
        analysis_results = [
            {
                'classification': 'SIGNIFICANT',
                'explanation': 'Test change',
                'deleted_text': 'old',
                'inserted_text': 'new'
            }
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
            output_path = tmp.name
        
        try:
            result = create_commented_docx(
                str(test_docx_file), 
                analysis_results, 
                output_path
            )
            assert result is True
            assert os.path.exists(output_path)
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_save_analysis_metadata_function(self):
        """Test save_analysis_metadata function"""
        with tempfile.TemporaryDirectory() as temp_dir:
            analysis_results = [{'classification': 'SIGNIFICANT'}]
            
            metadata_path = save_analysis_metadata(
                'test.docx',
                'template.docx',
                analysis_results,
                temp_dir
            )
            
            assert os.path.exists(metadata_path)
            
            # Verify JSON content
            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            assert 'uploaded_filename' in metadata
            assert 'selected_template' in metadata
            assert 'analysis_timestamp' in metadata
            assert 'total_changes' in metadata
            assert 'analysis_results' in metadata


class TestAnalyzerEdgeCases:
    """Test edge cases and error conditions"""

    def test_empty_texts(self, analyzer):
        """Test analyzer with empty texts"""
        changes = analyzer.find_changes("", "")
        assert isinstance(changes, list)
        assert len(changes) == 0
        
        similarity = analyzer.calculate_similarity("", "")
        assert similarity == 1.0

    def test_whitespace_only_texts(self, analyzer):
        """Test analyzer with whitespace-only texts"""
        changes = analyzer.find_changes("   ", "   ")
        assert isinstance(changes, list)
        
        similarity = analyzer.calculate_similarity("   ", "   ")
        assert similarity == 1.0

    def test_unicode_text(self, analyzer):
        """Test analyzer with unicode text"""
        text1 = "This contains unicode: éñøÿ"
        text2 = "This contains unicode: éñøÿ"
        
        changes = analyzer.find_changes(text1, text2)
        assert isinstance(changes, list)
        
        similarity = analyzer.calculate_similarity(text1, text2)
        assert similarity == 1.0

    def test_very_long_texts(self, analyzer):
        """Test analyzer with very long texts"""
        long_text1 = "A" * 10000
        long_text2 = "B" * 10000
        
        changes = analyzer.find_changes(long_text1, long_text2)
        assert isinstance(changes, list)
        
        similarity = analyzer.calculate_similarity(long_text1, long_text2)
        assert 0.0 <= similarity <= 1.0

    def test_special_characters(self, analyzer):
        """Test analyzer with special characters"""
        text1 = "Special chars: !@#$%^&*()_+-=[]{}|;:,.<>?"
        text2 = "Special chars: !@#$%^&*()_+-=[]{}|;:,.<>?"
        
        changes = analyzer.find_changes(text1, text2)
        assert isinstance(changes, list)
        
        similarity = analyzer.calculate_similarity(text1, text2)
        assert similarity == 1.0
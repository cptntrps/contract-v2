"""
Test comparison engine functionality
"""
import pytest
from app.core.services.comparison_engine import ComparisonEngine, ComparisonError


class TestComparisonEngine:
    """Test ComparisonEngine functionality"""
    
    @pytest.fixture
    def engine(self):
        """Create comparison engine instance"""
        return ComparisonEngine()
    
    @pytest.fixture
    def sample_texts(self):
        """Sample texts for comparison testing"""
        return {
            'original': """This is a sample contract.
            The terms are as follows:
            1. Payment due in 30 days
            2. Service level agreement applies
            3. Termination clause included""",
            
            'modified': """This is a sample contract.
            The terms are as follows:
            1. Payment due in 45 days
            2. Service level agreement applies
            3. Early termination clause included
            4. Additional warranty terms""",
            
            'identical': """This is a sample contract.
            The terms are as follows:
            1. Payment due in 30 days
            2. Service level agreement applies
            3. Termination clause included""",
            
            'completely_different': """Completely different document.
            This has nothing in common.
            No similar content at all."""
        }
    
    def test_calculate_similarity_identical(self, engine, sample_texts):
        """Test similarity calculation for identical texts"""
        similarity = engine.calculate_similarity(
            sample_texts['original'], 
            sample_texts['identical']
        )
        assert similarity == 1.0
    
    def test_calculate_similarity_different(self, engine, sample_texts):
        """Test similarity calculation for different texts"""
        similarity = engine.calculate_similarity(
            sample_texts['original'],
            sample_texts['completely_different']
        )
        assert 0.0 <= similarity < 0.5  # Should be low similarity
    
    def test_calculate_similarity_modified(self, engine, sample_texts):
        """Test similarity calculation for modified texts"""
        similarity = engine.calculate_similarity(
            sample_texts['original'],
            sample_texts['modified']
        )
        assert 0.5 <= similarity <= 0.9  # Should be moderate similarity
    
    def test_calculate_similarity_empty_texts(self, engine):
        """Test similarity calculation with empty texts"""
        # Both empty should be 1.0
        assert engine.calculate_similarity("", "") == 1.0
        
        # One empty should be 0.0
        assert engine.calculate_similarity("text", "") == 0.0
        assert engine.calculate_similarity("", "text") == 0.0
    
    def test_find_changes_basic(self, engine, sample_texts):
        """Test basic change detection"""
        changes = engine.find_changes(
            sample_texts['original'],
            sample_texts['modified']
        )
        
        assert isinstance(changes, list)
        assert len(changes) > 0
        
        # Check change format
        for change in changes:
            assert isinstance(change, tuple)
            assert len(change) == 2
            assert change[0] in ['delete', 'insert']
    
    def test_find_changes_identical(self, engine, sample_texts):
        """Test change detection for identical texts"""
        changes = engine.find_changes(
            sample_texts['original'],
            sample_texts['identical']
        )
        assert changes == []
    
    def test_find_changes_empty(self, engine):
        """Test change detection with empty texts"""
        # Both empty
        changes = engine.find_changes("", "")
        assert changes == []
        
        # Insert into empty
        changes = engine.find_changes("", "new text")
        assert len(changes) == 1
        assert changes[0][0] == 'insert'
        
        # Delete from text
        changes = engine.find_changes("old text", "")
        assert len(changes) == 1
        assert changes[0][0] == 'delete'
    
    def test_find_detailed_changes(self, engine, sample_texts):
        """Test detailed change detection"""
        changes = engine.find_detailed_changes(
            sample_texts['original'],
            sample_texts['modified']
        )
        
        assert isinstance(changes, list)
        assert len(changes) > 0
        
        # Check detailed change structure
        for change in changes:
            assert isinstance(change, dict)
            required_keys = [
                'operation', 'original_start', 'original_end',
                'modified_start', 'modified_end', 'deleted_text',
                'inserted_text', 'context_before', 'context_after'
            ]
            for key in required_keys:
                assert key in change
    
    def test_find_detailed_changes_types(self, engine):
        """Test different types of detailed changes"""
        # Test replacement
        changes = engine.find_detailed_changes(
            "Payment due in 30 days",
            "Payment due in 45 days"
        )
        
        assert len(changes) >= 1
        replace_change = next((c for c in changes if c['operation'] == 'replace'), None)
        if replace_change:
            assert '30' in replace_change['deleted_text']
            assert '45' in replace_change['inserted_text']
    
    def test_find_word_level_changes(self, engine):
        """Test word-level change detection"""
        text1 = "The quick brown fox jumps"
        text2 = "The slow brown fox walks"
        
        changes = engine.find_word_level_changes(text1, text2)
        
        assert isinstance(changes, list)
        assert len(changes) > 0
        
        # Check word-level change structure
        for change in changes:
            assert isinstance(change, dict)
            required_keys = [
                'operation', 'deleted_words', 'inserted_words',
                'position', 'deleted_text', 'inserted_text'
            ]
            for key in required_keys:
                assert key in change
    
    def test_filter_significant_changes(self, engine, sample_texts):
        """Test filtering of significant changes"""
        # Get all changes first
        changes = engine.find_detailed_changes(
            sample_texts['original'],
            sample_texts['modified']
        )
        
        # Filter for significant changes
        significant = engine.filter_significant_changes(
            changes,
            min_length=5,
            ignore_whitespace=True
        )
        
        assert isinstance(significant, list)
        assert len(significant) <= len(changes)
        
        # Check that filtered changes meet criteria
        for change in significant:
            deleted_len = len(change.get('deleted_text', ''))
            inserted_len = len(change.get('inserted_text', ''))
            total_len = deleted_len + inserted_len
            assert total_len >= 5
    
    def test_filter_whitespace_changes(self, engine):
        """Test filtering of whitespace-only changes"""
        changes = [
            {
                'operation': 'replace',
                'deleted_text': '  ',
                'inserted_text': '    '
            },
            {
                'operation': 'replace', 
                'deleted_text': 'important text',
                'inserted_text': 'very important text'
            }
        ]
        
        significant = engine.filter_significant_changes(
            changes,
            ignore_whitespace=True
        )
        
        # Should filter out whitespace-only change
        assert len(significant) == 1
        assert 'important text' in significant[0]['deleted_text']
    
    def test_get_change_statistics(self, engine, sample_texts):
        """Test change statistics generation"""
        changes = engine.find_detailed_changes(
            sample_texts['original'],
            sample_texts['modified']
        )
        
        stats = engine.get_change_statistics(changes)
        
        # Check statistics structure
        required_keys = [
            'total_changes', 'insertions', 'deletions', 'replacements',
            'total_inserted_chars', 'total_deleted_chars', 
            'largest_change', 'average_change_size'
        ]
        
        for key in required_keys:
            assert key in stats
        
        # Validate statistics values
        assert stats['total_changes'] == len(changes)
        assert stats['insertions'] >= 0
        assert stats['deletions'] >= 0
        assert stats['replacements'] >= 0
        assert stats['total_changes'] == (
            stats['insertions'] + stats['deletions'] + stats['replacements']
        )
    
    def test_get_change_statistics_empty(self, engine):
        """Test change statistics for empty change list"""
        stats = engine.get_change_statistics([])
        
        assert stats['total_changes'] == 0
        assert stats['insertions'] == 0
        assert stats['deletions'] == 0
        assert stats['replacements'] == 0
        assert stats['largest_change'] == 0
        assert stats['average_change_size'] == 0
    
    def test_comparison_error_handling(self, engine):
        """Test error handling in comparison operations"""
        # Test with None inputs - these should be handled gracefully or raise errors
        # Based on the implementation, None inputs return 0.0 for similarity
        similarity = engine.calculate_similarity(None, "text")
        assert similarity == 0.0
        
        similarity = engine.calculate_similarity("text", None)
        assert similarity == 0.0
        
        # find_changes with None should raise ComparisonError
        with pytest.raises(Exception):  # Should raise ComparisonError
            engine.find_changes("text", None)
            
        with pytest.raises(Exception):  # Should raise ComparisonError
            engine.find_changes(None, "text")
    
    def test_insignificant_change_detection(self, engine):
        """Test detection of insignificant changes"""
        # Test case changes
        changes = [
            {
                'deleted_text': 'contract',
                'inserted_text': 'Contract'
            }
        ]
        
        # Should be filtered as insignificant
        significant = engine.filter_significant_changes(changes)
        assert len(significant) == 0
        
        # Test punctuation changes
        changes = [
            {
                'deleted_text': 'agreement.',
                'inserted_text': 'agreement;'
            }
        ]
        
        significant = engine.filter_significant_changes(changes)
        assert len(significant) == 0
    
    def test_context_extraction(self, engine):
        """Test context extraction in detailed changes"""
        text1 = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        text2 = "Line 1\nLine 2\nModified Line 3\nLine 4\nLine 5"
        
        changes = engine.find_detailed_changes(text1, text2)
        
        # Find the replacement change
        replace_change = next((c for c in changes if c['operation'] == 'replace'), None)
        assert replace_change is not None
        
        # Check context extraction
        assert replace_change['context_before'] != ''
        assert replace_change['context_after'] != ''
        assert 'Line 2' in replace_change['context_before']
        assert 'Line 4' in replace_change['context_after']
    
    def test_large_text_comparison(self, engine):
        """Test comparison with large texts"""
        large_text1 = "Line content\n" * 1000
        large_text2 = "Line content\n" * 999 + "Modified line\n"
        
        # Should handle large texts without errors
        similarity = engine.calculate_similarity(large_text1, large_text2)
        assert 0.0 <= similarity <= 1.0
        
        changes = engine.find_changes(large_text1, large_text2)
        assert isinstance(changes, list)
    
    def test_unicode_handling(self, engine):
        """Test handling of unicode characters"""
        text1 = "Contrat français avec accents éàü"
        text2 = "Contract français avec accents éàü modifié"
        
        similarity = engine.calculate_similarity(text1, text2)
        assert 0.0 <= similarity <= 1.0
        
        changes = engine.find_changes(text1, text2)
        assert isinstance(changes, list)
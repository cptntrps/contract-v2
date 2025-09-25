"""
Comparison Engine Service

Handles text comparison and change detection algorithms.
"""

import difflib
from typing import List, Tuple, Dict, Any

from ...utils.logging.setup import get_logger

logger = get_logger(__name__)


class ComparisonError(Exception):
    """Exception raised when text comparison fails"""
    pass


class ComparisonEngine:
    """
    Text comparison engine for detecting changes between documents.
    
    Handles:
    - Text similarity calculation
    - Change detection using difflib
    - Context extraction around changes
    - Change categorization and filtering
    """
    
    def __init__(self):
        """Initialize comparison engine"""
        logger.debug("Comparison engine initialized")
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts using SequenceMatcher.
        
        Args:
            text1: Original text
            text2: Modified text
            
        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        try:
            if not text1 and not text2:
                return 1.0  # Both empty
            
            if not text1 or not text2:
                return 0.0  # One empty
            
            similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
            
            logger.debug(f"Calculated similarity: {similarity:.3f}")
            return similarity
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            raise ComparisonError(f"Similarity calculation failed: {e}")
    
    def find_changes(self, text1: str, text2: str) -> List[Tuple[str, str]]:
        """
        Compare two texts and return structured differences.
        
        Args:
            text1: Original text (template)
            text2: Modified text (contract)
            
        Returns:
            List of differences in format [('operation', 'text'), ...]
            where operation is 'delete' or 'insert'
        """
        try:
            if not text1 and not text2:
                return []
            
            # Use unified diff to find changes
            differ = difflib.unified_diff(
                text1.splitlines(keepends=True),
                text2.splitlines(keepends=True),
                lineterm='',
                n=0  # No context lines
            )
            
            changes = []
            for line in differ:
                # Skip diff headers
                if line.startswith('--- ') or line.startswith('+++ ') or line.startswith('@@'):
                    continue
                elif line.startswith('-'):
                    changes.append(('delete', line[1:]))
                elif line.startswith('+'):
                    changes.append(('insert', line[1:]))
            
            logger.debug(f"Found {len(changes)} changes")
            return changes
            
        except Exception as e:
            logger.error(f"Error finding changes: {e}")
            raise ComparisonError(f"Change detection failed: {e}")
    
    def find_detailed_changes(self, text1: str, text2: str) -> List[Dict[str, Any]]:
        """
        Find detailed changes with context and position information.
        
        Args:
            text1: Original text (template)
            text2: Modified text (contract)
            
        Returns:
            List of detailed change dictionaries
        """
        try:
            changes = []
            
            # Split texts into lines for analysis
            lines1 = text1.splitlines()
            lines2 = text2.splitlines()
            
            # Use SequenceMatcher for detailed comparison
            matcher = difflib.SequenceMatcher(None, lines1, lines2)
            
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'equal':
                    continue  # No change
                
                change = {
                    'operation': tag,
                    'original_start': i1,
                    'original_end': i2,
                    'modified_start': j1,
                    'modified_end': j2,
                    'deleted_text': '',
                    'inserted_text': '',
                    'context_before': '',
                    'context_after': ''
                }
                
                # Extract deleted and inserted text
                if tag in ['delete', 'replace']:
                    change['deleted_text'] = '\n'.join(lines1[i1:i2])
                
                if tag in ['insert', 'replace']:
                    change['inserted_text'] = '\n'.join(lines2[j1:j2])
                
                # Extract context
                context_size = 2
                
                # Context before
                if i1 > 0:
                    context_start = max(0, i1 - context_size)
                    change['context_before'] = '\n'.join(lines1[context_start:i1])
                
                # Context after
                if i2 < len(lines1):
                    context_end = min(len(lines1), i2 + context_size)
                    change['context_after'] = '\n'.join(lines1[i2:context_end])
                
                changes.append(change)
            
            logger.debug(f"Found {len(changes)} detailed changes")
            return changes
            
        except Exception as e:
            logger.error(f"Error finding detailed changes: {e}")
            raise ComparisonError(f"Detailed change detection failed: {e}")
    
    def find_word_level_changes(self, text1: str, text2: str) -> List[Dict[str, Any]]:
        """
        Find changes at word level for more granular analysis.
        
        Args:
            text1: Original text
            text2: Modified text
            
        Returns:
            List of word-level changes
        """
        try:
            # Split into words while preserving whitespace information
            words1 = text1.split()
            words2 = text2.split()
            
            matcher = difflib.SequenceMatcher(None, words1, words2)
            changes = []
            
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'equal':
                    continue
                
                change = {
                    'operation': tag,
                    'deleted_words': words1[i1:i2] if tag in ['delete', 'replace'] else [],
                    'inserted_words': words2[j1:j2] if tag in ['insert', 'replace'] else [],
                    'position': i1,
                    'deleted_text': ' '.join(words1[i1:i2]) if tag in ['delete', 'replace'] else '',
                    'inserted_text': ' '.join(words2[j1:j2]) if tag in ['insert', 'replace'] else ''
                }
                
                changes.append(change)
            
            logger.debug(f"Found {len(changes)} word-level changes")
            return changes
            
        except Exception as e:
            logger.error(f"Error finding word-level changes: {e}")
            raise ComparisonError(f"Word-level change detection failed: {e}")
    
    def filter_significant_changes(
        self,
        changes: List[Dict[str, Any]],
        min_length: int = 5,
        ignore_whitespace: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Filter changes to remove insignificant ones.
        
        Args:
            changes: List of changes to filter
            min_length: Minimum character length for significant changes
            ignore_whitespace: Whether to ignore whitespace-only changes
            
        Returns:
            Filtered list of significant changes
        """
        try:
            significant_changes = []
            
            for change in changes:
                deleted_text = change.get('deleted_text', '')
                inserted_text = change.get('inserted_text', '')
                
                # Skip if only whitespace changes
                if ignore_whitespace:
                    if deleted_text.strip() == '' and inserted_text.strip() == '':
                        continue
                
                # Skip if changes are too small
                total_change_length = len(deleted_text) + len(inserted_text)
                if total_change_length < min_length:
                    continue
                
                # Skip common insignificant patterns
                if self._is_insignificant_change(deleted_text, inserted_text):
                    continue
                
                significant_changes.append(change)
            
            logger.debug(f"Filtered to {len(significant_changes)} significant changes from {len(changes)} total")
            return significant_changes
            
        except Exception as e:
            logger.error(f"Error filtering changes: {e}")
            return changes  # Return original list if filtering fails
    
    def _is_insignificant_change(self, deleted_text: str, inserted_text: str) -> bool:
        """
        Check if a change is insignificant based on content patterns.
        
        Args:
            deleted_text: Text that was deleted
            inserted_text: Text that was inserted
            
        Returns:
            True if change is insignificant
        """
        # Common insignificant patterns
        insignificant_patterns = [
            # Punctuation changes
            (deleted_text.strip(' .,;'), inserted_text.strip(' .,;')),
            # Case changes
            (deleted_text.lower(), inserted_text.lower()),
            # Multiple spaces to single space
            (' '.join(deleted_text.split()), ' '.join(inserted_text.split()))
        ]
        
        for pattern in insignificant_patterns:
            if pattern[0] == pattern[1]:
                return True
        
        # Very short changes (single characters)
        if len(deleted_text) <= 1 and len(inserted_text) <= 1:
            return True
        
        return False
    
    def get_change_statistics(self, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate statistics about the changes.
        
        Args:
            changes: List of changes to analyze
            
        Returns:
            Dictionary with change statistics
        """
        try:
            stats = {
                'total_changes': len(changes),
                'insertions': 0,
                'deletions': 0,
                'replacements': 0,
                'total_inserted_chars': 0,
                'total_deleted_chars': 0,
                'largest_change': 0,
                'average_change_size': 0
            }
            
            if not changes:
                return stats
            
            change_sizes = []
            
            for change in changes:
                operation = change.get('operation', '')
                deleted_text = change.get('deleted_text', '')
                inserted_text = change.get('inserted_text', '')
                
                # Count operations
                if operation == 'insert':
                    stats['insertions'] += 1
                elif operation == 'delete':
                    stats['deletions'] += 1
                elif operation == 'replace':
                    stats['replacements'] += 1
                
                # Count characters
                stats['total_deleted_chars'] += len(deleted_text)
                stats['total_inserted_chars'] += len(inserted_text)
                
                # Track change sizes
                change_size = len(deleted_text) + len(inserted_text)
                change_sizes.append(change_size)
                stats['largest_change'] = max(stats['largest_change'], change_size)
            
            # Calculate average
            if change_sizes:
                stats['average_change_size'] = sum(change_sizes) / len(change_sizes)
            
            logger.debug(f"Generated change statistics: {stats['total_changes']} changes")
            return stats
            
        except Exception as e:
            logger.error(f"Error generating change statistics: {e}")
            return {'error': str(e)}


__all__ = ['ComparisonEngine', 'ComparisonError']
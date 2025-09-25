"""
Base Report Generator - Domain Layer

Abstract base class for all report generators following single responsibility.
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from ....utils.logging.setup import get_logger

logger = get_logger(__name__)


class ReportError(Exception):
    """Custom exception for report generation errors."""
    pass


class BaseReportGenerator(ABC):
    """
    Abstract base class for all report generators.
    
    Purpose: Defines common interface and shared functionality for all
    format-specific report generators. Enforces consistent architecture
    and provides utilities for path validation and metadata handling.
    
    AI Context: Base class for the report generation system. All format-specific
    generators inherit from this. When debugging report issues, check format-
    specific generators first, then common base functionality here.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize base report generator.
        
        Args:
            config: Configuration for report generation parameters
            
        AI Context: Base initialization that should be called by all subclasses
        via super().__init__(). Sets up logging and configuration.
        """
        self.config = config or {}
        logger.debug(f"{self.__class__.__name__} initialized")
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return the format name handled by this generator."""
        pass
    
    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension for this format."""
        pass
    
    @property
    @abstractmethod
    def dependencies_available(self) -> bool:
        """Check if required dependencies are available."""
        pass
    
    @abstractmethod
    def generate_report(self, analysis: Any, output_path: str, **options) -> bool:
        """
        Generate report in this format.
        
        Args:
            analysis: Analysis result to generate report from
            output_path: Path to save report
            **options: Format-specific options
            
        Returns:
            True if successful
            
        Raises:
            ReportError: If generation fails
        """
        pass
    
    def validate_dependencies(self) -> None:
        """
        Validate that required dependencies are available.
        
        Raises:
            ReportError: If required dependencies are missing
            
        AI Context: Called before report generation to ensure dependencies
        are available. Each format-specific generator implements its own
        dependency checking logic.
        """
        if not self.dependencies_available:
            raise ReportError(f"Required dependencies for {self.format_name} format are not available")
    
    def validate_output_path(self, output_path: str) -> str:
        """
        Validate and normalize output path.
        
        Args:
            output_path: Requested output path
            
        Returns:
            Normalized path with correct extension
            
        Raises:
            ReportError: If path is invalid or not writable
            
        AI Context: Common path validation used by all generators. Ensures
        parent directories exist, adds extensions, and validates write permissions.
        """
        try:
            path = Path(output_path)
            
            # Add extension if missing
            if not path.suffix:
                path = path.with_suffix(self.file_extension)
            
            # Ensure parent directory exists
            parent = path.parent
            if not parent.exists():
                parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {parent}")
            
            # Test write permissions
            self._test_write_permissions(path)
            
            return str(path)
            
        except Exception as e:
            raise ReportError(f"Invalid output path '{output_path}': {e}")
    
    def create_metadata(self, analysis: Any, **options) -> Dict[str, Any]:
        """
        Create standard metadata for reports.
        
        Args:
            analysis: Analysis result
            **options: Additional options
            
        Returns:
            Dictionary containing report metadata
            
        AI Context: Standard metadata creation used by all generators.
        Provides consistent metadata structure across all report formats.
        """
        return {
            'format': self.format_name,
            'extension': self.file_extension,
            'generator': self.__class__.__name__,
            'generation_timestamp': datetime.now().isoformat(),
            'analysis_id': getattr(analysis, 'analysis_id', None),
            'contract_id': getattr(analysis, 'contract_id', None),
            'template_id': getattr(analysis, 'template_id', None),
            'options': options,
            'generator_version': '2.0.0'
        }
    
    def log_generation_start(self, output_path: str) -> None:
        """Log report generation start."""
        logger.info(f"Starting {self.format_name} report generation: {output_path}")
    
    def log_generation_success(self, output_path: str) -> None:
        """Log successful report generation."""
        logger.info(f"{self.format_name} report generated successfully: {output_path}")
    
    def log_generation_failure(self, output_path: str, error: Exception) -> None:
        """Log report generation failure."""
        logger.error(f"{self.format_name} report generation failed for {output_path}: {error}")
    
    def _test_write_permissions(self, path: Path) -> None:
        """
        Test write permissions for the given path.
        
        Args:
            path: Path to test
            
        Raises:
            ReportError: If path is not writable
        """
        try:
            # Try to create a temporary test file
            test_file = path.parent / f".test_{datetime.now().timestamp()}"
            test_file.touch()
            test_file.unlink()
            
        except Exception as e:
            raise ReportError(f"Cannot write to path '{path}': {e}")
    
    def wrap_text(self, text: str, width: int) -> List[str]:
        """
        Wrap text to specified width.
        
        Args:
            text: Text to wrap
            width: Maximum line width
            
        Returns:
            List of wrapped lines
            
        AI Context: Utility method used by multiple generators for text formatting.
        Provides consistent text wrapping behavior across formats.
        """
        if not text:
            return []
            
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(word)
            
            # If adding this word would exceed width, start new line
            if current_length + word_length + 1 > width:
                if current_line:  # Don't add empty lines
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = word_length
            else:
                current_line.append(word)
                current_length += word_length + 1  # +1 for space
        
        # Add final line if not empty
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def format_changes_for_display(self, changes: List[Any]) -> List[Dict[str, Any]]:
        """
        Format changes for display in reports.
        
        Args:
            changes: List of change objects
            
        Returns:
            List of formatted change dictionaries
            
        AI Context: Common change formatting used by multiple generators.
        Provides consistent change display format across all report types.
        """
        formatted = []
        
        for change in changes:
            # Handle different change types
            change_type = getattr(change, 'change_type', None)
            if hasattr(change_type, 'value'):
                change_type = change_type.value
            
            display_text = self._create_change_display_text(change, change_type)
            context_text = self._create_context_text(change)
            
            formatted.append({
                'operation': change_type or 'unknown',
                'display_text': display_text,
                'context': context_text,
                'position': getattr(change, 'line_number', 0) or 0,
                'original_text': getattr(change, 'deleted_text', '') or '',
                'modified_text': getattr(change, 'inserted_text', '') or ''
            })
        
        return formatted
    
    def _create_change_display_text(self, change: Any, change_type: str) -> str:
        """Create display text for a change."""
        deleted_text = getattr(change, 'deleted_text', '') or ''
        inserted_text = getattr(change, 'inserted_text', '') or ''
        
        if change_type == 'replacement':
            return f"{deleted_text} → {inserted_text}"
        elif change_type == 'insertion':
            return f"+ {inserted_text}"
        elif change_type == 'deletion':
            return f"- {deleted_text}"
        else:
            # Handle unknown change types
            if inserted_text and deleted_text:
                return f"{deleted_text} → {inserted_text}"
            elif inserted_text:
                return f"+ {inserted_text}"
            elif deleted_text:
                return f"- {deleted_text}"
            else:
                return "No change text available"
    
    def _create_context_text(self, change: Any) -> str:
        """Create context text for a change."""
        context_before = getattr(change, 'context_before', '') or ''
        context_after = getattr(change, 'context_after', '') or ''
        
        if context_before or context_after:
            return f"{context_before} ... {context_after}".strip()
        else:
            return "No context available"
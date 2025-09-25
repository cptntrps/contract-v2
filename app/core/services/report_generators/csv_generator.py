"""
CSV Report Generator - Domain Layer

Specialized generator for CSV reports with tabular data.
Following architectural standards: single responsibility, comprehensive documentation.
"""

import csv
from typing import Dict, Any, Optional, List

from .base_generator import BaseReportGenerator, ReportError
from ....utils.logging.setup import get_logger

logger = get_logger(__name__)


class CSVReportGenerator(BaseReportGenerator):
    """
    Specialized CSV report generator for tabular data export.
    
    Purpose: Generates CSV reports containing analysis data in tabular format.
    Ideal for spreadsheet applications, data analysis tools, and systems
    that require simple structured data import.
    
    AI Context: CSV-specific report generator. Always available as it uses
    Python's built-in csv module. Provides clean tabular data export with
    proper escaping and encoding.
    """
    
    @property
    def format_name(self) -> str:
        """Return format name for CSV reports."""
        return 'csv'
    
    @property
    def file_extension(self) -> str:
        """Return file extension for CSV files."""
        return '.csv'
    
    @property
    def dependencies_available(self) -> bool:
        """CSV is always available (built-in Python module)."""
        return True
    
    def generate_report(self, analysis: Any, output_path: str,
                       include_headers: bool = True,
                       delimiter: str = ',',
                       encoding: str = 'utf-8',
                       **options) -> bool:
        """
        Generate CSV report with changes data in tabular format.
        
        Purpose: Creates CSV file containing all change data in structured
        tabular format. Handles proper escaping of text fields and ensures
        compatibility with spreadsheet applications.
        
        Args:
            analysis: Analysis result containing changes and metadata
            output_path: Path to save CSV file
            include_headers: Whether to include column headers
            delimiter: Field delimiter character
            encoding: File encoding
            **options: Additional CSV-specific options
            
        Returns:
            True if successful
            
        Raises:
            ReportError: If CSV generation fails
            
        AI Context: Main CSV generation method. Creates tabular data with
        proper field escaping. For debugging, check field formatting and
        encoding issues.
        """
        # Validate path (no dependencies to check for CSV)
        normalized_path = self.validate_output_path(output_path)
        
        self.log_generation_start(normalized_path)
        
        try:
            with open(normalized_path, 'w', newline='', encoding=encoding) as f:
                # Define field names
                fieldnames = self._get_fieldnames(**options)
                
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
                
                # Write headers if requested
                if include_headers:
                    writer.writeheader()
                
                # Write change data
                changes = getattr(analysis, 'changes', [])
                formatted_changes = self.format_changes_for_display(changes)
                
                for idx, change in enumerate(formatted_changes):
                    row_data = self._build_row_data(change, changes[idx] if idx < len(changes) else None)
                    writer.writerow(row_data)
            
            self.log_generation_success(normalized_path)
            return True
            
        except Exception as e:
            self.log_generation_failure(normalized_path, e)
            raise ReportError(f"Failed to generate CSV report: {e}")
    
    def _get_fieldnames(self, **options) -> List[str]:
        """
        Get CSV field names based on options.
        
        Args:
            **options: CSV generation options
            
        Returns:
            List of field names for CSV headers
            
        AI Context: Defines CSV column structure. Can be customized based on
        options to include different fields or change field order.
        """
        # Standard fieldnames
        standard_fields = [
            'operation',
            'original_text',
            'modified_text',
            'position',
            'context',
            'classification',
            'explanation'
        ]
        
        # Check for custom fieldnames in options
        custom_fields = options.get('fieldnames')
        if custom_fields:
            return custom_fields
        
        # Check for extended fields option
        if options.get('extended_fields', False):
            return standard_fields + [
                'confidence_score',
                'context_before',
                'context_after',
                'change_category'
            ]
        
        return standard_fields
    
    def _build_row_data(self, formatted_change: Dict[str, Any], 
                       original_change: Any = None) -> Dict[str, Any]:
        """
        Build row data dictionary for CSV writer.
        
        Args:
            formatted_change: Formatted change data
            original_change: Original change object (for additional data)
            
        Returns:
            Dictionary with row data for CSV
            
        AI Context: Converts change data to CSV row format. Handles field
        mapping and ensures all required fields are present with proper values.
        """
        row_data = {
            'operation': formatted_change.get('operation', ''),
            'original_text': self._clean_text_for_csv(formatted_change.get('original_text', '')),
            'modified_text': self._clean_text_for_csv(formatted_change.get('modified_text', '')),
            'position': formatted_change.get('position', 0),
            'context': self._clean_text_for_csv(formatted_change.get('context', '')),
            'classification': '',
            'explanation': ''
        }
        
        # Add data from original change object if available
        if original_change:
            # Classification
            classification = getattr(original_change, 'classification', None)
            if hasattr(classification, 'value'):
                classification = classification.value
            row_data['classification'] = classification or ''
            
            # Explanation
            row_data['explanation'] = self._clean_text_for_csv(
                getattr(original_change, 'explanation', '') or ''
            )
            
            # Extended fields if needed
            row_data['confidence_score'] = getattr(original_change, 'confidence_score', '')
            row_data['context_before'] = self._clean_text_for_csv(
                getattr(original_change, 'context_before', '') or ''
            )
            row_data['context_after'] = self._clean_text_for_csv(
                getattr(original_change, 'context_after', '') or ''
            )
            row_data['change_category'] = self._determine_change_category(original_change)
        
        return row_data
    
    def _clean_text_for_csv(self, text: str) -> str:
        """
        Clean text for CSV output.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text suitable for CSV
            
        AI Context: Ensures text is properly formatted for CSV. Removes
        problematic characters and handles line breaks that could break
        CSV structure.
        """
        if not text:
            return ''
        
        # Convert to string if not already
        text = str(text)
        
        # Replace line breaks with spaces
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Replace multiple spaces with single space
        text = ' '.join(text.split())
        
        # Truncate very long text to avoid CSV parsing issues
        max_length = 1000
        if len(text) > max_length:
            text = text[:max_length] + '...'
        
        return text
    
    def _determine_change_category(self, change: Any) -> str:
        """
        Determine change category based on content analysis.
        
        Args:
            change: Change object
            
        Returns:
            Change category string
        """
        # Simple categorization based on content
        deleted_text = getattr(change, 'deleted_text', '') or ''
        inserted_text = getattr(change, 'inserted_text', '') or ''
        combined_text = (deleted_text + ' ' + inserted_text).lower()
        
        # Financial category
        if any(keyword in combined_text for keyword in ['$', 'payment', 'fee', 'cost', 'price']):
            return 'financial'
        
        # Date/time category
        if any(keyword in combined_text for keyword in ['date', 'deadline', 'schedule', 'term']):
            return 'temporal'
        
        # Legal category
        if any(keyword in combined_text for keyword in ['shall', 'liability', 'breach', 'termination']):
            return 'legal'
        
        # Scope category
        if any(keyword in combined_text for keyword in ['scope', 'deliverable', 'service', 'work']):
            return 'scope'
        
        return 'general'
    
    def generate_summary_csv(self, analysis: Any, output_path: str,
                           **options) -> bool:
        """
        Generate summary CSV with high-level analysis data.
        
        Args:
            analysis: Analysis result data
            output_path: Path to save CSV file
            **options: Additional options
            
        Returns:
            True if successful
            
        Raises:
            ReportError: If generation fails
            
        AI Context: Generates compact CSV with summary information rather
        than detailed change data. Useful for dashboard or overview reports.
        """
        normalized_path = self.validate_output_path(output_path)
        
        try:
            with open(normalized_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'analysis_id',
                    'contract_id',
                    'status',
                    'total_changes',
                    'insertions',
                    'deletions',
                    'replacements',
                    'created_at'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                statistics = getattr(analysis, 'statistics', {})
                
                summary_row = {
                    'analysis_id': getattr(analysis, 'analysis_id', ''),
                    'contract_id': getattr(analysis, 'contract_id', ''),
                    'status': getattr(analysis, 'status', ''),
                    'total_changes': statistics.get('total_changes', 0),
                    'insertions': statistics.get('insertions', 0),
                    'deletions': statistics.get('deletions', 0),
                    'replacements': statistics.get('replacements', 0),
                    'created_at': str(getattr(analysis, 'created_at', ''))
                }
                
                writer.writerow(summary_row)
            
            self.log_generation_success(normalized_path)
            return True
            
        except Exception as e:
            self.log_generation_failure(normalized_path, e)
            raise ReportError(f"Failed to generate summary CSV: {e}")
    
    def generate_changes_by_category_csv(self, analysis: Any, output_path: str,
                                       **options) -> bool:
        """
        Generate CSV grouped by change categories.
        
        Args:
            analysis: Analysis result data
            output_path: Path to save CSV file
            **options: Additional options
            
        Returns:
            True if successful
            
        Raises:
            ReportError: If generation fails
        """
        normalized_path = self.validate_output_path(output_path)
        
        try:
            with open(normalized_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'category',
                    'change_count',
                    'operation_type',
                    'sample_change'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                # Categorize changes
                changes = getattr(analysis, 'changes', [])
                category_data = self._categorize_changes(changes)
                
                for category, data in category_data.items():
                    writer.writerow({
                        'category': category,
                        'change_count': data['count'],
                        'operation_type': data['common_operation'],
                        'sample_change': self._clean_text_for_csv(data['sample_text'])
                    })
            
            self.log_generation_success(normalized_path)
            return True
            
        except Exception as e:
            self.log_generation_failure(normalized_path, e)
            raise ReportError(f"Failed to generate categorized CSV: {e}")
    
    def _categorize_changes(self, changes: List[Any]) -> Dict[str, Dict[str, Any]]:
        """Categorize changes and collect statistics."""
        categories = {}
        
        for change in changes:
            category = self._determine_change_category(change)
            
            if category not in categories:
                categories[category] = {
                    'count': 0,
                    'operations': [],
                    'sample_text': ''
                }
            
            categories[category]['count'] += 1
            
            # Track operation types
            change_type = getattr(change, 'change_type', None)
            if hasattr(change_type, 'value'):
                change_type = change_type.value
            if change_type:
                categories[category]['operations'].append(change_type)
            
            # Store sample text if not already set
            if not categories[category]['sample_text']:
                sample_text = getattr(change, 'inserted_text', '') or getattr(change, 'deleted_text', '')
                if sample_text:
                    categories[category]['sample_text'] = sample_text[:100]
        
        # Determine most common operation for each category
        for category, data in categories.items():
            if data['operations']:
                most_common = max(set(data['operations']), key=data['operations'].count)
                data['common_operation'] = most_common
            else:
                data['common_operation'] = 'unknown'
        
        return categories
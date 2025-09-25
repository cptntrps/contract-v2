"""
JSON Report Generator - Domain Layer

Specialized generator for JSON reports with structured data.
Following architectural standards: single responsibility, comprehensive documentation.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional

from .base_generator import BaseReportGenerator, ReportError
from ....utils.logging.setup import get_logger

logger = get_logger(__name__)


class JSONReportGenerator(BaseReportGenerator):
    """
    Specialized JSON report generator with structured data export.
    
    Purpose: Generates JSON reports containing complete analysis data in
    structured format. Ideal for API integration, data processing, and
    programmatic consumption of analysis results.
    
    AI Context: JSON-specific report generator. Always available as it uses
    Python's built-in json module. Provides complete data serialization
    with proper type handling and UTF-8 encoding.
    """
    
    @property
    def format_name(self) -> str:
        """Return format name for JSON reports."""
        return 'json'
    
    @property
    def file_extension(self) -> str:
        """Return file extension for JSON files."""
        return '.json'
    
    @property
    def dependencies_available(self) -> bool:
        """JSON is always available (built-in Python module)."""
        return True
    
    def generate_report(self, analysis: Any, output_path: str,
                       indent: int = 2,
                       include_metadata: bool = True,
                       **options) -> bool:
        """
        Generate JSON report with complete analysis data.
        
        Purpose: Creates structured JSON file containing all analysis data
        including changes, statistics, metadata, and AI analysis results.
        Ensures proper serialization of complex data types.
        
        Args:
            analysis: Analysis result containing changes and metadata
            output_path: Path to save JSON file
            indent: JSON indentation level for readability
            include_metadata: Whether to include generation metadata
            **options: Additional JSON-specific options
            
        Returns:
            True if successful
            
        Raises:
            ReportError: If JSON generation fails
            
        AI Context: Main JSON generation method. Handles complete data
        serialization with proper type conversion. For debugging, check
        data serialization and file encoding issues.
        """
        # Validate path (no dependencies to check for JSON)
        normalized_path = self.validate_output_path(output_path)
        
        self.log_generation_start(normalized_path)
        
        try:
            # Build complete data structure
            report_data = self._build_report_data(analysis, include_metadata, **options)
            
            # Write JSON file with proper encoding
            with open(normalized_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, 
                         indent=indent, 
                         ensure_ascii=False,
                         default=self._json_serializer,
                         separators=(',', ': ') if indent else (',', ':'))
            
            self.log_generation_success(normalized_path)
            return True
            
        except Exception as e:
            self.log_generation_failure(normalized_path, e)
            raise ReportError(f"Failed to generate JSON report: {e}")
    
    def _build_report_data(self, analysis: Any, include_metadata: bool,
                          **options) -> Dict[str, Any]:
        """
        Build complete report data structure.
        
        Args:
            analysis: Analysis result data
            include_metadata: Whether to include metadata
            **options: Additional options
            
        Returns:
            Complete report data dictionary
            
        AI Context: Core data building method. Converts analysis object to
        JSON-serializable dictionary with proper structure and type handling.
        """
        # Base analysis data
        data = {
            'analysis_id': getattr(analysis, 'analysis_id', None),
            'contract_id': getattr(analysis, 'contract_id', None),
            'template_id': getattr(analysis, 'template_id', None),
            'status': getattr(analysis, 'status', None),
            'created_at': self._serialize_datetime(getattr(analysis, 'created_at', None)),
            'completed_at': self._serialize_datetime(getattr(analysis, 'completed_at', None)),
            'statistics': getattr(analysis, 'statistics', {}),
            'llm_analysis': getattr(analysis, 'llm_analysis', None),
            'metadata': getattr(analysis, 'metadata', {}),
            'changes': self._serialize_changes(getattr(analysis, 'changes', []))
        }
        
        # Add generation metadata if requested
        if include_metadata:
            data['report_metadata'] = self.create_metadata(analysis, **options)
        
        # Add format-specific data
        data['format_info'] = {
            'format': self.format_name,
            'version': '2.0.0',
            'encoding': 'utf-8',
            'structure_version': '1.0'
        }
        
        return data
    
    def _serialize_changes(self, changes: list) -> list:
        """
        Serialize changes list to JSON-compatible format.
        
        Args:
            changes: List of change objects
            
        Returns:
            List of serialized change dictionaries
        """
        serialized_changes = []
        
        for change in changes:
            # Extract change type
            change_type = getattr(change, 'change_type', None)
            if hasattr(change_type, 'value'):
                change_type = change_type.value
            
            # Extract classification
            classification = getattr(change, 'classification', None)
            if hasattr(classification, 'value'):
                classification = classification.value
            
            change_data = {
                'operation': change_type,
                'original_text': getattr(change, 'deleted_text', None),
                'modified_text': getattr(change, 'inserted_text', None),
                'position': getattr(change, 'line_number', None),
                'context_before': getattr(change, 'context_before', None),
                'context_after': getattr(change, 'context_after', None),
                'classification': classification,
                'explanation': getattr(change, 'explanation', None),
                'confidence_score': getattr(change, 'confidence_score', None)
            }
            
            # Add any additional attributes
            if hasattr(change, 'metadata') and change.metadata:
                change_data['change_metadata'] = change.metadata
            
            serialized_changes.append(change_data)
        
        return serialized_changes
    
    def _serialize_datetime(self, dt: Any) -> Optional[str]:
        """
        Serialize datetime object to ISO format string.
        
        Args:
            dt: Datetime object or None
            
        Returns:
            ISO format string or None
        """
        if dt is None:
            return None
        
        if hasattr(dt, 'isoformat'):
            return dt.isoformat()
        
        # Handle string datetime
        if isinstance(dt, str):
            return dt
        
        return str(dt)
    
    def _json_serializer(self, obj: Any) -> Any:
        """
        Custom JSON serializer for complex objects.
        
        Args:
            obj: Object to serialize
            
        Returns:
            JSON-serializable representation
            
        AI Context: Handles serialization of complex objects that json.dump
        cannot handle by default. Converts datetime, enums, and custom objects.
        """
        # Handle datetime objects
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        
        # Handle enum objects
        if hasattr(obj, 'value'):
            return obj.value
        
        # Handle objects with dict representation
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        
        # Fallback to string representation
        return str(obj)
    
    def generate_minimal_report(self, analysis: Any, output_path: str,
                              **options) -> bool:
        """
        Generate minimal JSON report with essential data only.
        
        Args:
            analysis: Analysis result data
            output_path: Path to save JSON file
            **options: Additional options
            
        Returns:
            True if successful
            
        Raises:
            ReportError: If generation fails
            
        AI Context: Generates compact JSON report with only essential data.
        Useful for applications that need basic analysis results without
        full metadata and detailed information.
        """
        normalized_path = self.validate_output_path(output_path)
        
        try:
            # Build minimal data structure
            minimal_data = {
                'analysis_id': getattr(analysis, 'analysis_id', None),
                'status': getattr(analysis, 'status', None),
                'total_changes': getattr(analysis, 'statistics', {}).get('total_changes', 0),
                'changes': [
                    {
                        'type': getattr(change.change_type, 'value', 'unknown') 
                               if hasattr(change, 'change_type') else 'unknown',
                        'original': getattr(change, 'deleted_text', ''),
                        'modified': getattr(change, 'inserted_text', ''),
                        'position': getattr(change, 'line_number', 0)
                    }
                    for change in getattr(analysis, 'changes', [])
                ],
                'generated_at': datetime.now().isoformat()
            }
            
            with open(normalized_path, 'w', encoding='utf-8') as f:
                json.dump(minimal_data, f, separators=(',', ':'))
            
            self.log_generation_success(normalized_path)
            return True
            
        except Exception as e:
            self.log_generation_failure(normalized_path, e)
            raise ReportError(f"Failed to generate minimal JSON report: {e}")
    
    def generate_structured_export(self, analysis: Any, output_path: str,
                                 export_schema: str = 'standard',
                                 **options) -> bool:
        """
        Generate structured JSON export with specific schema.
        
        Args:
            analysis: Analysis result data
            output_path: Path to save JSON file
            export_schema: Export schema type ('standard', 'api', 'minimal')
            **options: Additional options
            
        Returns:
            True if successful
            
        Raises:
            ReportError: If generation fails
        """
        if export_schema == 'minimal':
            return self.generate_minimal_report(analysis, output_path, **options)
        elif export_schema == 'api':
            return self._generate_api_format(analysis, output_path, **options)
        else:
            return self.generate_report(analysis, output_path, **options)
    
    def _generate_api_format(self, analysis: Any, output_path: str,
                           **options) -> bool:
        """Generate JSON in API-friendly format."""
        normalized_path = self.validate_output_path(output_path)
        
        try:
            api_data = {
                'data': {
                    'id': getattr(analysis, 'analysis_id', None),
                    'type': 'contract_analysis',
                    'attributes': {
                        'contract_id': getattr(analysis, 'contract_id', None),
                        'template_id': getattr(analysis, 'template_id', None),
                        'status': getattr(analysis, 'status', None),
                        'statistics': getattr(analysis, 'statistics', {}),
                        'summary': getattr(analysis, 'llm_analysis', {}).get('summary', None)
                    },
                    'relationships': {
                        'changes': {
                            'data': [
                                {
                                    'type': 'change',
                                    'id': f"change_{idx}",
                                    'attributes': {
                                        'operation': getattr(change.change_type, 'value', 'unknown')
                                                   if hasattr(change, 'change_type') else 'unknown',
                                        'original_text': getattr(change, 'deleted_text', ''),
                                        'modified_text': getattr(change, 'inserted_text', ''),
                                        'position': getattr(change, 'line_number', 0)
                                    }
                                }
                                for idx, change in enumerate(getattr(analysis, 'changes', []))
                            ]
                        }
                    }
                },
                'meta': {
                    'generated_at': datetime.now().isoformat(),
                    'format': 'json-api',
                    'version': '1.0'
                }
            }
            
            with open(normalized_path, 'w', encoding='utf-8') as f:
                json.dump(api_data, f, indent=2, ensure_ascii=False)
            
            self.log_generation_success(normalized_path)
            return True
            
        except Exception as e:
            self.log_generation_failure(normalized_path, e)
            raise ReportError(f"Failed to generate API format JSON report: {e}")
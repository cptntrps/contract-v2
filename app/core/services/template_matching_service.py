"""
Template Matching Service - Domain Layer

Handles intelligent template matching based on contract content analysis.
Following architectural standards: single responsibility, comprehensive documentation.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from flask import current_app

from ...core.services.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class TemplateMatchingService:
    """
    Intelligent template matching service for contract analysis.
    
    Purpose: Analyzes contract content to find the best matching template using
    vendor-specific rules, document type detection, and similarity scoring.
    
    AI Context: This service centralizes all template matching business logic.
    When debugging template selection issues, start here. The service uses a
    three-tier matching strategy: vendor-specific → document type → similarity-based.
    """
    
    def __init__(self, templates_folder: Optional[str] = None):
        """
        Initialize template matching service.
        
        Args:
            templates_folder: Optional path to templates directory.
                            If None, uses Flask config or defaults to 'data/templates'
        """
        self.doc_processor = DocumentProcessor()
        self._templates_folder = templates_folder
        
    def find_best_template(self, contract) -> Optional[str]:
        """
        Find the best matching template for a contract using intelligent rules.
        
        Purpose: Implements three-tier matching strategy to select optimal template
        for contract analysis based on content analysis and business rules.
        
        Args:
            contract: Contract entity with file_path attribute for content extraction
        
        Returns:
            Optional[str]: Absolute path to best matching template file, or None if no match
        
        Raises:
            TemplateMatchingError: If template directory inaccessible or content extraction fails
            DocumentProcessingError: If contract file cannot be read
        
        AI Context: Primary template selection function. Matching strategy:
        1. Vendor-specific matching (highest priority)
        2. Document type matching (SOW vs Change Order)  
        3. Similarity-based matching (content analysis)
        For debugging, check template directory existence and contract content extraction first.
        """
        try:
            templates_dir = self._get_templates_directory()
            template_files = list(templates_dir.glob('*.docx'))
            
            if not template_files:
                logger.warning(f"No template files found in {templates_dir}")
                return None
            
            # Extract contract content for analysis
            contract_content = self._extract_contract_content(contract)
            if not contract_content:
                logger.warning("No content extracted from contract, using fallback template")
                return str(template_files[0])
            
            contract_content_lower = contract_content.lower()
            
            # Strategy 1: Vendor-specific matching (highest priority)
            vendor_match = self._match_by_vendor(contract_content_lower, templates_dir)
            if vendor_match:
                logger.info(f"Template selected by vendor matching: {vendor_match}")
                return vendor_match
            
            # Strategy 2: Document type matching
            doc_type_match = self._match_by_document_type(contract_content_lower, templates_dir)
            if doc_type_match:
                logger.info(f"Template selected by document type matching: {doc_type_match}")
                return doc_type_match
            
            # Strategy 3: Similarity-based matching (fallback)
            similarity_match = self._match_by_similarity(contract_content, template_files)
            if similarity_match:
                logger.info(f"Template selected by similarity matching: {similarity_match}")
                return similarity_match
            
            # Final fallback: first available template
            fallback_template = str(template_files[0])
            logger.warning(f"No intelligent match found, using fallback template: {fallback_template}")
            return fallback_template
            
        except Exception as e:
            logger.error(f"Template matching failed: {e}")
            raise TemplateMatchingError(f"Failed to find template match: {str(e)}")
    
    def _get_templates_directory(self) -> Path:
        """
        Get templates directory path with fallback logic.
        
        Returns:
            Path: Templates directory path
        
        Raises:
            TemplateMatchingError: If directory doesn't exist or isn't accessible
        """
        if self._templates_folder:
            templates_dir = Path(self._templates_folder)
        else:
            templates_dir = Path(current_app.config.get('TEMPLATES_FOLDER', 'data/templates'))
        
        if not templates_dir.exists():
            raise TemplateMatchingError(f"Templates directory not found: {templates_dir}")
        
        return templates_dir
    
    def _extract_contract_content(self, contract) -> Optional[str]:
        """
        Extract text content from contract file.
        
        Args:
            contract: Contract entity with file_path attribute
        
        Returns:
            Optional[str]: Extracted text content or None if extraction fails
        """
        try:
            return self.doc_processor.extract_text_from_docx(contract.file_path)
        except Exception as e:
            logger.error(f"Error extracting contract content: {e}")
            return None
    
    def _match_by_vendor(self, contract_content_lower: str, templates_dir: Path) -> Optional[str]:
        """
        Match template based on vendor-specific keywords in contract content.
        
        Purpose: Implements vendor-specific template matching rules for known
        vendors with specialized contract formats.
        
        Args:
            contract_content_lower: Lowercase contract content for case-insensitive matching
            templates_dir: Path to templates directory
        
        Returns:
            Optional[str]: Path to vendor-specific template or None if no vendor match
        
        AI Context: Vendor matching uses exact keyword matching with predefined
        vendor-template mappings. If vendor detected but template missing, logs warning.
        """
        vendor_templates = {
            'capgemini': 'VENDOR_CAPGEMINI_SOW_v1.docx',
            'blue optima': 'VENDOR_BLUEOPTIMA_SOW_v1.docx', 
            'blueoptima': 'VENDOR_BLUEOPTIMA_SOW_v1.docx',
            'epam': 'VENDOR_EPAM_SOW_v1.docx'
        }
        
        for vendor, template_name in vendor_templates.items():
            if vendor in contract_content_lower:
                template_path = templates_dir / template_name
                if template_path.exists():
                    logger.info(f"Vendor match found: {vendor} → {template_name}")
                    return str(template_path)
                else:
                    logger.warning(f"Vendor '{vendor}' detected but template '{template_name}' not found")
        
        return None
    
    def _match_by_document_type(self, contract_content_lower: str, templates_dir: Path) -> Optional[str]:
        """
        Match template based on document type analysis (SOW vs Change Order).
        
        Purpose: Classifies contract as Statement of Work or Change Order based
        on keyword frequency and selects appropriate template type.
        
        Args:
            contract_content_lower: Lowercase contract content for analysis
            templates_dir: Path to templates directory
        
        Returns:
            Optional[str]: Path to document-type-specific template or None if no clear type
        
        AI Context: Uses keyword frequency analysis to determine document type.
        SOW keywords include 'statement of work', 'scope of work'.
        Change Order keywords include 'change order', 'amendment', 'modification'.
        """
        sow_keywords = [
            'statement of work', 'sow', 'scope of work', 
            'work statement', 'services agreement'
        ]
        co_keywords = [
            'change order', 'change request', 'amendment', 
            'modification', 'addendum'
        ]
        
        sow_count = sum(1 for keyword in sow_keywords if keyword in contract_content_lower)
        co_count = sum(1 for keyword in co_keywords if keyword in contract_content_lower)
        
        logger.debug(f"Document type analysis: SOW keywords={sow_count}, CO keywords={co_count}")
        
        if sow_count > co_count and sow_count > 0:
            return self._find_sow_template(templates_dir)
        elif co_count > sow_count and co_count > 0:
            return self._find_change_order_template(templates_dir)
        
        return None
    
    def _find_sow_template(self, templates_dir: Path) -> Optional[str]:
        """Find the best SOW (Statement of Work) template."""
        sow_preferences = [
            'VENDOR_GENERIC_SOW_v1.docx',
            'BASE_SOW_TEMPLATE_v1.docx',
            'SOW_TEMPLATE.docx'
        ]
        
        for template_name in sow_preferences:
            template_path = templates_dir / template_name
            if template_path.exists():
                return str(template_path)
        
        # Fallback: any file with 'sow' in name
        sow_files = list(templates_dir.glob('*sow*.docx')) + list(templates_dir.glob('*SOW*.docx'))
        if sow_files:
            return str(sow_files[0])
        
        return None
    
    def _find_change_order_template(self, templates_dir: Path) -> Optional[str]:
        """Find the best Change Order template."""
        co_preferences = [
            'VENDOR_GENERIC_CO_v1.docx',
            'BASE_CHANGE_ORDER_v1.docx',
            'CHANGE_ORDER_TEMPLATE.docx'
        ]
        
        for template_name in co_preferences:
            template_path = templates_dir / template_name
            if template_path.exists():
                return str(template_path)
        
        # Fallback: any file with change order indicators
        co_patterns = ['*change*', '*amendment*', '*modification*']
        for pattern in co_patterns:
            co_files = list(templates_dir.glob(f'{pattern}.docx'))
            if co_files:
                return str(co_files[0])
        
        return None
    
    def _match_by_similarity(self, contract_content: str, template_files: List[Path]) -> Optional[str]:
        """
        Match template based on content similarity analysis.
        
        Purpose: Performs text similarity comparison between contract content
        and template content to find best match when vendor/type rules fail.
        
        Args:
            contract_content: Full contract text content
            template_files: List of available template file paths
        
        Returns:
            Optional[str]: Path to most similar template or None if all similarities below threshold
        
        AI Context: Uses basic word overlap similarity. In production, consider
        implementing semantic similarity using embeddings or TF-IDF for better accuracy.
        Current implementation is lightweight but may miss semantic matches.
        """
        if not contract_content or not template_files:
            return None
        
        best_match = None
        best_similarity = 0.0
        similarity_threshold = 0.1  # Minimum similarity required
        
        contract_words = set(contract_content.lower().split())
        
        for template_file in template_files:
            try:
                template_content = self.doc_processor.extract_text_from_docx(str(template_file))
                if not template_content:
                    continue
                
                template_words = set(template_content.lower().split())
                
                # Calculate Jaccard similarity (intersection over union)
                intersection = len(contract_words.intersection(template_words))
                union = len(contract_words.union(template_words))
                
                if union > 0:
                    similarity = intersection / union
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = str(template_file)
                        
            except Exception as e:
                logger.warning(f"Error calculating similarity for {template_file}: {e}")
                continue
        
        if best_similarity >= similarity_threshold:
            logger.info(f"Similarity match: {best_match} (score: {best_similarity:.3f})")
            return best_match
        else:
            logger.info(f"No similarity match above threshold {similarity_threshold} (best: {best_similarity:.3f})")
            return None
    
    def get_matching_statistics(self, contract) -> Dict[str, any]:
        """
        Get detailed matching statistics for debugging and analysis.
        
        Purpose: Provides detailed breakdown of matching logic results for
        debugging template selection issues and improving matching algorithms.
        
        Args:
            contract: Contract entity for analysis
        
        Returns:
            Dict[str, any]: Detailed matching statistics including:
                - vendor_matches: List of detected vendors
                - document_type_analysis: Keyword counts and classification
                - similarity_scores: Top template matches with scores
                - selected_template: Final template selection and reason
        
        AI Context: Use this function for debugging template matching issues.
        Provides complete visibility into matching decision process.
        """
        try:
            templates_dir = self._get_templates_directory()
            template_files = list(templates_dir.glob('*.docx'))
            contract_content = self._extract_contract_content(contract)
            
            if not contract_content:
                return {'error': 'Could not extract contract content'}
            
            contract_content_lower = contract_content.lower()
            
            # Analyze vendor matches
            vendor_analysis = self._analyze_vendor_matches(contract_content_lower)
            
            # Analyze document type
            doc_type_analysis = self._analyze_document_type(contract_content_lower)
            
            # Calculate similarity scores for all templates
            similarity_analysis = self._analyze_similarity_scores(contract_content, template_files)
            
            # Get final selection
            selected_template = self.find_best_template(contract)
            
            return {
                'vendor_analysis': vendor_analysis,
                'document_type_analysis': doc_type_analysis,
                'similarity_analysis': similarity_analysis,
                'selected_template': selected_template,
                'total_templates_available': len(template_files)
            }
            
        except Exception as e:
            logger.error(f"Error generating matching statistics: {e}")
            return {'error': str(e)}
    
    def _analyze_vendor_matches(self, contract_content_lower: str) -> Dict[str, bool]:
        """Analyze which vendors are detected in contract content."""
        vendors = ['capgemini', 'blue optima', 'blueoptima', 'epam']
        return {vendor: vendor in contract_content_lower for vendor in vendors}
    
    def _analyze_document_type(self, contract_content_lower: str) -> Dict[str, any]:
        """Analyze document type classification details."""
        sow_keywords = ['statement of work', 'sow', 'scope of work', 'work statement', 'services agreement']
        co_keywords = ['change order', 'change request', 'amendment', 'modification', 'addendum']
        
        sow_matches = [kw for kw in sow_keywords if kw in contract_content_lower]
        co_matches = [kw for kw in co_keywords if kw in contract_content_lower]
        
        return {
            'sow_keyword_count': len(sow_matches),
            'co_keyword_count': len(co_matches),
            'sow_keywords_found': sow_matches,
            'co_keywords_found': co_matches,
            'classification': 'sow' if len(sow_matches) > len(co_matches) else 'change_order' if len(co_matches) > 0 else 'unknown'
        }
    
    def _analyze_similarity_scores(self, contract_content: str, template_files: List[Path]) -> List[Dict[str, any]]:
        """Calculate similarity scores for all templates."""
        if not contract_content:
            return []
        
        contract_words = set(contract_content.lower().split())
        scores = []
        
        for template_file in template_files:
            try:
                template_content = self.doc_processor.extract_text_from_docx(str(template_file))
                if template_content:
                    template_words = set(template_content.lower().split())
                    intersection = len(contract_words.intersection(template_words))
                    union = len(contract_words.union(template_words))
                    similarity = intersection / union if union > 0 else 0.0
                    
                    scores.append({
                        'template': template_file.name,
                        'similarity_score': round(similarity, 4),
                        'word_intersection': intersection,
                        'word_union': union
                    })
            except Exception as e:
                scores.append({
                    'template': template_file.name,
                    'error': str(e)
                })
        
        # Sort by similarity score descending
        scores.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        return scores


class TemplateMatchingError(Exception):
    """
    Exception raised when template matching operations fail.
    
    Purpose: Provides specific exception type for template matching errors,
    allowing for targeted error handling in the analysis workflow.
    """
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        """
        Initialize template matching error.
        
        Args:
            message: Human-readable error description
            details: Optional additional error context
        """
        super().__init__(message)
        self.details = details or {}
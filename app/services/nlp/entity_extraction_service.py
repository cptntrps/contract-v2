"""
Entity Extraction Service - Domain Layer

Handles extraction and classification of named entities from contract text.
Following architectural standards: single responsibility, comprehensive documentation.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class ExtractedEntity:
    """Container for extracted entity information."""
    entity_type: str
    text: str
    confidence: float
    start_position: int
    end_position: int
    context: str
    metadata: Dict[str, Any]


class EntityExtractionService:
    """
    Extracts and classifies named entities from contract text.
    
    Purpose: Identifies and categorizes key entities such as parties, dates, 
    monetary amounts, locations, and legal terms within contract documents.
    Supports contract analysis by providing structured entity information.
    
    AI Context: This service handles all entity recognition tasks. When debugging
    entity-related issues, start here. The service uses pattern-based extraction
    combined with contextual analysis for legal domain accuracy.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize entity extraction service.
        
        Args:
            config: Configuration for entity extraction parameters
        """
        self.config = config or {}
        self._entity_patterns = self._initialize_entity_patterns()
        self._confidence_thresholds = self._initialize_confidence_thresholds()
        
    def extract_entities(self, text: str) -> List[ExtractedEntity]:
        """
        Extract all entities from contract text.
        
        Purpose: Performs comprehensive entity extraction including parties,
        dates, monetary amounts, legal terms, and contract-specific entities.
        
        Args:
            text: Contract text to analyze
        
        Returns:
            List[ExtractedEntity]: Extracted entities with metadata
        
        Raises:
            EntityExtractionError: If extraction process fails
        
        AI Context: Primary entity extraction function. Uses pattern-based
        matching with legal domain specialization. For debugging, check
        pattern definitions and confidence scoring logic.
        """
        try:
            logger.debug(f"Extracting entities from text ({len(text)} characters)")
            
            entities = []
            
            # Extract different entity types
            entities.extend(self._extract_parties(text))
            entities.extend(self._extract_dates(text))
            entities.extend(self._extract_monetary_amounts(text))
            entities.extend(self._extract_legal_terms(text))
            entities.extend(self._extract_locations(text))
            entities.extend(self._extract_durations(text))
            entities.extend(self._extract_percentages(text))
            
            # Sort entities by position in text
            entities.sort(key=lambda e: e.start_position)
            
            # Remove overlapping entities (keep highest confidence)
            entities = self._remove_overlapping_entities(entities)
            
            logger.info(f"Extracted {len(entities)} entities")
            return entities
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            raise EntityExtractionError(f"Entity extraction failed: {str(e)}")
    
    def extract_entities_by_type(self, text: str, entity_type: str) -> List[ExtractedEntity]:
        """
        Extract entities of specific type from text.
        
        Args:
            text: Contract text to analyze
            entity_type: Type of entity to extract (e.g., 'PARTY', 'DATE', 'MONEY')
        
        Returns:
            List[ExtractedEntity]: Entities of specified type
        """
        all_entities = self.extract_entities(text)
        return [entity for entity in all_entities if entity.entity_type == entity_type]
    
    def _extract_parties(self, text: str) -> List[ExtractedEntity]:
        """Extract party/organization entities from contract text."""
        entities = []
        
        # Common party indicators
        party_patterns = [
            r'(?i)\b([A-Z][a-z]+ (?:[A-Z][a-z]+ )*(?:Inc\.?|LLC|Corp\.?|Corporation|Company|Ltd\.?))\b',
            r'(?i)\b([A-Z][A-Z\s&]+(?:Inc\.?|LLC|Corp\.?|Corporation|Company|Ltd\.?))\b',
            r'(?i)(?:party|client|vendor|contractor|supplier|provider):\s*([A-Z][^\n,;]+)',
            r'(?i)between\s+([A-Z][^\n,;(]+?)(?:\s+\(|\s+,|\s+and)',
            r'(?i)and\s+([A-Z][^\n,;(]+?)(?:\s+\(|\s+,|\s*$)'
        ]
        
        for pattern in party_patterns:
            for match in re.finditer(pattern, text):
                entity_text = match.group(1).strip()
                if len(entity_text) > 2 and self._is_valid_party_name(entity_text):
                    entities.append(ExtractedEntity(
                        entity_type='PARTY',
                        text=entity_text,
                        confidence=self._calculate_party_confidence(entity_text, text),
                        start_position=match.start(1),
                        end_position=match.end(1),
                        context=self._get_context(text, match.start(), match.end()),
                        metadata={'pattern_matched': pattern}
                    ))
        
        return entities
    
    def _extract_dates(self, text: str) -> List[ExtractedEntity]:
        """Extract date entities from contract text."""
        entities = []
        
        date_patterns = [
            r'\b(\d{1,2}/\d{1,2}/\d{4})\b',  # MM/DD/YYYY
            r'\b(\d{4}-\d{2}-\d{2})\b',      # YYYY-MM-DD
            r'\b([A-Z][a-z]+ \d{1,2},? \d{4})\b',  # Month DD, YYYY
            r'\b(\d{1,2} [A-Z][a-z]+ \d{4})\b',    # DD Month YYYY
            r'\b([A-Z][a-z]+ \d{4})\b'       # Month YYYY
        ]
        
        for pattern in date_patterns:
            for match in re.finditer(pattern, text):
                entity_text = match.group(1)
                confidence = self._calculate_date_confidence(entity_text)
                
                if confidence >= self._confidence_thresholds.get('date', 0.5):
                    entities.append(ExtractedEntity(
                        entity_type='DATE',
                        text=entity_text,
                        confidence=confidence,
                        start_position=match.start(1),
                        end_position=match.end(1),
                        context=self._get_context(text, match.start(), match.end()),
                        metadata={'pattern_matched': pattern}
                    ))
        
        return entities
    
    def _extract_monetary_amounts(self, text: str) -> List[ExtractedEntity]:
        """Extract monetary amount entities from contract text."""
        entities = []
        
        money_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b',  # $1,000.00
            r'\b(\d{1,3}(?:,\d{3})*(?:\.\d{2})?) dollars?\b',  # 1,000.00 dollars
            r'\$(\d+(?:\.\d{2})?)\s*(?:million|thousand|billion)',  # $1.5 million
            r'(?:USD|EUR|GBP|CAD)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'  # USD 1,000.00
        ]
        
        for pattern in money_patterns:
            for match in re.finditer(pattern, text):
                entity_text = match.group(0)
                amount = match.group(1)
                
                entities.append(ExtractedEntity(
                    entity_type='MONEY',
                    text=entity_text,
                    confidence=self._calculate_money_confidence(entity_text),
                    start_position=match.start(),
                    end_position=match.end(),
                    context=self._get_context(text, match.start(), match.end()),
                    metadata={'amount': amount, 'pattern_matched': pattern}
                ))
        
        return entities
    
    def _extract_legal_terms(self, text: str) -> List[ExtractedEntity]:
        """Extract legal terminology entities from contract text."""
        entities = []
        
        legal_terms = [
            'liability', 'indemnification', 'breach', 'termination', 'amendment',
            'confidentiality', 'non-disclosure', 'intellectual property', 'warranties',
            'representations', 'covenant', 'jurisdiction', 'arbitration', 'mediation',
            'force majeure', 'assignment', 'novation', 'severability', 'waiver'
        ]
        
        for term in legal_terms:
            pattern = rf'\b({re.escape(term)})\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(ExtractedEntity(
                    entity_type='LEGAL_TERM',
                    text=match.group(1),
                    confidence=0.8,  # Legal terms have high confidence
                    start_position=match.start(1),
                    end_position=match.end(1),
                    context=self._get_context(text, match.start(), match.end()),
                    metadata={'term_category': 'legal'}
                ))
        
        return entities
    
    def _extract_locations(self, text: str) -> List[ExtractedEntity]:
        """Extract location entities from contract text."""
        entities = []
        
        # State abbreviations and full names
        us_states = [
            'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
            'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
            'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
            'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
            'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
            'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
            'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
            'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
            'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
            'West Virginia', 'Wisconsin', 'Wyoming'
        ]
        
        for state in us_states:
            pattern = rf'\b({re.escape(state)})\b'
            for match in re.finditer(pattern, text):
                entities.append(ExtractedEntity(
                    entity_type='LOCATION',
                    text=match.group(1),
                    confidence=0.7,
                    start_position=match.start(1),
                    end_position=match.end(1),
                    context=self._get_context(text, match.start(), match.end()),
                    metadata={'location_type': 'state'}
                ))
        
        return entities
    
    def _extract_durations(self, text: str) -> List[ExtractedEntity]:
        """Extract duration/time period entities from contract text."""
        entities = []
        
        duration_patterns = [
            r'\b(\d+)\s+(days?|weeks?|months?|years?)\b',
            r'\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+(days?|weeks?|months?|years?)\b',
            r'\b(\d+)-(?:day|week|month|year)\b'
        ]
        
        for pattern in duration_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(ExtractedEntity(
                    entity_type='DURATION',
                    text=match.group(0),
                    confidence=0.8,
                    start_position=match.start(),
                    end_position=match.end(),
                    context=self._get_context(text, match.start(), match.end()),
                    metadata={'pattern_matched': pattern}
                ))
        
        return entities
    
    def _extract_percentages(self, text: str) -> List[ExtractedEntity]:
        """Extract percentage entities from contract text."""
        entities = []
        
        percentage_patterns = [
            r'\b(\d+(?:\.\d+)?%)\b',
            r'\b(\d+(?:\.\d+)?) percent\b'
        ]
        
        for pattern in percentage_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(ExtractedEntity(
                    entity_type='PERCENTAGE',
                    text=match.group(0),
                    confidence=0.9,
                    start_position=match.start(),
                    end_position=match.end(),
                    context=self._get_context(text, match.start(), match.end()),
                    metadata={'pattern_matched': pattern}
                ))
        
        return entities
    
    def _is_valid_party_name(self, name: str) -> bool:
        """Validate if extracted text is likely a valid party name."""
        # Filter out common false positives
        invalid_terms = {'the', 'and', 'or', 'to', 'of', 'in', 'for', 'with', 'by'}
        words = name.lower().split()
        
        if len(words) < 1:
            return False
        
        # Check if it's just common words
        if all(word in invalid_terms for word in words):
            return False
        
        # Must contain at least one capitalized word or company indicator
        has_capital = any(word[0].isupper() for word in words if word)
        has_company_indicator = any(indicator in name.lower() for indicator in 
                                   ['inc', 'llc', 'corp', 'company', 'ltd'])
        
        return has_capital or has_company_indicator
    
    def _calculate_party_confidence(self, party_name: str, full_text: str) -> float:
        """Calculate confidence score for party name extraction."""
        confidence = 0.5  # Base confidence
        
        # Boost confidence for company indicators
        company_indicators = ['inc.', 'llc', 'corp.', 'corporation', 'company', 'ltd.']
        if any(indicator in party_name.lower() for indicator in company_indicators):
            confidence += 0.3
        
        # Boost confidence if appears multiple times
        occurrences = full_text.lower().count(party_name.lower())
        if occurrences > 1:
            confidence += min(0.2, occurrences * 0.05)
        
        # Boost confidence if in typical party context
        context_indicators = ['between', 'party', 'client', 'vendor', 'contractor']
        party_context = self._get_context(full_text, 
                                         full_text.find(party_name), 
                                         full_text.find(party_name) + len(party_name))
        
        if any(indicator in party_context.lower() for indicator in context_indicators):
            confidence += 0.2
        
        return min(1.0, confidence)
    
    def _calculate_date_confidence(self, date_text: str) -> float:
        """Calculate confidence score for date extraction."""
        confidence = 0.6  # Base confidence for dates
        
        # Higher confidence for standard formats
        if re.match(r'\d{1,2}/\d{1,2}/\d{4}', date_text):
            confidence = 0.9
        elif re.match(r'\d{4}-\d{2}-\d{2}', date_text):
            confidence = 0.9
        elif re.match(r'[A-Z][a-z]+ \d{1,2},? \d{4}', date_text):
            confidence = 0.8
        
        return confidence
    
    def _calculate_money_confidence(self, money_text: str) -> float:
        """Calculate confidence score for monetary amount extraction."""
        confidence = 0.8  # Monetary patterns are usually reliable
        
        # Higher confidence for currency symbols
        if money_text.startswith('$'):
            confidence = 0.9
        
        # Higher confidence for explicit currency codes
        if re.search(r'\b(USD|EUR|GBP|CAD)\b', money_text):
            confidence = 0.9
        
        return confidence
    
    def _get_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Extract context around entity position."""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()
    
    def _remove_overlapping_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Remove overlapping entities, keeping those with higher confidence."""
        if not entities:
            return entities
        
        # Sort by start position, then by confidence (descending)
        sorted_entities = sorted(entities, key=lambda e: (e.start_position, -e.confidence))
        
        filtered_entities = []
        last_end = -1
        
        for entity in sorted_entities:
            # If this entity doesn't overlap with the previous one
            if entity.start_position >= last_end:
                filtered_entities.append(entity)
                last_end = entity.end_position
            else:
                # If this entity has higher confidence, replace the previous one
                if filtered_entities and entity.confidence > filtered_entities[-1].confidence:
                    filtered_entities[-1] = entity
                    last_end = entity.end_position
        
        return filtered_entities
    
    def _initialize_entity_patterns(self) -> Dict[str, List[str]]:
        """Initialize regex patterns for different entity types."""
        return {
            'party': [
                r'(?i)\b([A-Z][a-z]+ (?:[A-Z][a-z]+ )*(?:Inc\.?|LLC|Corp\.?|Corporation|Company|Ltd\.?))\b',
                r'(?i)(?:party|client|vendor|contractor):\s*([A-Z][^\n,;]+)'
            ],
            'date': [
                r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
                r'\b([A-Z][a-z]+ \d{1,2},? \d{4})\b'
            ],
            'money': [
                r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b',
                r'\b(\d{1,3}(?:,\d{3})*(?:\.\d{2})?) dollars?\b'
            ]
        }
    
    def _initialize_confidence_thresholds(self) -> Dict[str, float]:
        """Initialize confidence thresholds for different entity types."""
        return {
            'party': 0.6,
            'date': 0.5,
            'money': 0.7,
            'legal_term': 0.8,
            'location': 0.7,
            'duration': 0.6,
            'percentage': 0.8
        }


class EntityExtractionError(Exception):
    """Exception raised when entity extraction fails."""
    pass
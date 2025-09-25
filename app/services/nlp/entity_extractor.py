"""
Named Entity Recognition and Extraction for Legal Documents

Specialized entity extraction for contract analysis including parties,
dates, monetary amounts, legal terms, and obligations.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Represents an extracted entity"""
    text: str
    entity_type: str
    start_pos: int
    end_pos: int
    confidence: float
    metadata: Dict[str, Any]


@dataclass
class EntityExtractionResult:
    """Container for entity extraction results"""
    entities: List[Entity]
    entity_counts: Dict[str, int]
    extraction_metadata: Dict[str, Any]


class EntityExtractor:
    """
    Specialized entity extractor for legal documents and contracts.
    
    Extracts key entities relevant to contract analysis including:
    - Legal parties (organizations, individuals)
    - Financial amounts and terms
    - Dates and deadlines
    - Legal obligations and requirements
    - Contract-specific terminology
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize entity extractor
        
        Args:
            config: Configuration for extraction parameters
        """
        self.config = config or {}
        
        # Initialize extraction patterns
        self.patterns = self._initialize_extraction_patterns()
        
        # Entity type priorities for conflict resolution
        self.entity_priorities = {
            'MONEY': 10,
            'DATE': 9,
            'ORGANIZATION': 8,
            'PERSON': 8,
            'LEGAL_OBLIGATION': 7,
            'CONTRACT_TERM': 6,
            'ADDRESS': 5,
            'PERCENTAGE': 4,
            'DURATION': 3
        }
        
        logger.info("EntityExtractor initialized with legal document patterns")
    
    def extract_entities(self, text: str) -> EntityExtractionResult:
        """
        Extract entities from contract text
        
        Args:
            text: Contract text to analyze
            
        Returns:
            EntityExtractionResult containing found entities
        """
        try:
            logger.debug(f"Extracting entities from {len(text)} characters of text")
            
            entities = []
            
            # Extract each entity type
            for entity_type, extractors in self.patterns.items():
                type_entities = self._extract_entity_type(text, entity_type, extractors)
                entities.extend(type_entities)
            
            # Resolve overlapping entities
            entities = self._resolve_overlaps(entities)
            
            # Calculate entity counts
            entity_counts = {}
            for entity in entities:
                entity_counts[entity.entity_type] = entity_counts.get(entity.entity_type, 0) + 1
            
            # Generate extraction metadata
            extraction_metadata = {
                'total_entities': len(entities),
                'text_length': len(text),
                'extraction_timestamp': datetime.now().isoformat(),
                'entity_types_found': list(entity_counts.keys()),
                'extraction_confidence': self._calculate_overall_confidence(entities)
            }
            
            logger.info(f"Extracted {len(entities)} entities of {len(entity_counts)} types")
            
            return EntityExtractionResult(
                entities=entities,
                entity_counts=entity_counts,
                extraction_metadata=extraction_metadata
            )
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {str(e)}")
            return EntityExtractionResult(
                entities=[],
                entity_counts={},
                extraction_metadata={'error': str(e)}
            )
    
    def extract_contract_parties(self, text: str) -> List[Entity]:
        """Extract contract parties (organizations and individuals)"""
        parties = []
        
        # Organization patterns
        org_patterns = [
            r'\b[A-Z][a-zA-Z\s&,.-]+(?:Corporation|Corp\.?|Inc\.?|LLC|Ltd\.?|Limited|Company|Co\.?|LP|LLP)\b',
            r'\b[A-Z][a-zA-Z\s&,.-]+(?:Holdings?|Group|Enterprises?|Solutions?|Systems?|Technologies?)\b'
        ]
        
        for pattern in org_patterns:
            for match in re.finditer(pattern, text):
                parties.append(Entity(
                    text=match.group().strip(),
                    entity_type='ORGANIZATION',
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.8,
                    metadata={'pattern_type': 'organization'}
                ))
        
        # Person patterns (simple heuristic)
        person_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b'
        for match in re.finditer(person_pattern, text):
            # Skip if it looks like an organization
            match_text = match.group()
            if not any(org_word in match_text for org_word in ['Corp', 'Inc', 'LLC', 'Ltd', 'Company']):
                parties.append(Entity(
                    text=match_text,
                    entity_type='PERSON',
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.6,
                    metadata={'pattern_type': 'person_name'}
                ))
        
        return parties
    
    def extract_financial_terms(self, text: str) -> List[Entity]:
        """Extract financial amounts and terms"""
        financial_entities = []
        
        # Money amounts
        money_patterns = [
            r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand|M|B|K))?',
            r'(?:USD|US\$|dollars?)\s*[\d,]+(?:\.\d{2})?',
            r'[\d,]+(?:\.\d{2})?\s*dollars?'
        ]
        
        for pattern in money_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Extract numeric value for metadata
                numeric_value = self._extract_numeric_value(match.group())
                
                financial_entities.append(Entity(
                    text=match.group(),
                    entity_type='MONEY',
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.9,
                    metadata={
                        'numeric_value': numeric_value,
                        'currency': 'USD'
                    }
                ))
        
        # Percentages
        percentage_pattern = r'\b\d+(?:\.\d+)?%|\b\d+(?:\.\d+)?\s*percent'
        for match in re.finditer(percentage_pattern, text, re.IGNORECASE):
            percentage_value = float(re.search(r'\d+(?:\.\d+)?', match.group()).group())
            
            financial_entities.append(Entity(
                text=match.group(),
                entity_type='PERCENTAGE',
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=0.85,
                metadata={'percentage_value': percentage_value}
            ))
        
        return financial_entities
    
    def extract_dates_and_deadlines(self, text: str) -> List[Entity]:
        """Extract dates, deadlines, and time periods"""
        temporal_entities = []
        
        # Date patterns
        date_patterns = [
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
            r'\b\d{1,2}/\d{1,2}/\d{4}',
            r'\b\d{4}-\d{2}-\d{2}',
            r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}'
        ]
        
        for pattern in date_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                temporal_entities.append(Entity(
                    text=match.group(),
                    entity_type='DATE',
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.9,
                    metadata={'date_format': 'explicit_date'}
                ))
        
        # Duration patterns
        duration_patterns = [
            r'\b\d+\s*(?:days?|weeks?|months?|years?)\b',
            r'\bwithin\s+\d+\s*(?:days?|weeks?|months?|years?)\b'
        ]
        
        for pattern in duration_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                temporal_entities.append(Entity(
                    text=match.group(),
                    entity_type='DURATION',
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.8,
                    metadata={'duration_type': 'time_period'}
                ))
        
        return temporal_entities
    
    def extract_legal_obligations(self, text: str) -> List[Entity]:
        """Extract legal obligations and requirements"""
        obligations = []
        
        # Obligation patterns with modal verbs
        obligation_patterns = [
            r'\b(?:shall|must|will|agrees? to|required to|obligated to)\s+[^.]+',
            r'\b(?:Party|Contractor|Provider|Client|Customer)\s+(?:shall|must|will)\s+[^.]+',
            r'\b(?:is|are)\s+required\s+to\s+[^.]+',
            r'\b(?:covenant|undertake)s?\s+to\s+[^.]+'
        ]
        
        for pattern in obligation_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Limit length to avoid overly long extractions
                obligation_text = match.group()[:200]
                if obligation_text.endswith('...') is False and len(match.group()) > 200:
                    obligation_text += '...'
                
                obligations.append(Entity(
                    text=obligation_text,
                    entity_type='LEGAL_OBLIGATION',
                    start_pos=match.start(),
                    end_pos=match.start() + len(obligation_text),
                    confidence=0.7,
                    metadata={'obligation_type': 'modal_requirement'}
                ))
        
        return obligations
    
    def _extract_entity_type(
        self, 
        text: str, 
        entity_type: str, 
        extractors: List[Dict[str, Any]]
    ) -> List[Entity]:
        """Extract entities of a specific type using configured extractors"""
        entities = []
        
        for extractor in extractors:
            pattern = extractor['pattern']
            confidence = extractor.get('confidence', 0.5)
            metadata = extractor.get('metadata', {})
            
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entity = Entity(
                    text=match.group(),
                    entity_type=entity_type,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=confidence,
                    metadata=metadata
                )
                entities.append(entity)
        
        return entities
    
    def _resolve_overlaps(self, entities: List[Entity]) -> List[Entity]:
        """Resolve overlapping entities by priority and confidence"""
        if not entities:
            return entities
        
        # Sort by start position
        entities.sort(key=lambda e: e.start_pos)
        
        resolved = []
        i = 0
        
        while i < len(entities):
            current = entities[i]
            overlapping = [current]
            
            # Find all overlapping entities
            j = i + 1
            while j < len(entities) and entities[j].start_pos < current.end_pos:
                overlapping.append(entities[j])
                j += 1
            
            if len(overlapping) == 1:
                resolved.append(current)
            else:
                # Choose best entity based on priority and confidence
                best_entity = self._choose_best_entity(overlapping)
                resolved.append(best_entity)
            
            i = j if j > i + 1 else i + 1
        
        return resolved
    
    def _choose_best_entity(self, overlapping_entities: List[Entity]) -> Entity:
        """Choose the best entity from overlapping candidates"""
        def score_entity(entity):
            priority = self.entity_priorities.get(entity.entity_type, 1)
            return priority * entity.confidence
        
        return max(overlapping_entities, key=score_entity)
    
    def _calculate_overall_confidence(self, entities: List[Entity]) -> float:
        """Calculate overall confidence of entity extraction"""
        if not entities:
            return 0.0
        
        return sum(entity.confidence for entity in entities) / len(entities)
    
    def _extract_numeric_value(self, money_text: str) -> Optional[float]:
        """Extract numeric value from money string"""
        try:
            # Remove currency symbols and words
            clean_text = re.sub(r'[^\d.,]', '', money_text)
            clean_text = clean_text.replace(',', '')
            
            if clean_text:
                value = float(clean_text)
                
                # Handle million/billion multipliers
                if any(word in money_text.lower() for word in ['million', 'm']):
                    value *= 1_000_000
                elif any(word in money_text.lower() for word in ['billion', 'b']):
                    value *= 1_000_000_000
                elif any(word in money_text.lower() for word in ['thousand', 'k']):
                    value *= 1_000
                
                return value
        except (ValueError, AttributeError):
            pass
        
        return None
    
    def _initialize_extraction_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize extraction patterns for different entity types"""
        return {
            'MONEY': [
                {
                    'pattern': r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand|M|B|K))?',
                    'confidence': 0.9,
                    'metadata': {'currency': 'USD', 'pattern_type': 'dollar_amount'}
                },
                {
                    'pattern': r'(?:USD|US\$)\s*[\d,]+(?:\.\d{2})?',
                    'confidence': 0.85,
                    'metadata': {'currency': 'USD', 'pattern_type': 'explicit_usd'}
                }
            ],
            'DATE': [
                {
                    'pattern': r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
                    'confidence': 0.95,
                    'metadata': {'date_format': 'month_day_year'}
                },
                {
                    'pattern': r'\b\d{1,2}/\d{1,2}/\d{4}',
                    'confidence': 0.85,
                    'metadata': {'date_format': 'numeric'}
                }
            ],
            'ORGANIZATION': [
                {
                    'pattern': r'\b[A-Z][a-zA-Z\s&,.-]+(?:Corporation|Corp\.?|Inc\.?|LLC|Ltd\.?|Company|Co\.?)\b',
                    'confidence': 0.8,
                    'metadata': {'org_type': 'corporation'}
                }
            ],
            'CONTRACT_TERM': [
                {
                    'pattern': r'\b(?:force majeure|intellectual property|confidentiality|indemnification|termination)\b',
                    'confidence': 0.7,
                    'metadata': {'term_type': 'legal_concept'}
                }
            ],
            'ADDRESS': [
                {
                    'pattern': r'\d+\s+[A-Z][a-zA-Z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Place|Pl)',
                    'confidence': 0.75,
                    'metadata': {'address_type': 'street_address'}
                }
            ]
        }
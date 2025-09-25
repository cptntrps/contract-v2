"""
Contract Clause Classification and Analysis

Classifies and analyzes different types of contract clauses using
pattern matching and legal domain expertise.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ClauseMatch:
    """Represents a matched clause in the contract"""
    clause_type: str
    text: str
    start_pos: int
    end_pos: int
    confidence: float
    metadata: Dict[str, Any]
    patterns_matched: List[str]
    risk_level: str


@dataclass
class ClauseAnalysisResult:
    """Container for clause analysis results"""
    clauses: List[ClauseMatch]
    clause_counts: Dict[str, int]
    missing_clauses: List[str]
    risk_summary: Dict[str, Any]
    analysis_metadata: Dict[str, Any]


class ClauseClassifier:
    """
    Contract clause classifier for legal document analysis.
    
    Identifies and classifies different types of contract clauses
    including payment terms, liability clauses, termination conditions,
    and other legal provisions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize clause classifier
        
        Args:
            config: Configuration for classification parameters
        """
        self.config = config or {}
        
        # Initialize clause patterns and definitions
        self.clause_patterns = self._initialize_clause_patterns()
        self.clause_definitions = self._initialize_clause_definitions()
        self.standard_clauses = self._initialize_standard_clauses()
        
        # Risk assessment weights
        self.risk_weights = {
            'liability': 0.9,
            'termination': 0.8,
            'indemnification': 0.8,
            'confidentiality': 0.7,
            'intellectual_property': 0.7,
            'payment_terms': 0.6,
            'force_majeure': 0.4,
            'governing_law': 0.3
        }
        
        logger.info("ClauseClassifier initialized with legal clause patterns")
    
    def classify_clauses(self, text: str) -> ClauseAnalysisResult:
        """
        Classify and analyze contract clauses
        
        Args:
            text: Contract text to analyze
            
        Returns:
            ClauseAnalysisResult containing classified clauses and analysis
        """
        try:
            logger.debug(f"Classifying clauses in {len(text)} characters of text")
            
            clauses = []
            
            # Identify clauses by type
            for clause_type, patterns in self.clause_patterns.items():
                type_clauses = self._find_clauses_of_type(text, clause_type, patterns)
                clauses.extend(type_clauses)
            
            # Remove overlapping clauses
            clauses = self._resolve_clause_overlaps(clauses)
            
            # Calculate clause counts
            clause_counts = {}
            for clause in clauses:
                clause_counts[clause.clause_type] = clause_counts.get(clause.clause_type, 0) + 1
            
            # Identify missing standard clauses
            missing_clauses = self._identify_missing_clauses(clause_counts)
            
            # Generate risk summary
            risk_summary = self._generate_risk_summary(clauses)
            
            # Create analysis metadata
            analysis_metadata = {
                'total_clauses': len(clauses),
                'clause_types_found': len(clause_counts),
                'text_length': len(text),
                'analysis_timestamp': datetime.now().isoformat(),
                'missing_critical_clauses': len([c for c in missing_clauses if c in ['liability', 'termination', 'confidentiality']]),
                'high_risk_clauses': len([c for c in clauses if c.risk_level == 'HIGH'])
            }
            
            logger.info(f"Classified {len(clauses)} clauses of {len(clause_counts)} types")
            
            return ClauseAnalysisResult(
                clauses=clauses,
                clause_counts=clause_counts,
                missing_clauses=missing_clauses,
                risk_summary=risk_summary,
                analysis_metadata=analysis_metadata
            )
            
        except Exception as e:
            logger.error(f"Clause classification failed: {str(e)}")
            return ClauseAnalysisResult(
                clauses=[],
                clause_counts={},
                missing_clauses=[],
                risk_summary={'error': str(e)},
                analysis_metadata={'error': str(e)}
            )
    
    def _find_clauses_of_type(
        self, 
        text: str, 
        clause_type: str, 
        patterns: List[Dict[str, Any]]
    ) -> List[ClauseMatch]:
        """Find clauses of a specific type using patterns"""
        clauses = []
        
        for pattern_config in patterns:
            pattern = pattern_config['pattern']
            confidence = pattern_config.get('confidence', 0.5)
            metadata = pattern_config.get('metadata', {})
            
            # Find pattern matches
            for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
                # Extract surrounding context for better clause identification
                context_start = max(0, match.start() - 100)
                context_end = min(len(text), match.end() + 100)
                context_text = text[context_start:context_end]
                
                # Assess risk level for this clause
                risk_level = self._assess_clause_risk(clause_type, match.group(), context_text)
                
                clause = ClauseMatch(
                    clause_type=clause_type,
                    text=match.group(),
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=confidence,
                    metadata={
                        **metadata,
                        'context': context_text,
                        'pattern_matched': pattern
                    },
                    patterns_matched=[pattern],
                    risk_level=risk_level
                )
                
                clauses.append(clause)
        
        return clauses
    
    def _resolve_clause_overlaps(self, clauses: List[ClauseMatch]) -> List[ClauseMatch]:
        """Resolve overlapping clause matches"""
        if not clauses:
            return clauses
        
        # Sort by start position
        clauses.sort(key=lambda c: c.start_pos)
        
        resolved = []
        i = 0
        
        while i < len(clauses):
            current = clauses[i]
            overlapping = [current]
            
            # Find all overlapping clauses
            j = i + 1
            while j < len(clauses) and clauses[j].start_pos < current.end_pos:
                overlapping.append(clauses[j])
                j += 1
            
            if len(overlapping) == 1:
                resolved.append(current)
            else:
                # Choose best clause based on confidence and risk importance
                best_clause = self._choose_best_clause(overlapping)
                resolved.append(best_clause)
            
            i = j if j > i + 1 else i + 1
        
        return resolved
    
    def _choose_best_clause(self, overlapping_clauses: List[ClauseMatch]) -> ClauseMatch:
        """Choose the best clause from overlapping matches"""
        def score_clause(clause):
            # Priority based on risk level and confidence
            risk_multiplier = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}.get(clause.risk_level, 1)
            type_weight = self.risk_weights.get(clause.clause_type, 0.5)
            return clause.confidence * risk_multiplier * type_weight
        
        return max(overlapping_clauses, key=score_clause)
    
    def _assess_clause_risk(self, clause_type: str, clause_text: str, context: str) -> str:
        """Assess risk level of a clause"""
        text_lower = clause_text.lower()
        context_lower = context.lower()
        
        # High risk indicators
        high_risk_terms = [
            'unlimited liability', 'personal guarantee', 'liquidated damages',
            'immediate termination', 'no liability', 'as is', 'without warranty',
            'indemnify against all', 'hold harmless from any'
        ]
        
        if any(term in text_lower for term in high_risk_terms):
            return 'HIGH'
        
        # Clause-specific risk assessment
        if clause_type == 'liability':
            if any(term in text_lower for term in ['limit', 'cap', 'exclude']):
                return 'MEDIUM'
            if 'unlimited' in text_lower:
                return 'HIGH'
        
        elif clause_type == 'termination':
            if any(term in text_lower for term in ['immediate', 'without notice', 'at will']):
                return 'HIGH'
            if any(term in text_lower for term in ['30 days', 'notice period']):
                return 'MEDIUM'
        
        elif clause_type == 'payment_terms':
            if any(term in text_lower for term in ['penalty', 'interest', 'late fee']):
                return 'HIGH'
        
        # Medium risk indicators
        medium_risk_terms = [
            'breach', 'default', 'penalty', 'damages', 'forfeit',
            'suspend', 'terminate', 'cancel'
        ]
        
        if any(term in text_lower for term in medium_risk_terms):
            return 'MEDIUM'
        
        return 'LOW'
    
    def _identify_missing_clauses(self, found_clause_counts: Dict[str, int]) -> List[str]:
        """Identify standard clauses that are missing from the contract"""
        missing = []
        
        for standard_clause in self.standard_clauses:
            if standard_clause not in found_clause_counts:
                missing.append(standard_clause)
        
        return missing
    
    def _generate_risk_summary(self, clauses: List[ClauseMatch]) -> Dict[str, Any]:
        """Generate risk summary from classified clauses"""
        risk_summary = {
            'overall_risk': 'LOW',
            'high_risk_clauses': [],
            'missing_protections': [],
            'recommendations': []
        }
        
        high_risk_clauses = [c for c in clauses if c.risk_level == 'HIGH']
        medium_risk_clauses = [c for c in clauses if c.risk_level == 'MEDIUM']
        
        # Determine overall risk
        if len(high_risk_clauses) > 0:
            risk_summary['overall_risk'] = 'HIGH'
        elif len(medium_risk_clauses) > 2:
            risk_summary['overall_risk'] = 'MEDIUM'
        
        # Document high risk clauses
        risk_summary['high_risk_clauses'] = [
            {
                'type': clause.clause_type,
                'text_preview': clause.text[:100] + '...' if len(clause.text) > 100 else clause.text,
                'reason': f"{clause.clause_type} clause with high risk indicators"
            }
            for clause in high_risk_clauses
        ]
        
        # Identify missing protections
        clause_types = {c.clause_type for c in clauses}
        critical_protections = ['liability', 'indemnification', 'confidentiality', 'termination']
        
        for protection in critical_protections:
            if protection not in clause_types:
                risk_summary['missing_protections'].append(protection)
        
        # Generate recommendations
        recommendations = []
        
        if high_risk_clauses:
            recommendations.append("Review high-risk clauses with legal counsel")
        
        if risk_summary['missing_protections']:
            recommendations.append(f"Consider adding missing protections: {', '.join(risk_summary['missing_protections'])}")
        
        if any(c.clause_type == 'liability' and 'unlimited' in c.text.lower() for c in clauses):
            recommendations.append("Negotiate liability limitations to reduce exposure")
        
        risk_summary['recommendations'] = recommendations
        
        return risk_summary
    
    def _initialize_clause_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize clause identification patterns"""
        return {
            'payment_terms': [
                {
                    'pattern': r'payment\s+(?:shall\s+be\s+)?(?:due|made|payable).*?(?:\.|;|\n)',
                    'confidence': 0.8,
                    'metadata': {'category': 'financial'}
                },
                {
                    'pattern': r'(?:net\s+)?\d+\s+days?.*?payment',
                    'confidence': 0.9,
                    'metadata': {'category': 'financial', 'type': 'payment_terms'}
                }
            ],
            
            'liability': [
                {
                    'pattern': r'liability.*?(?:limited|unlimited|excluded|disclaimed).*?(?:\.|;|\n)',
                    'confidence': 0.85,
                    'metadata': {'category': 'risk'}
                },
                {
                    'pattern': r'in\s+no\s+event.*?liable.*?(?:\.|;|\n)',
                    'confidence': 0.9,
                    'metadata': {'category': 'risk', 'type': 'limitation'}
                }
            ],
            
            'termination': [
                {
                    'pattern': r'(?:this\s+agreement|contract).*?(?:terminate|end|expire).*?(?:\.|;|\n)',
                    'confidence': 0.8,
                    'metadata': {'category': 'duration'}
                },
                {
                    'pattern': r'upon.*?(?:breach|default|violation).*?terminate.*?(?:\.|;|\n)',
                    'confidence': 0.9,
                    'metadata': {'category': 'duration', 'trigger': 'breach'}
                }
            ],
            
            'indemnification': [
                {
                    'pattern': r'indemnify.*?(?:hold\s+harmless|defend).*?(?:\.|;|\n)',
                    'confidence': 0.9,
                    'metadata': {'category': 'protection'}
                },
                {
                    'pattern': r'(?:defend|hold\s+harmless).*?indemnify.*?(?:\.|;|\n)',
                    'confidence': 0.85,
                    'metadata': {'category': 'protection'}
                }
            ],
            
            'confidentiality': [
                {
                    'pattern': r'confidential.*?(?:information|data|material).*?(?:\.|;|\n)',
                    'confidence': 0.8,
                    'metadata': {'category': 'information'}
                },
                {
                    'pattern': r'non-disclosure.*?(?:agreement|obligation).*?(?:\.|;|\n)',
                    'confidence': 0.9,
                    'metadata': {'category': 'information', 'type': 'nda'}
                }
            ],
            
            'intellectual_property': [
                {
                    'pattern': r'intellectual\s+property.*?(?:rights|ownership).*?(?:\.|;|\n)',
                    'confidence': 0.85,
                    'metadata': {'category': 'ip'}
                },
                {
                    'pattern': r'copyright.*?(?:patent|trademark|trade\s+secret).*?(?:\.|;|\n)',
                    'confidence': 0.8,
                    'metadata': {'category': 'ip'}
                }
            ],
            
            'force_majeure': [
                {
                    'pattern': r'force\s+majeure.*?(?:event|circumstance).*?(?:\.|;|\n)',
                    'confidence': 0.95,
                    'metadata': {'category': 'risk_mitigation'}
                },
                {
                    'pattern': r'act\s+of\s+(?:god|nature).*?(?:beyond.*?control|unforeseeable).*?(?:\.|;|\n)',
                    'confidence': 0.7,
                    'metadata': {'category': 'risk_mitigation'}
                }
            ],
            
            'governing_law': [
                {
                    'pattern': r'governed\s+by.*?laws?\s+of.*?(?:\.|;|\n)',
                    'confidence': 0.9,
                    'metadata': {'category': 'jurisdiction'}
                },
                {
                    'pattern': r'jurisdiction.*?courts?\s+of.*?(?:\.|;|\n)',
                    'confidence': 0.85,
                    'metadata': {'category': 'jurisdiction'}
                }
            ]
        }
    
    def _initialize_clause_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Initialize clause definitions and descriptions"""
        return {
            'payment_terms': {
                'description': 'Clauses defining payment obligations, timing, and methods',
                'importance': 'high',
                'typical_content': ['payment due dates', 'payment methods', 'late payment penalties']
            },
            'liability': {
                'description': 'Clauses limiting or defining liability exposure',
                'importance': 'critical',
                'typical_content': ['liability caps', 'exclusions', 'limitation of damages']
            },
            'termination': {
                'description': 'Clauses defining how and when the contract can be terminated',
                'importance': 'high',
                'typical_content': ['termination triggers', 'notice requirements', 'post-termination obligations']
            },
            'indemnification': {
                'description': 'Clauses requiring one party to protect another from certain risks',
                'importance': 'critical',
                'typical_content': ['indemnification scope', 'defense obligations', 'hold harmless provisions']
            },
            'confidentiality': {
                'description': 'Clauses protecting confidential information',
                'importance': 'high',
                'typical_content': ['confidentiality obligations', 'information protection', 'non-disclosure requirements']
            },
            'intellectual_property': {
                'description': 'Clauses defining IP ownership and usage rights',
                'importance': 'high',
                'typical_content': ['IP ownership', 'license grants', 'IP indemnification']
            },
            'force_majeure': {
                'description': 'Clauses excusing performance due to extraordinary circumstances',
                'importance': 'medium',
                'typical_content': ['force majeure events', 'notice requirements', 'mitigation obligations']
            },
            'governing_law': {
                'description': 'Clauses specifying applicable law and jurisdiction',
                'importance': 'medium',
                'typical_content': ['governing law', 'jurisdiction', 'dispute resolution venue']
            }
        }
    
    def _initialize_standard_clauses(self) -> List[str]:
        """Initialize list of standard clauses expected in most contracts"""
        return [
            'payment_terms',
            'liability',
            'termination',
            'confidentiality',
            'governing_law'
        ]
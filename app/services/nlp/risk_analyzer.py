"""
Contract Risk Analysis Engine

Comprehensive risk assessment for contract changes and terms using
pattern recognition and legal domain expertise.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import Counter, defaultdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskCategory(Enum):
    """Risk category enumeration"""
    FINANCIAL = "financial"
    LEGAL = "legal"
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    REPUTATIONAL = "reputational"


@dataclass
class RiskIndicator:
    """Individual risk indicator found in text"""
    risk_type: str
    risk_level: RiskLevel
    risk_category: RiskCategory
    description: str
    evidence_text: str
    confidence: float
    position: Tuple[int, int]
    mitigation_suggestions: List[str]
    metadata: Dict[str, Any]


@dataclass
class RiskAssessment:
    """Complete risk assessment result"""
    overall_risk_level: RiskLevel
    risk_indicators: List[RiskIndicator]
    risk_summary: Dict[str, Any]
    recommendations: List[str]
    risk_scores: Dict[str, float]
    analysis_metadata: Dict[str, Any]


class RiskAnalyzer:
    """
    Contract risk analyzer for comprehensive risk assessment.
    
    Identifies and assesses various types of risks in contract terms
    including financial, legal, operational, and compliance risks.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize risk analyzer
        
        Args:
            config: Configuration for risk analysis parameters
        """
        self.config = config or {}
        
        # Initialize risk patterns and rules
        self.risk_patterns = self._initialize_risk_patterns()
        self.risk_rules = self._initialize_risk_rules()
        self.mitigation_strategies = self._initialize_mitigation_strategies()
        
        # Risk scoring weights
        self.category_weights = {
            RiskCategory.FINANCIAL: 1.0,
            RiskCategory.LEGAL: 0.9,
            RiskCategory.OPERATIONAL: 0.7,
            RiskCategory.COMPLIANCE: 0.8,
            RiskCategory.REPUTATIONAL: 0.6
        }
        
        logger.info("RiskAnalyzer initialized with comprehensive risk assessment capabilities")
    
    def analyze_risks(self, text: str, changes: Optional[List[Dict[str, Any]]] = None) -> RiskAssessment:
        """
        Perform comprehensive risk analysis on contract text
        
        Args:
            text: Contract text to analyze
            changes: Optional list of changes to analyze for risk impact
            
        Returns:
            RiskAssessment containing complete risk analysis
        """
        try:
            logger.debug(f"Analyzing risks in {len(text)} characters of text")
            
            risk_indicators = []
            
            # Analyze general contract risks
            general_risks = self._analyze_general_risks(text)
            risk_indicators.extend(general_risks)
            
            # Analyze change-specific risks if changes provided
            if changes:
                change_risks = self._analyze_change_risks(changes, text)
                risk_indicators.extend(change_risks)
            
            # Calculate risk scores by category
            risk_scores = self._calculate_risk_scores(risk_indicators)
            
            # Determine overall risk level
            overall_risk_level = self._determine_overall_risk_level(risk_scores, risk_indicators)
            
            # Generate risk summary
            risk_summary = self._generate_risk_summary(risk_indicators, risk_scores)
            
            # Generate recommendations
            recommendations = self._generate_risk_recommendations(risk_indicators, overall_risk_level)
            
            # Create analysis metadata
            analysis_metadata = {
                'total_risk_indicators': len(risk_indicators),
                'high_risk_indicators': len([r for r in risk_indicators if r.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]),
                'risk_categories_found': len(set(r.risk_category for r in risk_indicators)),
                'analysis_timestamp': datetime.now().isoformat(),
                'text_length': len(text),
                'changes_analyzed': len(changes) if changes else 0
            }
            
            logger.info(f"Risk analysis completed - Overall risk: {overall_risk_level.value}, Indicators: {len(risk_indicators)}")
            
            return RiskAssessment(
                overall_risk_level=overall_risk_level,
                risk_indicators=risk_indicators,
                risk_summary=risk_summary,
                recommendations=recommendations,
                risk_scores=risk_scores,
                analysis_metadata=analysis_metadata
            )
            
        except Exception as e:
            logger.error(f"Risk analysis failed: {str(e)}")
            return RiskAssessment(
                overall_risk_level=RiskLevel.LOW,
                risk_indicators=[],
                risk_summary={'error': str(e)},
                recommendations=['Risk analysis failed - manual review required'],
                risk_scores={},
                analysis_metadata={'error': str(e)}
            )
    
    def _analyze_general_risks(self, text: str) -> List[RiskIndicator]:
        """Analyze general contract risks using pattern matching"""
        risk_indicators = []
        
        for risk_type, patterns in self.risk_patterns.items():
            for pattern_config in patterns:
                pattern = pattern_config['pattern']
                risk_level = RiskLevel(pattern_config['risk_level'])
                risk_category = RiskCategory(pattern_config['risk_category'])
                confidence = pattern_config.get('confidence', 0.7)
                description = pattern_config.get('description', f"{risk_type} risk detected")
                
                # Find pattern matches
                for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
                    # Get surrounding context
                    context_start = max(0, match.start() - 50)
                    context_end = min(len(text), match.end() + 50)
                    evidence_text = text[context_start:context_end].strip()
                    
                    # Get mitigation suggestions
                    mitigation_suggestions = self.mitigation_strategies.get(risk_type, [])
                    
                    risk_indicator = RiskIndicator(
                        risk_type=risk_type,
                        risk_level=risk_level,
                        risk_category=risk_category,
                        description=description,
                        evidence_text=evidence_text,
                        confidence=confidence,
                        position=(match.start(), match.end()),
                        mitigation_suggestions=mitigation_suggestions,
                        metadata={
                            'pattern_matched': pattern,
                            'match_text': match.group()
                        }
                    )
                    
                    risk_indicators.append(risk_indicator)
        
        return risk_indicators
    
    def _analyze_change_risks(self, changes: List[Dict[str, Any]], full_text: str) -> List[RiskIndicator]:
        """Analyze risks specific to contract changes"""
        risk_indicators = []
        
        for change in changes:
            change_text = ""
            if 'deleted_text' in change:
                change_text += change['deleted_text'] + " "
            if 'inserted_text' in change:
                change_text += change['inserted_text']
            
            if not change_text.strip():
                continue
            
            # Assess change-specific risks
            change_risks = self._assess_change_risk_level(change, change_text)
            
            for risk in change_risks:
                risk_indicators.append(risk)
        
        return risk_indicators
    
    def _assess_change_risk_level(self, change: Dict[str, Any], change_text: str) -> List[RiskIndicator]:
        """Assess risk level of a specific change"""
        risks = []
        text_lower = change_text.lower()
        
        # Financial risk indicators
        financial_patterns = [
            (r'\$[\d,]+', RiskLevel.MEDIUM, "Monetary amount changed"),
            (r'payment.*(?:increase|decrease)', RiskLevel.HIGH, "Payment terms modified"),
            (r'penalty.*\$', RiskLevel.HIGH, "Financial penalty introduced"),
            (r'(?:late|interest).*fee', RiskLevel.MEDIUM, "Fee structure changed")
        ]
        
        for pattern, risk_level, description in financial_patterns:
            if re.search(pattern, text_lower):
                risks.append(RiskIndicator(
                    risk_type="financial_change",
                    risk_level=risk_level,
                    risk_category=RiskCategory.FINANCIAL,
                    description=description,
                    evidence_text=change_text[:200],
                    confidence=0.8,
                    position=(0, len(change_text)),
                    mitigation_suggestions=["Review financial impact with finance team", "Verify budget approval"],
                    metadata={'change_id': change.get('id', 'unknown')}
                ))
        
        # Legal risk indicators
        legal_patterns = [
            (r'liability.*unlimited', RiskLevel.CRITICAL, "Unlimited liability exposure"),
            (r'indemnif', RiskLevel.HIGH, "Indemnification obligations changed"),
            (r'termination.*immediate', RiskLevel.HIGH, "Immediate termination clause"),
            (r'breach.*(?:material|significant)', RiskLevel.MEDIUM, "Material breach definition changed")
        ]
        
        for pattern, risk_level, description in legal_patterns:
            if re.search(pattern, text_lower):
                risks.append(RiskIndicator(
                    risk_type="legal_change",
                    risk_level=risk_level,
                    risk_category=RiskCategory.LEGAL,
                    description=description,
                    evidence_text=change_text[:200],
                    confidence=0.9,
                    position=(0, len(change_text)),
                    mitigation_suggestions=["Require legal review", "Consider liability insurance"],
                    metadata={'change_id': change.get('id', 'unknown')}
                ))
        
        # Operational risk indicators
        operational_patterns = [
            (r'deadline.*(?:shortened|reduced)', RiskLevel.HIGH, "Delivery timeline shortened"),
            (r'scope.*(?:expanded|increased)', RiskLevel.MEDIUM, "Scope of work expanded"),
            (r'performance.*standard.*(?:raised|increased)', RiskLevel.MEDIUM, "Performance standards raised")
        ]
        
        for pattern, risk_level, description in operational_patterns:
            if re.search(pattern, text_lower):
                risks.append(RiskIndicator(
                    risk_type="operational_change",
                    risk_level=risk_level,
                    risk_category=RiskCategory.OPERATIONAL,
                    description=description,
                    evidence_text=change_text[:200],
                    confidence=0.7,
                    position=(0, len(change_text)),
                    mitigation_suggestions=["Assess operational capacity", "Review resource allocation"],
                    metadata={'change_id': change.get('id', 'unknown')}
                ))
        
        return risks
    
    def _calculate_risk_scores(self, risk_indicators: List[RiskIndicator]) -> Dict[str, float]:
        """Calculate risk scores by category"""
        category_scores = defaultdict(list)
        
        for indicator in risk_indicators:
            # Convert risk level to numeric score
            level_scores = {
                RiskLevel.LOW: 0.25,
                RiskLevel.MEDIUM: 0.5,
                RiskLevel.HIGH: 0.75,
                RiskLevel.CRITICAL: 1.0
            }
            
            score = level_scores[indicator.risk_level] * indicator.confidence
            category_scores[indicator.risk_category.value].append(score)
        
        # Calculate average scores per category
        risk_scores = {}
        for category, scores in category_scores.items():
            if scores:
                # Use weighted average with higher weight for higher scores
                sorted_scores = sorted(scores, reverse=True)
                weighted_sum = sum(score * (len(sorted_scores) - i) for i, score in enumerate(sorted_scores))
                weight_sum = sum(len(sorted_scores) - i for i in range(len(sorted_scores)))
                risk_scores[category] = weighted_sum / weight_sum if weight_sum > 0 else 0.0
            else:
                risk_scores[category] = 0.0
        
        return risk_scores
    
    def _determine_overall_risk_level(
        self, 
        risk_scores: Dict[str, float], 
        risk_indicators: List[RiskIndicator]
    ) -> RiskLevel:
        """Determine overall risk level based on scores and indicators"""
        
        # Check for critical indicators
        critical_indicators = [r for r in risk_indicators if r.risk_level == RiskLevel.CRITICAL]
        if critical_indicators:
            return RiskLevel.CRITICAL
        
        # Calculate weighted average risk score
        weighted_score = 0.0
        total_weight = 0.0
        
        for category_name, score in risk_scores.items():
            try:
                category = RiskCategory(category_name)
                weight = self.category_weights.get(category, 0.5)
                weighted_score += score * weight
                total_weight += weight
            except ValueError:
                continue
        
        if total_weight == 0:
            return RiskLevel.LOW
        
        avg_risk_score = weighted_score / total_weight
        
        # Convert score to risk level
        if avg_risk_score >= 0.8:
            return RiskLevel.HIGH
        elif avg_risk_score >= 0.5:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_risk_summary(
        self, 
        risk_indicators: List[RiskIndicator], 
        risk_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate comprehensive risk summary"""
        
        # Count indicators by level and category
        level_counts = Counter(indicator.risk_level for indicator in risk_indicators)
        category_counts = Counter(indicator.risk_category for indicator in risk_indicators)
        
        # Identify top risks
        top_risks = sorted(risk_indicators, key=lambda r: (r.risk_level.value, -r.confidence), reverse=True)[:5]
        
        # Calculate risk distribution
        risk_distribution = {}
        for level in RiskLevel:
            risk_distribution[level.value] = level_counts.get(level, 0)
        
        return {
            'risk_distribution': risk_distribution,
            'category_scores': risk_scores,
            'category_counts': {cat.value: count for cat, count in category_counts.items()},
            'top_risks': [
                {
                    'type': risk.risk_type,
                    'level': risk.risk_level.value,
                    'category': risk.risk_category.value,
                    'description': risk.description,
                    'confidence': risk.confidence
                }
                for risk in top_risks
            ],
            'critical_areas': [
                category for category, score in risk_scores.items() if score >= 0.7
            ]
        }
    
    def _generate_risk_recommendations(
        self, 
        risk_indicators: List[RiskIndicator], 
        overall_risk_level: RiskLevel
    ) -> List[str]:
        """Generate risk-based recommendations"""
        recommendations = []
        
        # Overall risk recommendations
        if overall_risk_level == RiskLevel.CRITICAL:
            recommendations.extend([
                "🚨 CRITICAL: Do not proceed without comprehensive legal review",
                "🚨 Engage senior legal counsel immediately",
                "🚨 Consider risk mitigation insurance or guarantees"
            ])
        elif overall_risk_level == RiskLevel.HIGH:
            recommendations.extend([
                "⚠️ HIGH RISK: Requires thorough legal and business review",
                "⚠️ Obtain stakeholder approval before proceeding",
                "⚠️ Implement risk monitoring and reporting"
            ])
        elif overall_risk_level == RiskLevel.MEDIUM:
            recommendations.extend([
                "⚠️ MEDIUM RISK: Review with appropriate teams",
                "⚠️ Document risk acceptance and mitigation plans"
            ])
        
        # Category-specific recommendations
        category_counts = Counter(indicator.risk_category for indicator in risk_indicators)
        
        if RiskCategory.FINANCIAL in category_counts and category_counts[RiskCategory.FINANCIAL] > 1:
            recommendations.append("💰 Review financial exposure with finance team")
        
        if RiskCategory.LEGAL in category_counts and category_counts[RiskCategory.LEGAL] > 0:
            recommendations.append("⚖️ Obtain legal counsel review for legal risks")
        
        if RiskCategory.OPERATIONAL in category_counts and category_counts[RiskCategory.OPERATIONAL] > 1:
            recommendations.append("🔧 Assess operational capacity and resource requirements")
        
        if RiskCategory.COMPLIANCE in category_counts and category_counts[RiskCategory.COMPLIANCE] > 0:
            recommendations.append("📋 Verify compliance with regulatory requirements")
        
        # Specific risk type recommendations
        risk_types = {indicator.risk_type for indicator in risk_indicators}
        
        if 'unlimited_liability' in risk_types:
            recommendations.append("🛡️ Negotiate liability caps to limit exposure")
        
        if 'immediate_termination' in risk_types:
            recommendations.append("📅 Request notice period for termination clauses")
        
        if 'penalty_clause' in risk_types:
            recommendations.append("💸 Review penalty structures and ensure reasonableness")
        
        # Add mitigation strategies from high-confidence indicators
        high_confidence_indicators = [r for r in risk_indicators if r.confidence >= 0.8]
        for indicator in high_confidence_indicators[:3]:  # Top 3 high-confidence risks
            recommendations.extend([f"• {suggestion}" for suggestion in indicator.mitigation_suggestions[:2]])
        
        return list(set(recommendations))  # Remove duplicates
    
    def _initialize_risk_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize risk detection patterns"""
        return {
            'unlimited_liability': [
                {
                    'pattern': r'unlimited\s+liability',
                    'risk_level': 'CRITICAL',
                    'risk_category': 'legal',
                    'confidence': 0.95,
                    'description': 'Unlimited liability exposure detected'
                }
            ],
            'immediate_termination': [
                {
                    'pattern': r'immediate(?:ly)?\s+terminat',
                    'risk_level': 'HIGH',
                    'risk_category': 'legal',
                    'confidence': 0.9,
                    'description': 'Immediate termination clause without notice period'
                }
            ],
            'penalty_clause': [
                {
                    'pattern': r'penalty.*\$[\d,]+|liquidated\s+damages.*\$[\d,]+',
                    'risk_level': 'HIGH',
                    'risk_category': 'financial',
                    'confidence': 0.8,
                    'description': 'Significant financial penalties specified'
                }
            ],
            'indemnification_broad': [
                {
                    'pattern': r'indemnify.*(?:all|any).*(?:claims|damages|losses)',
                    'risk_level': 'HIGH',
                    'risk_category': 'legal',
                    'confidence': 0.85,
                    'description': 'Broad indemnification obligations'
                }
            ],
            'no_warranty': [
                {
                    'pattern': r'(?:no|without)\s+warrant(?:y|ies)|as\s+is.*without\s+warrant',
                    'risk_level': 'MEDIUM',
                    'risk_category': 'legal',
                    'confidence': 0.8,
                    'description': 'No warranty or as-is provisions'
                }
            ],
            'force_majeure_narrow': [
                {
                    'pattern': r'force\s+majeure.*(?:only|limited\s+to|solely)',
                    'risk_level': 'MEDIUM',
                    'risk_category': 'operational',
                    'confidence': 0.7,
                    'description': 'Narrowly defined force majeure clause'
                }
            ],
            'personal_guarantee': [
                {
                    'pattern': r'personal(?:ly)?\s+guarantee|individual(?:ly)?\s+liable',
                    'risk_level': 'CRITICAL',
                    'risk_category': 'financial',
                    'confidence': 0.9,
                    'description': 'Personal guarantee or individual liability'
                }
            ],
            'auto_renewal': [
                {
                    'pattern': r'automat(?:ic|ically)\s+renew|auto-renewal',
                    'risk_level': 'MEDIUM',
                    'risk_category': 'operational',
                    'confidence': 0.8,
                    'description': 'Automatic renewal without opt-out period'
                }
            ]
        }
    
    def _initialize_risk_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize risk assessment rules"""
        return {
            'high_value_contract': {
                'condition': 'contract_value > 100000',
                'risk_multiplier': 1.5,
                'description': 'High-value contracts require additional scrutiny'
            },
            'long_term_contract': {
                'condition': 'contract_duration > 24_months',
                'risk_multiplier': 1.3,
                'description': 'Long-term contracts have increased risk exposure'
            },
            'international_contract': {
                'condition': 'contains_international_elements',
                'risk_multiplier': 1.4,
                'description': 'International contracts have jurisdictional complexities'
            }
        }
    
    def _initialize_mitigation_strategies(self) -> Dict[str, List[str]]:
        """Initialize risk mitigation strategies"""
        return {
            'unlimited_liability': [
                "Negotiate liability caps or limitations",
                "Obtain liability insurance coverage",
                "Add carve-outs for gross negligence only"
            ],
            'immediate_termination': [
                "Request notice period (30-60 days minimum)",
                "Negotiate cure period for material breaches",
                "Add termination fee or wind-down provisions"
            ],
            'penalty_clause': [
                "Negotiate reasonable penalty amounts",
                "Add caps on total penalty exposure",
                "Include force majeure exceptions"
            ],
            'indemnification_broad': [
                "Limit indemnification to third-party claims",
                "Add knowledge qualifiers and materiality thresholds",
                "Negotiate mutual indemnification"
            ],
            'no_warranty': [
                "Request limited warranties for critical functions",
                "Negotiate service level agreements",
                "Add right to cure defects"
            ],
            'personal_guarantee': [
                "Limit personal guarantee to specific amounts",
                "Add sunset clauses for personal liability",
                "Negotiate corporate guarantee alternative"
            ]
        }
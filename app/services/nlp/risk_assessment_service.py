"""
Risk Assessment Service - Domain Layer

Handles contract risk analysis and pattern identification.
Following architectural standards: single responsibility, comprehensive documentation.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import Counter

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classifications."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskIndicator:
    """Container for risk assessment information."""
    risk_type: str
    risk_level: RiskLevel
    description: str
    confidence: float
    evidence: List[str]
    mitigation_suggestions: List[str]
    metadata: Dict[str, Any]


@dataclass
class RiskAssessment:
    """Complete risk assessment results."""
    overall_risk_level: RiskLevel
    risk_score: float
    identified_risks: List[RiskIndicator]
    risk_summary: str
    recommendations: List[str]
    assessment_metadata: Dict[str, Any]


class RiskAssessmentService:
    """
    Analyzes contract content for potential legal and business risks.
    
    Purpose: Identifies risk patterns, assesses risk levels, and provides
    mitigation recommendations for contract review workflows. Specializes
    in legal document risk analysis using domain-specific patterns.
    
    AI Context: This service handles all risk-related analysis. When debugging
    risk assessment issues, start here. The service uses pattern-based analysis
    combined with legal domain expertise to identify potential contract risks.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize risk assessment service.
        
        Args:
            config: Configuration for risk assessment parameters
        """
        self.config = config or {}
        self._risk_patterns = self._initialize_risk_patterns()
        self._risk_weights = self._initialize_risk_weights()
        self._mitigation_strategies = self._initialize_mitigation_strategies()
        
    def assess_contract_risks(self, contract_text: str, changes: Optional[List[Dict]] = None) -> RiskAssessment:
        """
        Perform comprehensive risk assessment of contract text.
        
        Purpose: Analyzes contract content and detected changes to identify
        potential legal and business risks. Provides risk scoring, categorization,
        and mitigation recommendations.
        
        Args:
            contract_text: Full contract text to analyze
            changes: Optional list of detected changes for change-specific risk analysis
        
        Returns:
            RiskAssessment: Complete risk analysis with recommendations
        
        Raises:
            RiskAssessmentError: If risk analysis process fails
        
        AI Context: Primary risk assessment function. Combines pattern-based
        risk detection with change impact analysis. For debugging, check
        risk pattern matching and scoring logic.
        """
        try:
            logger.info(f"Starting comprehensive risk assessment ({len(contract_text)} characters)")
            
            # Identify risk indicators in contract text
            risk_indicators = self._identify_all_risk_indicators(contract_text)
            
            # Analyze change-specific risks if changes provided
            if changes:
                change_risks = self._analyze_change_risks(changes, contract_text)
                risk_indicators.extend(change_risks)
            
            # Calculate overall risk score
            risk_score = self._calculate_overall_risk_score(risk_indicators)
            
            # Determine overall risk level
            overall_risk_level = self._determine_risk_level(risk_score)
            
            # Generate risk summary and recommendations
            risk_summary = self._generate_risk_summary(risk_indicators, overall_risk_level)
            recommendations = self._generate_risk_recommendations(risk_indicators, overall_risk_level)
            
            assessment = RiskAssessment(
                overall_risk_level=overall_risk_level,
                risk_score=risk_score,
                identified_risks=risk_indicators,
                risk_summary=risk_summary,
                recommendations=recommendations,
                assessment_metadata={
                    'risk_indicator_count': len(risk_indicators),
                    'high_risk_count': len([r for r in risk_indicators if r.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]),
                    'assessment_timestamp': logger.handlers[0].formatter.formatTime if logger.handlers else None,
                    'analysis_scope': 'full_contract' if not changes else 'contract_with_changes'
                }
            )
            
            logger.info(f"Risk assessment completed: {overall_risk_level.value} risk with {len(risk_indicators)} indicators")
            return assessment
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            raise RiskAssessmentError(f"Risk assessment failed: {str(e)}")
    
    def assess_change_risk(self, change: Dict[str, Any], contract_context: str) -> List[RiskIndicator]:
        """
        Assess risk level of a specific contract change.
        
        Args:
            change: Change details including original/modified text
            contract_context: Surrounding contract context
        
        Returns:
            List[RiskIndicator]: Risk indicators for the specific change
        """
        try:
            change_text = f"{change.get('original', '')} {change.get('modified', '')}"
            change_type = change.get('type', 'unknown')
            
            risks = []
            
            # Analyze change content for risk patterns
            content_risks = self._identify_risk_patterns_in_text(change_text)
            
            # Assess change type specific risks
            type_risks = self._assess_change_type_risks(change_type, change)
            
            # Assess context-specific risks
            context_risks = self._assess_contextual_risks(change_text, contract_context)
            
            risks.extend(content_risks)
            risks.extend(type_risks)
            risks.extend(context_risks)
            
            # Enhance risks with change-specific metadata
            for risk in risks:
                risk.metadata.update({
                    'change_type': change_type,
                    'change_id': change.get('id'),
                    'analysis_type': 'change_specific'
                })
            
            return risks
            
        except Exception as e:
            logger.error(f"Change risk assessment failed: {e}")
            return []
    
    def _identify_all_risk_indicators(self, text: str) -> List[RiskIndicator]:
        """Identify all risk indicators in contract text."""
        risk_indicators = []
        
        # Identify different types of risks
        risk_indicators.extend(self._identify_liability_risks(text))
        risk_indicators.extend(self._identify_financial_risks(text))
        risk_indicators.extend(self._identify_compliance_risks(text))
        risk_indicators.extend(self._identify_termination_risks(text))
        risk_indicators.extend(self._identify_ip_risks(text))
        risk_indicators.extend(self._identify_confidentiality_risks(text))
        risk_indicators.extend(self._identify_force_majeure_risks(text))
        
        return risk_indicators
    
    def _identify_liability_risks(self, text: str) -> List[RiskIndicator]:
        """Identify liability-related risks."""
        risks = []
        text_lower = text.lower()
        
        # High liability exposure indicators
        high_liability_patterns = [
            r'unlimited liability',
            r'no limitation.*liability',
            r'waive.*limitation.*liability',
            r'joint and several liability'
        ]
        
        for pattern in high_liability_patterns:
            if re.search(pattern, text_lower):
                risks.append(RiskIndicator(
                    risk_type='LIABILITY',
                    risk_level=RiskLevel.HIGH,
                    description='High liability exposure detected',
                    confidence=0.8,
                    evidence=[pattern],
                    mitigation_suggestions=[
                        'Negotiate liability caps',
                        'Add mutual limitation of liability clause',
                        'Consider insurance requirements'
                    ],
                    metadata={'pattern': pattern, 'category': 'liability_exposure'}
                ))
        
        # Missing liability limitations
        if not re.search(r'limitation.*liability|liability.*limited|cap.*liability', text_lower):
            risks.append(RiskIndicator(
                risk_type='LIABILITY',
                risk_level=RiskLevel.MEDIUM,
                description='No liability limitation clause detected',
                confidence=0.7,
                evidence=['absence of liability limitation language'],
                mitigation_suggestions=[
                    'Add mutual limitation of liability clause',
                    'Define specific liability caps',
                    'Exclude certain types of damages'
                ],
                metadata={'category': 'missing_protection'}
            ))
        
        return risks
    
    def _identify_financial_risks(self, text: str) -> List[RiskIndicator]:
        """Identify financial risks in contract."""
        risks = []
        text_lower = text.lower()
        
        # Payment term risks
        payment_risks = [
            (r'payment.*due.*immediately', RiskLevel.HIGH, 'Immediate payment requirement'),
            (r'payment.*(\d+).*days?.*after', RiskLevel.MEDIUM, 'Extended payment terms'),
            (r'no refund|non-refundable', RiskLevel.MEDIUM, 'Non-refundable payment terms'),
            (r'penalty.*late.*payment', RiskLevel.MEDIUM, 'Late payment penalties')
        ]
        
        for pattern, risk_level, description in payment_risks:
            if re.search(pattern, text_lower):
                risks.append(RiskIndicator(
                    risk_type='FINANCIAL',
                    risk_level=risk_level,
                    description=description,
                    confidence=0.7,
                    evidence=[pattern],
                    mitigation_suggestions=self._get_financial_mitigations(description),
                    metadata={'pattern': pattern, 'category': 'payment_terms'}
                ))
        
        # Cost escalation risks
        if re.search(r'automatic.*increase|escalation.*cost|price.*adjustment', text_lower):
            risks.append(RiskIndicator(
                risk_type='FINANCIAL',
                risk_level=RiskLevel.MEDIUM,
                description='Automatic cost escalation provisions',
                confidence=0.8,
                evidence=['cost escalation language'],
                mitigation_suggestions=[
                    'Cap annual increases',
                    'Require approval for increases',
                    'Tie increases to specific indices'
                ],
                metadata={'category': 'cost_escalation'}
            ))
        
        return risks
    
    def _identify_compliance_risks(self, text: str) -> List[RiskIndicator]:
        """Identify regulatory compliance risks."""
        risks = []
        text_lower = text.lower()
        
        # Regulatory compliance indicators
        compliance_areas = [
            ('gdpr|data protection', 'Data protection compliance requirements'),
            ('hipaa', 'Healthcare data compliance requirements'),
            ('sox|sarbanes', 'Financial compliance requirements'),
            ('environmental.*regulation', 'Environmental compliance requirements'),
            ('export.*control', 'Export control compliance requirements')
        ]
        
        for pattern, description in compliance_areas:
            if re.search(pattern, text_lower):
                risks.append(RiskIndicator(
                    risk_type='COMPLIANCE',
                    risk_level=RiskLevel.HIGH,
                    description=description,
                    confidence=0.8,
                    evidence=[pattern],
                    mitigation_suggestions=[
                        'Ensure compliance procedures are defined',
                        'Allocate compliance responsibilities',
                        'Include compliance monitoring provisions'
                    ],
                    metadata={'pattern': pattern, 'category': 'regulatory_compliance'}
                ))
        
        return risks
    
    def _identify_termination_risks(self, text: str) -> List[RiskIndicator]:
        """Identify contract termination risks."""
        risks = []
        text_lower = text.lower()
        
        # Termination without cause
        if re.search(r'terminate.*without.*cause|terminate.*any.*reason', text_lower):
            risks.append(RiskIndicator(
                risk_type='TERMINATION',
                risk_level=RiskLevel.MEDIUM,
                description='Termination without cause allowed',
                confidence=0.8,
                evidence=['termination without cause language'],
                mitigation_suggestions=[
                    'Require advance notice period',
                    'Add termination fees or penalties',
                    'Include work completion obligations'
                ],
                metadata={'category': 'termination_rights'}
            ))
        
        # Short notice periods
        notice_match = re.search(r'(\d+).*days?.*notice.*terminat', text_lower)
        if notice_match:
            days = int(notice_match.group(1))
            if days < 30:
                risks.append(RiskIndicator(
                    risk_type='TERMINATION',
                    risk_level=RiskLevel.HIGH if days < 7 else RiskLevel.MEDIUM,
                    description=f'Short termination notice period ({days} days)',
                    confidence=0.9,
                    evidence=[f'{days} day notice period'],
                    mitigation_suggestions=[
                        'Negotiate longer notice period',
                        'Add project completion obligations',
                        'Include transition assistance requirements'
                    ],
                    metadata={'notice_days': days, 'category': 'notice_period'}
                ))
        
        return risks
    
    def _identify_ip_risks(self, text: str) -> List[RiskIndicator]:
        """Identify intellectual property risks."""
        risks = []
        text_lower = text.lower()
        
        # IP assignment without compensation
        if re.search(r'assign.*intellectual.*property|transfer.*ip.*rights', text_lower):
            if not re.search(r'compensation.*ip|payment.*intellectual', text_lower):
                risks.append(RiskIndicator(
                    risk_type='INTELLECTUAL_PROPERTY',
                    risk_level=RiskLevel.HIGH,
                    description='IP assignment without clear compensation',
                    confidence=0.7,
                    evidence=['IP assignment language without compensation'],
                    mitigation_suggestions=[
                        'Clarify IP compensation terms',
                        'Limit scope of IP assignment',
                        'Retain rights to pre-existing IP'
                    ],
                    metadata={'category': 'ip_assignment'}
                ))
        
        # Broad IP indemnification
        if re.search(r'indemnify.*intellectual.*property|ip.*infringement.*indemnity', text_lower):
            risks.append(RiskIndicator(
                risk_type='INTELLECTUAL_PROPERTY',
                risk_level=RiskLevel.MEDIUM,
                description='IP infringement indemnification obligations',
                confidence=0.8,
                evidence=['IP indemnification language'],
                mitigation_suggestions=[
                    'Limit indemnification scope',
                    'Add mutual indemnification',
                    'Cap indemnification amounts'
                ],
                metadata={'category': 'ip_indemnification'}
            ))
        
        return risks
    
    def _identify_confidentiality_risks(self, text: str) -> List[RiskIndicator]:
        """Identify confidentiality and data security risks."""
        risks = []
        text_lower = text.lower()
        
        # Broad confidentiality obligations
        if re.search(r'all.*information.*confidential|everything.*confidential', text_lower):
            risks.append(RiskIndicator(
                risk_type='CONFIDENTIALITY',
                risk_level=RiskLevel.MEDIUM,
                description='Overly broad confidentiality obligations',
                confidence=0.7,
                evidence=['broad confidentiality language'],
                mitigation_suggestions=[
                    'Define specific confidential information',
                    'Add standard exceptions',
                    'Limit duration of confidentiality'
                ],
                metadata={'category': 'confidentiality_scope'}
            ))
        
        # No data security requirements
        if not re.search(r'data.*security|security.*measures|encryption', text_lower):
            risks.append(RiskIndicator(
                risk_type='CONFIDENTIALITY',
                risk_level=RiskLevel.MEDIUM,
                description='No data security requirements specified',
                confidence=0.6,
                evidence=['absence of data security language'],
                mitigation_suggestions=[
                    'Add data security requirements',
                    'Specify encryption standards',
                    'Include breach notification obligations'
                ],
                metadata={'category': 'data_security'}
            ))
        
        return risks
    
    def _identify_force_majeure_risks(self, text: str) -> List[RiskIndicator]:
        """Identify force majeure and business continuity risks."""
        risks = []
        text_lower = text.lower()
        
        # No force majeure clause
        if not re.search(r'force.*majeure|act.*god|unforeseeable.*circumstances', text_lower):
            risks.append(RiskIndicator(
                risk_type='BUSINESS_CONTINUITY',
                risk_level=RiskLevel.MEDIUM,
                description='No force majeure protection',
                confidence=0.6,
                evidence=['absence of force majeure clause'],
                mitigation_suggestions=[
                    'Add force majeure clause',
                    'Define qualifying events',
                    'Include notification requirements'
                ],
                metadata={'category': 'force_majeure'}
            ))
        
        return risks
    
    def _analyze_change_risks(self, changes: List[Dict], contract_text: str) -> List[RiskIndicator]:
        """Analyze risks specific to contract changes."""
        change_risks = []
        
        for change in changes:
            change_risk_indicators = self.assess_change_risk(change, contract_text)
            change_risks.extend(change_risk_indicators)
        
        return change_risks
    
    def _assess_change_type_risks(self, change_type: str, change: Dict) -> List[RiskIndicator]:
        """Assess risks based on type of change."""
        risks = []
        
        if change_type == 'deletion':
            # Deletions can be risky if they remove protections
            risks.append(RiskIndicator(
                risk_type='CHANGE_IMPACT',
                risk_level=RiskLevel.MEDIUM,
                description='Text deletion may remove important protections',
                confidence=0.6,
                evidence=[f"Deleted: {change.get('original', '')}"],
                mitigation_suggestions=[
                    'Review deleted text for protective clauses',
                    'Ensure no critical terms were removed',
                    'Consider if deletion creates legal gaps'
                ],
                metadata={'change_type': 'deletion'}
            ))
        
        elif change_type == 'addition':
            # Additions can add new obligations or restrictions
            added_text = change.get('modified', '')
            if any(keyword in added_text.lower() for keyword in ['shall', 'must', 'required', 'obligation']):
                risks.append(RiskIndicator(
                    risk_type='CHANGE_IMPACT',
                    risk_level=RiskLevel.MEDIUM,
                    description='Addition creates new obligations',
                    confidence=0.7,
                    evidence=[f"Added: {added_text}"],
                    mitigation_suggestions=[
                        'Review new obligations for feasibility',
                        'Ensure reciprocal obligations where appropriate',
                        'Consider impact on existing terms'
                    ],
                    metadata={'change_type': 'addition'}
                ))
        
        return risks
    
    def _assess_contextual_risks(self, change_text: str, contract_context: str) -> List[RiskIndicator]:
        """Assess risks based on contract context."""
        risks = []
        
        # Risk patterns in change context
        risk_contexts = [
            ('liability', RiskLevel.HIGH, 'Liability-related change'),
            ('payment', RiskLevel.MEDIUM, 'Payment-related change'),
            ('termination', RiskLevel.MEDIUM, 'Termination-related change'),
            ('intellectual property', RiskLevel.MEDIUM, 'IP-related change'),
            ('confidential', RiskLevel.MEDIUM, 'Confidentiality-related change')
        ]
        
        change_text_lower = change_text.lower()
        context_lower = contract_context.lower()
        
        for context_keyword, risk_level, description in risk_contexts:
            if context_keyword in change_text_lower or context_keyword in context_lower:
                risks.append(RiskIndicator(
                    risk_type='CONTEXTUAL',
                    risk_level=risk_level,
                    description=description,
                    confidence=0.6,
                    evidence=[f"Context: {context_keyword}"],
                    mitigation_suggestions=[
                        'Review change in context of related clauses',
                        'Ensure change maintains clause consistency',
                        'Consider downstream impacts'
                    ],
                    metadata={'context_type': context_keyword}
                ))
        
        return risks
    
    def _identify_risk_patterns_in_text(self, text: str) -> List[RiskIndicator]:
        """Identify risk patterns in specific text."""
        risks = []
        text_lower = text.lower()
        
        # High-risk keywords
        high_risk_patterns = [
            ('unlimited', 'Unlimited obligation or liability'),
            ('irrevocable', 'Irrevocable commitment'),
            ('unconditional', 'Unconditional obligation'),
            ('guarantee', 'Guarantee obligation'),
            ('indemnify', 'Indemnification requirement')
        ]
        
        for pattern, description in high_risk_patterns:
            if pattern in text_lower:
                risks.append(RiskIndicator(
                    risk_type='CONTENT_RISK',
                    risk_level=RiskLevel.MEDIUM,
                    description=description,
                    confidence=0.7,
                    evidence=[pattern],
                    mitigation_suggestions=[
                        'Consider adding limitations or conditions',
                        'Evaluate scope of obligation',
                        'Ensure mutual terms where appropriate'
                    ],
                    metadata={'pattern': pattern}
                ))
        
        return risks
    
    def _calculate_overall_risk_score(self, risk_indicators: List[RiskIndicator]) -> float:
        """Calculate weighted overall risk score."""
        if not risk_indicators:
            return 0.0
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for risk in risk_indicators:
            weight = self._risk_weights.get(risk.risk_level, 1.0)
            weighted_score = self._risk_level_to_score(risk.risk_level) * weight * risk.confidence
            
            total_weighted_score += weighted_score
            total_weight += weight
        
        return min(1.0, total_weighted_score / total_weight if total_weight > 0 else 0.0)
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine overall risk level from risk score."""
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            return RiskLevel.HIGH
        elif risk_score >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _risk_level_to_score(self, risk_level: RiskLevel) -> float:
        """Convert risk level to numerical score."""
        score_map = {
            RiskLevel.LOW: 0.2,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.8,
            RiskLevel.CRITICAL: 1.0
        }
        return score_map.get(risk_level, 0.5)
    
    def _generate_risk_summary(self, risk_indicators: List[RiskIndicator], overall_risk: RiskLevel) -> str:
        """Generate executive summary of risk assessment."""
        if not risk_indicators:
            return "No significant risks identified in contract analysis."
        
        risk_counts = Counter(risk.risk_level for risk in risk_indicators)
        risk_types = Counter(risk.risk_type for risk in risk_indicators)
        
        summary_parts = [
            f"Overall risk level: {overall_risk.value.upper()}",
            f"Total risk indicators: {len(risk_indicators)}"
        ]
        
        if risk_counts[RiskLevel.CRITICAL] > 0:
            summary_parts.append(f"Critical risks: {risk_counts[RiskLevel.CRITICAL]}")
        if risk_counts[RiskLevel.HIGH] > 0:
            summary_parts.append(f"High risks: {risk_counts[RiskLevel.HIGH]}")
        if risk_counts[RiskLevel.MEDIUM] > 0:
            summary_parts.append(f"Medium risks: {risk_counts[RiskLevel.MEDIUM]}")
        
        # Top risk categories
        top_risk_types = risk_types.most_common(3)
        if top_risk_types:
            type_summary = ", ".join([f"{risk_type} ({count})" for risk_type, count in top_risk_types])
            summary_parts.append(f"Primary risk areas: {type_summary}")
        
        return ". ".join(summary_parts) + "."
    
    def _generate_risk_recommendations(self, risk_indicators: List[RiskIndicator], overall_risk: RiskLevel) -> List[str]:
        """Generate risk mitigation recommendations."""
        recommendations = set()
        
        # Add recommendations from individual risks
        for risk in risk_indicators:
            if risk.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                recommendations.update(risk.mitigation_suggestions)
        
        # Add overall recommendations based on risk level
        if overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.update([
                'Engage legal counsel for comprehensive contract review',
                'Consider additional insurance coverage',
                'Implement enhanced contract management processes'
            ])
        elif overall_risk == RiskLevel.MEDIUM:
            recommendations.update([
                'Review high and medium risk items with legal team',
                'Monitor contract performance closely',
                'Document risk acceptance decisions'
            ])
        
        return sorted(list(recommendations))
    
    def _get_financial_mitigations(self, risk_description: str) -> List[str]:
        """Get specific mitigation suggestions for financial risks."""
        mitigation_map = {
            'immediate payment': [
                'Negotiate payment terms',
                'Request payment schedule',
                'Add payment milestones'
            ],
            'extended payment': [
                'Add late payment interest',
                'Require payment guarantees',
                'Include acceleration clauses'
            ],
            'non-refundable': [
                'Negotiate partial refund terms',
                'Add performance-based refunds',
                'Include termination for cause refunds'
            ]
        }
        
        for key, suggestions in mitigation_map.items():
            if key in risk_description.lower():
                return suggestions
        
        return ['Review financial terms with finance team']
    
    def _initialize_risk_patterns(self) -> Dict[str, List[str]]:
        """Initialize risk detection patterns."""
        return {
            'high_liability': [
                r'unlimited liability',
                r'no limitation.*liability',
                r'joint and several liability'
            ],
            'financial_risk': [
                r'non-refundable',
                r'payment.*due.*immediately',
                r'automatic.*increase'
            ],
            'termination_risk': [
                r'terminate.*without.*cause',
                r'immediate.*termination'
            ]
        }
    
    def _initialize_risk_weights(self) -> Dict[RiskLevel, float]:
        """Initialize risk level weights for scoring."""
        return {
            RiskLevel.LOW: 0.5,
            RiskLevel.MEDIUM: 1.0,
            RiskLevel.HIGH: 2.0,
            RiskLevel.CRITICAL: 3.0
        }
    
    def _initialize_mitigation_strategies(self) -> Dict[str, List[str]]:
        """Initialize mitigation strategies for different risk types."""
        return {
            'LIABILITY': [
                'Add liability limitations',
                'Negotiate mutual liability caps',
                'Include insurance requirements'
            ],
            'FINANCIAL': [
                'Review payment terms',
                'Add financial protections',
                'Consider payment guarantees'
            ],
            'COMPLIANCE': [
                'Ensure regulatory compliance',
                'Add compliance monitoring',
                'Define compliance responsibilities'
            ]
        }


class RiskAssessmentError(Exception):
    """Exception raised when risk assessment fails."""
    pass
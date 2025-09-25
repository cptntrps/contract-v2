"""
Incremental Contract Analysis Engine

Implements proper change-by-change analysis similar to Word Track Changes,
focusing on individual deltas rather than sending full documents to LLM.
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..models.analysis_result import Change
from ...utils.logging.setup import get_logger

logger = get_logger(__name__)


@dataclass
class ChangeContext:
    """Context around a specific change"""
    before_text: str  # Text before the change
    after_text: str   # Text after the change
    section_title: str  # Which section this change is in
    change_type: str   # 'addition', 'deletion', 'modification', 'replacement'
    

class IncrementalAnalyzer:
    """
    Analyzes contract changes incrementally, one change at a time,
    similar to Word's Track Changes feature.
    """
    
    def __init__(self, llm_provider):
        self.llm_provider = llm_provider
        
    def analyze_change(self, change: Change, context: ChangeContext) -> Change:
        """
        Analyze a single change with its context using focused LLM analysis.
        
        Purpose: Provides granular, contextual analysis of individual contract changes
        similar to Word's Track Changes review. Focuses LLM attention on specific
        changes rather than processing entire documents.
        
        Args:
            change: The change to analyze
            context: Surrounding context for the change
            
        Returns:
            Enhanced change with classification and analysis including:
            - classification: CRITICAL/SIGNIFICANT/INCONSEQUENTIAL
            - explanation: Business-focused change description
            - risk_impact: Risk assessment
            - recommendation: Suggested action
            
        AI Context: Core incremental analysis function. If change classifications
        are inconsistent, debug the prompt construction and LLM response parsing here.
        This approach provides more accurate analysis than batch processing.
        """
        try:
            prompt = self._build_change_prompt(change, context)
            
            # Get LLM analysis for this specific change
            response = self.llm_provider.generate_response(prompt)
            
            # Parse and apply analysis
            analysis = self._parse_change_analysis(response.content)
            
            # Update change with analysis
            if analysis:
                change.classification = analysis.get('classification', 'INCONSEQUENTIAL')
                change.explanation = analysis.get('explanation', change.explanation)
                change.risk_impact = analysis.get('risk_impact', '')
                change.recommendation = analysis.get('recommendation', '')
                change.metadata['business_impact'] = analysis.get('business_impact', '')
                change.metadata['legal_significance'] = analysis.get('legal_significance', '')
                
            return change
            
        except Exception as e:
            logger.error(f"Error analyzing change {change.id}: {e}")
            return change  # Return original change if analysis fails
    
    def _build_change_prompt(self, change: Change, context: ChangeContext) -> str:
        """Build focused prompt for a single change analysis"""
        
        change_description = self._describe_change(change)
        
        prompt = f"""
Analyze this specific contract change and classify its business impact:

SECTION: {context.section_title}
CHANGE TYPE: {context.change_type}

CONTEXT BEFORE:
{context.before_text}

CHANGE DETAILS:
{change_description}

CONTEXT AFTER:
{context.after_text}

Analyze ONLY this change and provide:

1. Classification (CRITICAL/SIGNIFICANT/INCONSEQUENTIAL):
   - CRITICAL: Affects key business terms (price, liability, scope, termination, IP)
   - SIGNIFICANT: Important operational terms (deadlines, processes, responsibilities)  
   - INCONSEQUENTIAL: Minor wording, formatting, or template placeholder changes

2. Business Impact: How does this change affect the business relationship?

3. Legal Significance: Are there legal or compliance implications?

4. Risk Assessment: What risks does this change introduce or mitigate?

5. Recommendation: Should this change be accepted, negotiated, or rejected?

Respond in JSON format:
{{
  "classification": "CRITICAL|SIGNIFICANT|INCONSEQUENTIAL",
  "explanation": "Clear explanation of what changed and why it matters",
  "business_impact": "Specific business implications",
  "legal_significance": "Legal or compliance considerations",
  "risk_impact": "Risk analysis and mitigation",
  "recommendation": "Specific recommended action"
}}
"""
        return prompt
    
    def _describe_change(self, change: Change) -> str:
        """Create a clear description of what changed"""
        
        if change.deleted_text and change.inserted_text:
            return f"REPLACED: '{change.deleted_text}' → '{change.inserted_text}'"
        elif change.deleted_text:
            return f"DELETED: '{change.deleted_text}'"
        elif change.inserted_text:
            return f"ADDED: '{change.inserted_text}'"
        else:
            return "UNKNOWN CHANGE"
    
    def _parse_change_analysis(self, llm_response: str) -> Optional[Dict[str, str]]:
        """Parse LLM response for a single change"""
        try:
            # Clean response and parse JSON
            clean_response = llm_response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
                
            analysis = json.loads(clean_response)
            return analysis
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing change analysis: {e}")
            return None
    
    def extract_section_context(self, full_text: str, change_position: int) -> str:
        """
        Extract the section title/context where this change occurs
        
        Args:
            full_text: Full document text
            change_position: Approximate position of the change
            
        Returns:
            Section title or context description
        """
        try:
            # Look backwards from change position to find section headers
            text_before = full_text[:change_position]
            lines_before = text_before.split('\n')
            
            # Look for section patterns (numbers, headers, etc.)
            section_patterns = [
                lambda line: line.strip().startswith(tuple('0123456789')),  # Numbered sections
                lambda line: line.isupper() and len(line.strip()) < 50,      # ALL CAPS headers
                lambda line: 'SECTION' in line.upper(),                      # Section keywords
                lambda line: line.strip().endswith(':')                      # Colon endings
            ]
            
            # Find the most recent section header
            for line in reversed(lines_before[-20:]):  # Check last 20 lines
                line = line.strip()
                if line and any(pattern(line) for pattern in section_patterns):
                    return line
            
            # Fallback: use surrounding text
            start = max(0, change_position - 100)
            end = min(len(full_text), change_position + 100)
            return f"Context: ...{full_text[start:end]}..."
            
        except Exception as e:
            logger.warning(f"Error extracting section context: {e}")
            return "Unknown Section"
    
    def get_change_context(
        self, 
        full_text: str, 
        change: Change,
        context_size: int = 200
    ) -> ChangeContext:
        """
        Extract context around a change for better analysis
        
        Args:
            full_text: Complete document text
            change: Change object to get context for  
            context_size: Characters of context to include
            
        Returns:
            ChangeContext with before/after text and metadata
        """
        try:
            # For now, we'll use a simple approach
            # In a real implementation, you'd track change positions during diff
            
            # Determine change type
            if change.deleted_text and change.inserted_text:
                change_type = 'replacement'
            elif change.deleted_text:
                change_type = 'deletion'
            elif change.inserted_text:
                change_type = 'addition'
            else:
                change_type = 'unknown'
            
            # Extract section context (simplified)
            section_title = "Document Section"  # Would be determined from position
            
            # Get surrounding text (simplified - would use actual positions)
            before_text = f"...{change.deleted_text or change.inserted_text}..."[:context_size]
            after_text = f"...{change.inserted_text or change.deleted_text}..."[:context_size]
            
            return ChangeContext(
                before_text=before_text,
                after_text=after_text,
                section_title=section_title,
                change_type=change_type
            )
            
        except Exception as e:
            logger.error(f"Error getting change context: {e}")
            return ChangeContext("", "", "Unknown", "unknown")
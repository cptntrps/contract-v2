"""
Core Domain Models Package

Business domain entities and value objects for contract analysis.
"""

from .contract import Contract, validate_contract_file
from .analysis_result import (
    AnalysisResult, 
    Change, 
    ChangeClassification, 
    ChangeType,
    create_change_from_diff
)

__all__ = [
    'Contract',
    'AnalysisResult',
    'Change',
    'ChangeClassification',
    'ChangeType',
    'validate_contract_file',
    'create_change_from_diff'
]
"""
Contract Analyzer Application Package

A modular contract analysis application with LLM integration,
report generation, and web-based dashboard interface.
"""

__version__ = "1.2.1"
__author__ = "Contract Analyzer Team"

from .main import create_app

__all__ = ["create_app"]
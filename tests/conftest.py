"""
Pytest configuration and shared fixtures.
"""

import pytest
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import application for testing
from app.api.app import create_api_app
from app.config.settings import get_config

@pytest.fixture
def app():
    """Create application for testing."""
    config = get_config()
    config.TESTING = True
    app = create_api_app(config)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def sample_contract_data():
    """Sample contract data for testing."""
    return {
        'filename': 'test_contract.docx',
        'content': b'Test contract content',
        'size': 1024
    }

import pytest
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup and teardown for each test."""
    # Setup
    yield
    # Teardown

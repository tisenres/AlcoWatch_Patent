import sys
from pathlib import Path

# Add project root to sys.path for imports BEFORE anything else
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def pytest_configure(config):
    """Hook that runs at the start of pytest configuration."""
    project_root = Path(__file__).parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

"""
pytest configuration for encontreras tests.

All tests in this suite are pure unit tests — no network, no browser.
They test only the core modules: models, entity_resolution, lead_scorer, exporter.
"""

import sys
from pathlib import Path

# Make sure the project root is in sys.path so imports like
# `from src.core.models import Business` work regardless of how pytest is invoked.
sys.path.insert(0, str(Path(__file__).parent.parent))

"""Pytest configuration and shared fixtures."""

import json
import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def test_data_dir():
    """Return path to test input data."""
    return Path(__file__).parent / 'input'


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory for test results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def opted_in_players():
    """Return the list of opted-in players from test data."""
    opt_in_file = Path(__file__).parent / 'input' / 'opt_in.csv'
    if opt_in_file.exists():
        with open(opt_in_file, 'r') as f:
            return {line.strip() for line in f if line.strip()}
    return set()


@pytest.fixture
def sample_tournament_data():
    """Return sample tournament match data."""
    return {
        "20250817": {
            "id": "20250817",
            "rounds": {
                "1": {
                    "matches": [
                        {
                            "table": "1",
                            "player1": "Player A",
                            "player2": "Player B",
                            "result": [2, 0],
                            "has_bye": False
                        },
                        {
                            "table": "2",
                            "player1": "Player C",
                            "player2": "BYE",
                            "result": None,
                            "has_bye": True
                        }
                    ],
                    "processed_at": "2025-08-17T10:00:00"
                }
            },
            "created_at": "2025-08-17T09:00:00"
        }
    }

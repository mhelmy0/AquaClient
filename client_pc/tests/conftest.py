"""
Pytest configuration and shared fixtures.
"""

import pytest
import tempfile
from pathlib import Path
import sys

# Add modules directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))

from config import load_config
from logging_json import JsonLogger


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config(temp_dir):
    """Create a mock configuration for testing."""
    return {
        "stream": {
            "url": "rtmp://127.0.0.1/live/test",
            "read_timeout_seconds": 10,
            "reconnect": {
                "enabled": True,
                "backoff_seconds": [1, 2, 5, 10, 20, 30]
            }
        },
        "recording": {
            "enabled": True,
            "output_dir": str(temp_dir / "videos"),
            "segment_seconds": 10800,
            "disk_free_floor_mib": 500,
            "disk_free_resume_mib": 1024
        },
        "snapshots": {
            "output_dir": str(temp_dir / "snapshots"),
            "hotkey": "s",
            "interval_seconds": 0
        },
        "logging": {
            "level": "info",
            "file": str(temp_dir / "test.log"),
            "rotate_max_mb": 10,
            "rotate_backups": 5
        },
        "health": {
            "check_interval_seconds": 5
        }
    }


@pytest.fixture
def logger(mock_config):
    """Create a logger instance for testing."""
    return JsonLogger(mock_config)

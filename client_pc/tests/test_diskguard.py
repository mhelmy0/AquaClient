"""
Unit tests for disk space guard logic.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))

from recorder import Recorder


def test_disk_guard_pause_threshold(mock_config, logger):
    """Test that recording pauses when disk space falls below floor."""
    recorder = Recorder(mock_config, logger)

    # Mock disk space to be below floor (500 MiB)
    with patch.object(recorder, 'get_disk_free_mib', return_value=400):
        result = recorder.check_disk_space()

        # Should return False (not safe to record)
        assert result is False
        # Should be paused
        assert recorder.is_paused is True


def test_disk_guard_resume_threshold(mock_config, logger):
    """Test that recording resumes when disk space exceeds resume threshold."""
    recorder = Recorder(mock_config, logger)

    # First, simulate paused state due to low disk
    with patch.object(recorder, 'get_disk_free_mib', return_value=400):
        recorder.check_disk_space()
        assert recorder.is_paused is True

    # Now simulate disk space increasing above resume threshold (1024 MiB)
    with patch.object(recorder, 'get_disk_free_mib', return_value=1500):
        result = recorder.check_disk_space()

        # Should return True (safe to record)
        assert result is True
        # Should no longer be paused
        assert recorder.is_paused is False


def test_disk_guard_hysteresis(mock_config, logger):
    """Test hysteresis: won't resume until above resume threshold."""
    recorder = Recorder(mock_config, logger)

    # Pause due to low disk
    with patch.object(recorder, 'get_disk_free_mib', return_value=400):
        recorder.check_disk_space()
        assert recorder.is_paused is True

    # Disk increases slightly but still below resume threshold
    with patch.object(recorder, 'get_disk_free_mib', return_value=800):
        result = recorder.check_disk_space()

        # Should still be paused
        assert result is False
        assert recorder.is_paused is True


def test_disk_guard_safe_range(mock_config, logger):
    """Test that recording continues normally when disk space is adequate."""
    recorder = Recorder(mock_config, logger)

    # Ample disk space
    with patch.object(recorder, 'get_disk_free_mib', return_value=5000):
        result = recorder.check_disk_space()

        # Should be safe to record
        assert result is True
        assert recorder.is_paused is False


def test_disk_guard_exact_threshold(mock_config, logger):
    """Test behavior at exact threshold values."""
    recorder = Recorder(mock_config, logger)

    # Exactly at floor threshold (500 MiB)
    with patch.object(recorder, 'get_disk_free_mib', return_value=500):
        result = recorder.check_disk_space()
        # Should not pause (threshold is <, not <=)
        assert result is True

    # Just below floor
    with patch.object(recorder, 'get_disk_free_mib', return_value=499):
        result = recorder.check_disk_space()
        # Should pause
        assert result is False
        assert recorder.is_paused is True

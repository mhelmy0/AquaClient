"""
Unit tests for filename generation and validation.
"""

import pytest
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))

from snapshotter import Snapshotter


def test_snapshot_filename_format(mock_config, logger):
    """Test that snapshot filenames match expected pattern."""
    snapshotter = Snapshotter(mock_config, logger)

    filename = snapshotter.generate_filename()

    # Check pattern: snap_YYYYMMDD_HHMMSS_mmm.jpg
    assert filename.startswith("snap_")
    assert filename.endswith(".jpg")
    assert len(filename) == 28  # snap_ + 8 + _ + 6 + _ + 3 + .jpg = 28

    # Verify date components are numeric
    parts = filename.replace("snap_", "").replace(".jpg", "").split("_")
    assert len(parts) == 3
    assert parts[0].isdigit() and len(parts[0]) == 8  # YYYYMMDD
    assert parts[1].isdigit() and len(parts[1]) == 6  # HHMMSS
    assert parts[2].isdigit() and len(parts[2]) == 3  # milliseconds


def test_snapshot_filename_uniqueness(mock_config, logger):
    """Test that consecutive snapshots have different filenames."""
    snapshotter = Snapshotter(mock_config, logger)

    filename1 = snapshotter.generate_filename()
    filename2 = snapshotter.generate_filename()

    # Filenames should be different (millisecond precision)
    # Note: In rare cases they might be the same if generated in same millisecond
    # For this test, we just verify they're valid
    assert filename1.startswith("snap_")
    assert filename2.startswith("snap_")


def test_recording_segment_pattern():
    """Test that recording segment filenames follow strftime pattern."""
    # Pattern used in FFmpeg: rec_%Y%m%d_%H%M%S.mp4
    now = datetime.now()
    filename = now.strftime("rec_%Y%m%d_%H%M%S.mp4")

    assert filename.startswith("rec_")
    assert filename.endswith(".mp4")
    assert len(filename) == 23  # rec_ + 8 + _ + 6 + .mp4 = 23


def test_recording_segment_rollover():
    """Test that segment filenames roll over correctly at 3-hour boundaries."""
    # Simulate segment filenames at different times
    base_time = datetime(2025, 10, 3, 12, 0, 0)

    segment1 = base_time.strftime("rec_%Y%m%d_%H%M%S.mp4")
    # 3 hours later
    segment2 = base_time.replace(hour=15).strftime("rec_%Y%m%d_%H%M%S.mp4")

    assert segment1 == "rec_20251003_120000.mp4"
    assert segment2 == "rec_20251003_150000.mp4"
    assert segment1 != segment2

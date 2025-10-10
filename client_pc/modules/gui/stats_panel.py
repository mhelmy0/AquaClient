"""
Statistics panel widget for displaying recording and snapshot statistics.

Shows daily and total statistics for recordings and snapshots.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QGridLayout
from PyQt5.QtCore import Qt
from pathlib import Path
from datetime import datetime, timedelta
import os


class StatsPanel(QWidget):
    """
    Widget for displaying recording and snapshot statistics.

    Shows:
    - Recording time today
    - Number of segments today
    - Number of snapshots today
    - Total disk space used
    """

    def __init__(self, parent=None):
        """Initialize statistics panel."""
        super().__init__(parent)

        # Create layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Create group box
        group = QGroupBox("📊 Statistics")

        # Create grid layout for stats
        grid = QGridLayout()
        grid.setSpacing(10)

        # Today's recording time
        grid.addWidget(QLabel("Today's Recording:"), 0, 0)
        self.recording_time_label = QLabel("0h 0m")
        self.recording_time_label.setAlignment(Qt.AlignRight)
        grid.addWidget(self.recording_time_label, 0, 1)

        # Segments recorded today
        grid.addWidget(QLabel("Segments Today:"), 1, 0)
        self.segments_label = QLabel("0")
        self.segments_label.setAlignment(Qt.AlignRight)
        grid.addWidget(self.segments_label, 1, 1)

        # Snapshots taken today
        grid.addWidget(QLabel("Snapshots Today:"), 2, 0)
        self.snapshots_label = QLabel("0")
        self.snapshots_label.setAlignment(Qt.AlignRight)
        grid.addWidget(self.snapshots_label, 2, 1)

        # Total disk usage
        grid.addWidget(QLabel("Total Disk Used:"), 3, 0)
        self.disk_usage_label = QLabel("0.0 GB")
        self.disk_usage_label.setAlignment(Qt.AlignRight)
        grid.addWidget(self.disk_usage_label, 3, 1)

        group.setLayout(grid)
        layout.addWidget(group)
        self.setLayout(layout)

        # Internal state
        self.recording_seconds_today = 0
        self.segments_today = 0
        self.snapshots_today = 0
        self.total_disk_gb = 0.0

        # Paths for counting files
        self.videos_path = None
        self.snapshots_path = None

    def set_paths(self, videos_path: str, snapshots_path: str) -> None:
        """
        Set paths for recording and snapshot directories.

        Args:
            videos_path: Path to video recordings directory
            snapshots_path: Path to snapshots directory
        """
        self.videos_path = Path(videos_path)
        self.snapshots_path = Path(snapshots_path)

    def update_recording_time(self, seconds: int) -> None:
        """
        Update today's recording time.

        Args:
            seconds: Total recording seconds today
        """
        self.recording_seconds_today = seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        self.recording_time_label.setText(f"{hours}h {minutes}m")

    def update_segments_count(self, count: int) -> None:
        """
        Update segments recorded today.

        Args:
            count: Number of segments
        """
        self.segments_today = count
        self.segments_label.setText(str(count))

    def update_snapshots_count(self, count: int) -> None:
        """
        Update snapshots taken today.

        Args:
            count: Number of snapshots
        """
        self.snapshots_today = count
        self.snapshots_label.setText(str(count))

    def update_disk_usage(self, gb: float) -> None:
        """
        Update total disk usage.

        Args:
            gb: Disk usage in GB
        """
        self.total_disk_gb = gb
        self.disk_usage_label.setText(f"{gb:.1f} GB")

    def refresh_stats(self) -> None:
        """
        Refresh statistics by scanning file directories.

        Counts files created today in recording and snapshot directories.
        """
        if self.videos_path is None or self.snapshots_path is None:
            return

        today = datetime.now().date()
        segments_count = 0
        snapshots_count = 0
        total_size_bytes = 0

        # Count video segments from today
        if self.videos_path.exists():
            for file in self.videos_path.glob("*.mp4"):
                try:
                    file_time = datetime.fromtimestamp(file.stat().st_mtime)
                    if file_time.date() == today:
                        segments_count += 1
                    total_size_bytes += file.stat().st_size
                except Exception:
                    pass

        # Count snapshots from today
        if self.snapshots_path.exists():
            for file in self.snapshots_path.glob("*.jpg"):
                try:
                    file_time = datetime.fromtimestamp(file.stat().st_mtime)
                    if file_time.date() == today:
                        snapshots_count += 1
                    total_size_bytes += file.stat().st_size
                except Exception:
                    pass

        # Update displays
        self.update_segments_count(segments_count)
        self.update_snapshots_count(snapshots_count)
        self.update_disk_usage(total_size_bytes / (1024 ** 3))  # Convert to GB

    def increment_snapshot_count(self) -> None:
        """Increment snapshot count by 1."""
        self.update_snapshots_count(self.snapshots_today + 1)

    def reset_daily_stats(self) -> None:
        """Reset daily statistics (call at midnight)."""
        self.update_recording_time(0)
        self.update_segments_count(0)
        self.update_snapshots_count(0)

    def get_stats(self) -> dict:
        """
        Get current statistics as dictionary.

        Returns:
            Dictionary with all statistics
        """
        return {
            "recording_seconds_today": self.recording_seconds_today,
            "segments_today": self.segments_today,
            "snapshots_today": self.snapshots_today,
            "total_disk_gb": self.total_disk_gb
        }

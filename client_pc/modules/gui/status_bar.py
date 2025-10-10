"""
Status bar widget for displaying connection and recording status.

Shows real-time indicators for stream status, FPS, recording state, and uptime.
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt


class StatusBarWidget(QWidget):
    """
    Custom status bar showing stream and recording status.

    Displays:
    - Connection status with LED indicator
    - Current FPS
    - Recording status
    - Stream uptime
    """

    def __init__(self, parent=None):
        """Initialize status bar widget."""
        super().__init__(parent)

        # Create layout
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(20)

        # Connection status
        self.connection_indicator = QLabel("⚫")
        self.connection_indicator.setObjectName("statusLabel")
        self.connection_label = QLabel("STOPPED")
        self.connection_label.setObjectName("statusLabel")

        # FPS display
        self.fps_label = QLabel("FPS: 0.0")
        self.fps_label.setObjectName("statusLabel")

        # Recording status
        self.recording_indicator = QLabel("⚫")
        self.recording_indicator.setObjectName("statusLabel")
        self.recording_label = QLabel("NOT RECORDING")
        self.recording_label.setObjectName("statusLabel")

        # Uptime display
        self.uptime_label = QLabel("⏱️ 00:00:00")
        self.uptime_label.setObjectName("statusLabel")

        # Add widgets to layout
        layout.addWidget(self.connection_indicator)
        layout.addWidget(self.connection_label)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.fps_label)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.recording_indicator)
        layout.addWidget(self.recording_label)
        layout.addWidget(QLabel("|"))
        layout.addWidget(self.uptime_label)
        layout.addStretch()

        self.setLayout(layout)

        # Set initial style
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-bottom: 1px solid #3d3d3d;
            }
        """)

    def update_connection_status(self, status: str) -> None:
        """
        Update connection status display.

        Args:
            status: Status string ("running", "stopped", "reconnecting")
        """
        status_map = {
            "running": ("🟢", "CONNECTED", "#4caf50"),
            "stopped": ("⚫", "STOPPED", "#9e9e9e"),
            "reconnecting": ("🔴", "RECONNECTING", "#f44336")
        }

        indicator, text, _ = status_map.get(status, status_map["stopped"])
        self.connection_indicator.setText(indicator)
        self.connection_label.setText(text)

    def update_fps(self, fps: float) -> None:
        """
        Update FPS display.

        Args:
            fps: Current frames per second
        """
        self.fps_label.setText(f"FPS: {fps:.1f}")

    def update_recording_status(self, is_recording: bool, is_paused: bool = False) -> None:
        """
        Update recording status display.

        Args:
            is_recording: Whether recording is active
            is_paused: Whether recording is paused
        """
        if is_recording:
            if is_paused:
                self.recording_indicator.setText("🟡")
                self.recording_label.setText("PAUSED")
            else:
                self.recording_indicator.setText("🔴")
                self.recording_label.setText("RECORDING")
        else:
            self.recording_indicator.setText("⚫")
            self.recording_label.setText("NOT RECORDING")

    def update_uptime(self, uptime_seconds: int) -> None:
        """
        Update uptime display.

        Args:
            uptime_seconds: Stream uptime in seconds
        """
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        self.uptime_label.setText(f"⏱️ {hours:02d}:{minutes:02d}:{seconds:02d}")

    def reset(self) -> None:
        """Reset all status indicators to default state."""
        self.update_connection_status("stopped")
        self.update_fps(0.0)
        self.update_recording_status(False)
        self.update_uptime(0)

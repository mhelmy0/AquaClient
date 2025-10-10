"""
Log viewer widget for displaying application activity logs.

Shows recent log entries with color-coded severity levels.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QGroupBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor, QColor
from collections import deque


class LogViewer(QWidget):
    """
    Widget for displaying application logs.

    Maintains a scrolling list of recent log entries with syntax highlighting
    based on log level.
    """

    def __init__(self, max_lines: int = 50, parent=None):
        """
        Initialize log viewer.

        Args:
            max_lines: Maximum number of log lines to display
            parent: Parent widget
        """
        super().__init__(parent)

        self.max_lines = max_lines
        self.log_buffer = deque(maxlen=max_lines)

        # Create layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Create group box
        group = QGroupBox("📋 Activity Log")

        # Create text edit for logs
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMaximumHeight(150)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Group layout
        group_layout = QVBoxLayout()
        group_layout.addWidget(self.text_edit)
        group.setLayout(group_layout)

        layout.addWidget(group)
        self.setLayout(layout)

        # Color mapping for log levels
        self.level_colors = {
            "debug": QColor(150, 150, 150),      # Gray
            "info": QColor(255, 255, 255),       # White
            "service": QColor(76, 175, 80),      # Green
            "error": QColor(244, 67, 54),        # Red
            "warning": QColor(255, 193, 7),      # Yellow
        }

    def add_log(self, level: str, component: str, event: str, message: str) -> None:
        """
        Add a log entry to the viewer.

        Args:
            level: Log level (debug, info, service, error, warning)
            component: Component name (e.g., "stream_receiver")
            event: Event name (e.g., "input_opened")
            message: Log message
        """
        import datetime

        # Format timestamp
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # Format log entry
        log_entry = f"[{timestamp}] [{level.upper()}] {component}: {message}"

        # Add to buffer
        self.log_buffer.append((level, log_entry))

        # Update display
        self._update_display()

    def add_log_simple(self, level: str, message: str) -> None:
        """
        Add a simple log entry (without component/event details).

        Args:
            level: Log level
            message: Log message
        """
        import datetime

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level.upper()}] {message}"

        self.log_buffer.append((level, log_entry))
        self._update_display()

    def _update_display(self) -> None:
        """Update the text display with current log buffer."""
        # Clear text edit
        self.text_edit.clear()

        # Add all log entries with color coding
        for level, entry in self.log_buffer:
            color = self.level_colors.get(level.lower(), QColor(255, 255, 255))

            # Set text color
            self.text_edit.setTextColor(color)
            self.text_edit.append(entry)

        # Scroll to bottom
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_edit.setTextCursor(cursor)

    def clear(self) -> None:
        """Clear all log entries."""
        self.log_buffer.clear()
        self.text_edit.clear()

    def get_logs(self) -> list:
        """
        Get all current log entries.

        Returns:
            List of (level, message) tuples
        """
        return list(self.log_buffer)

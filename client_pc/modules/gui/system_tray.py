"""
System tray icon and menu for Aqua Stream Monitor.

Provides system tray integration with context menu and status indicators.
"""

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt, pyqtSignal, QObject


class SystemTrayIcon(QSystemTrayIcon):
    """
    System tray icon with context menu for quick access to application features.

    Signals:
        show_window: Emitted when user wants to show the main window
        hide_window: Emitted when user wants to hide the main window
        snapshot_requested: Emitted when user requests a snapshot
        start_recording_requested: Emitted when user requests to start recording
        stop_recording_requested: Emitted when user requests to stop recording
        pause_recording_requested: Emitted when user requests to pause recording
        exit_requested: Emitted when user wants to exit the application
    """

    show_window = pyqtSignal()
    hide_window = pyqtSignal()
    snapshot_requested = pyqtSignal()
    start_recording_requested = pyqtSignal()
    stop_recording_requested = pyqtSignal()
    pause_recording_requested = pyqtSignal()
    exit_requested = pyqtSignal()

    def __init__(self, parent=None):
        """Initialize system tray icon."""
        # Create initial icon
        icon = self._create_status_icon("gray")
        super().__init__(icon, parent)

        self.setToolTip("Aqua Stream Monitor")

        # Create context menu
        self.menu = QMenu()
        self._create_menu()
        self.setContextMenu(self.menu)

        # Connect signals
        self.activated.connect(self._on_activated)

        # Track window visibility
        self.window_visible = True

    def _create_status_icon(self, color: str) -> QIcon:
        """
        Create a status icon with specified color.

        Args:
            color: Color name (green, yellow, red, gray)

        Returns:
            QIcon with colored circle
        """
        # Create a 64x64 pixmap
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Map color names to QColor
        color_map = {
            "green": QColor(76, 175, 80),   # Streaming + Recording
            "yellow": QColor(255, 193, 7),  # Streaming only
            "red": QColor(244, 67, 54),     # Disconnected
            "gray": QColor(158, 158, 158)   # Stopped
        }

        # Draw filled circle
        painter.setBrush(color_map.get(color, color_map["gray"]))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(8, 8, 48, 48)

        painter.end()

        return QIcon(pixmap)

    def _create_menu(self) -> None:
        """Create the context menu."""
        # Show/Hide action
        self.show_hide_action = QAction("Hide Window", self.menu)
        self.show_hide_action.triggered.connect(self._toggle_window)
        self.menu.addAction(self.show_hide_action)

        self.menu.addSeparator()

        # Snapshot action
        snapshot_action = QAction("📷 Take Snapshot", self.menu)
        snapshot_action.triggered.connect(self.snapshot_requested.emit)
        self.menu.addAction(snapshot_action)

        # Recording actions
        self.start_recording_action = QAction("▶️ Start Recording", self.menu)
        self.start_recording_action.triggered.connect(self.start_recording_requested.emit)
        self.menu.addAction(self.start_recording_action)

        self.stop_recording_action = QAction("⏹️ Stop Recording", self.menu)
        self.stop_recording_action.triggered.connect(self.stop_recording_requested.emit)
        self.stop_recording_action.setEnabled(False)
        self.menu.addAction(self.stop_recording_action)

        self.pause_recording_action = QAction("⏸️ Pause Recording", self.menu)
        self.pause_recording_action.triggered.connect(self.pause_recording_requested.emit)
        self.pause_recording_action.setEnabled(False)
        self.menu.addAction(self.pause_recording_action)

        self.menu.addSeparator()

        # Quick stats action (placeholder)
        stats_action = QAction("📊 Quick Stats", self.menu)
        stats_action.setEnabled(False)  # TODO: Implement stats popup
        self.menu.addAction(stats_action)

        self.menu.addSeparator()

        # Exit action
        exit_action = QAction("❌ Exit", self.menu)
        exit_action.triggered.connect(self.exit_requested.emit)
        self.menu.addAction(exit_action)

    def _toggle_window(self) -> None:
        """Toggle window visibility."""
        if self.window_visible:
            self.hide_window.emit()
            self.window_visible = False
            self.show_hide_action.setText("Show Window")
        else:
            self.show_window.emit()
            self.window_visible = True
            self.show_hide_action.setText("Hide Window")

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """
        Handle tray icon activation.

        Args:
            reason: Activation reason (click, double-click, etc.)
        """
        if reason == QSystemTrayIcon.Trigger:  # Single click
            self._toggle_window()

    def update_status(self, status: str, recording: bool = False) -> None:
        """
        Update tray icon based on stream and recording status.

        Args:
            status: Stream status ("running", "stopped", "reconnecting")
            recording: Whether recording is active
        """
        if status == "running":
            if recording:
                color = "green"  # Streaming + Recording
                tooltip = "Aqua Stream Monitor - Recording"
            else:
                color = "yellow"  # Streaming only
                tooltip = "Aqua Stream Monitor - Streaming"
        elif status == "reconnecting":
            color = "red"  # Reconnecting
            tooltip = "Aqua Stream Monitor - Reconnecting..."
        else:
            color = "gray"  # Stopped
            tooltip = "Aqua Stream Monitor - Stopped"

        self.setIcon(self._create_status_icon(color))
        self.setToolTip(tooltip)

    def update_recording_state(self, is_recording: bool, is_paused: bool = False) -> None:
        """
        Update recording action states in the menu.

        Args:
            is_recording: Whether recording is active
            is_paused: Whether recording is paused
        """
        self.start_recording_action.setEnabled(not is_recording)
        self.stop_recording_action.setEnabled(is_recording)
        self.pause_recording_action.setEnabled(is_recording and not is_paused)

        if is_paused:
            self.pause_recording_action.setText("▶️ Resume Recording")
        else:
            self.pause_recording_action.setText("⏸️ Pause Recording")

    def set_window_visible(self, visible: bool) -> None:
        """
        Update window visibility state.

        Args:
            visible: Whether window is visible
        """
        self.window_visible = visible
        if visible:
            self.show_hide_action.setText("Hide Window")
        else:
            self.show_hide_action.setText("Show Window")

"""
Main window for Aqua Stream Monitor GUI.

Integrates all UI components and manages application state.
"""

import sys
import cv2
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMenuBar, QMenu, QAction, QMessageBox,
    QApplication
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QKeySequence, QCloseEvent

from .video_widget import VideoWidget
from .status_bar import StatusBarWidget
from .control_panel import ControlPanel
from .log_viewer import LogViewer
from .stats_panel import StatsPanel
from .system_tray import SystemTrayIcon
from .hotkey_manager import HotkeyManager
from .settings_dialog import SettingsDialog
from .themes import get_theme

from typing import Dict, Any, Optional


class MainWindow(QMainWindow):
    """
    Main application window.

    Provides the primary interface for monitoring and controlling the RTMP stream,
    recording, and snapshot functionality.

    Signals:
        stream_start_requested: Emitted when user wants to start streaming
        stream_stop_requested: Emitted when user wants to stop streaming
        recording_start_requested: Emitted when user wants to start recording
        recording_stop_requested: Emitted when user wants to stop recording
        recording_pause_requested: Emitted when user wants to pause recording
        recording_resume_requested: Emitted when user wants to resume recording
        snapshot_requested: Emitted when user wants to take a snapshot
    """

    stream_start_requested = pyqtSignal()
    stream_stop_requested = pyqtSignal()
    recording_start_requested = pyqtSignal()
    recording_stop_requested = pyqtSignal()
    recording_pause_requested = pyqtSignal()
    recording_resume_requested = pyqtSignal()
    snapshot_requested = pyqtSignal()

    def __init__(self, config: Dict[str, Any], parent=None):
        """
        Initialize main window.

        Args:
            config: Application configuration dictionary
            parent: Parent widget
        """
        super().__init__(parent)

        self.config = config
        self.is_fullscreen = False
        self.normal_geometry = None

        # Set window properties
        self.setWindowTitle("Aqua Stream Monitor")
        self.setMinimumSize(800, 600)

        # Load window settings
        window_config = config.get("ui", {}).get("window", {})
        self.resize(
            window_config.get("width", 1024),
            window_config.get("height", 768)
        )

        # Apply theme
        theme_name = window_config.get("theme", "dark")
        self.setStyleSheet(get_theme(theme_name))

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create status bar at top
        self.status_bar_widget = StatusBarWidget()
        main_layout.addWidget(self.status_bar_widget)

        # Create splitter for main content
        splitter = QSplitter(Qt.Horizontal)

        # Left side: Video and logs
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, 10, 10, 10)

        # Video widget
        self.video_widget = VideoWidget()
        self.video_widget.double_clicked.connect(self.toggle_fullscreen)
        left_layout.addWidget(self.video_widget, stretch=3)

        # Log viewer
        self.log_viewer = LogViewer()
        left_layout.addWidget(self.log_viewer, stretch=1)

        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)

        # Right side: Control panel and stats
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(10, 10, 10, 10)

        # Control panel
        self.control_panel = ControlPanel()
        self.control_panel.start_recording.connect(self._on_start_recording)
        self.control_panel.stop_recording.connect(self._on_stop_recording)
        self.control_panel.pause_recording.connect(self._on_pause_recording)
        self.control_panel.resume_recording.connect(self._on_resume_recording)
        self.control_panel.take_snapshot.connect(self._on_snapshot)
        self.control_panel.reconnect_stream.connect(self._on_reconnect)
        right_layout.addWidget(self.control_panel)

        # Stats panel
        self.stats_panel = StatsPanel()
        self.stats_panel.set_paths(
            config["recording"]["output_dir"],
            config["snapshots"]["output_dir"]
        )
        right_layout.addWidget(self.stats_panel)

        right_layout.addStretch()
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)

        # Set splitter sizes (70% left, 30% right)
        splitter.setSizes([700, 300])

        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)

        # Create menu bar
        self._create_menu_bar()

        # Create system tray icon
        tray_config = config.get("ui", {}).get("system_tray", {})
        if tray_config.get("enabled", True):
            self.tray_icon = SystemTrayIcon(self)
            self.tray_icon.show_window.connect(self.show)
            self.tray_icon.hide_window.connect(self.hide)
            self.tray_icon.snapshot_requested.connect(self._on_snapshot)
            self.tray_icon.start_recording_requested.connect(self._on_start_recording)
            self.tray_icon.stop_recording_requested.connect(self._on_stop_recording)
            self.tray_icon.pause_recording_requested.connect(self._on_pause_recording)
            self.tray_icon.exit_requested.connect(self.close)
            self.tray_icon.show()
        else:
            self.tray_icon = None

        # Create hotkey manager
        self.hotkey_manager = HotkeyManager(config.get("ui", {}))
        self.hotkey_manager.register_callback("snapshot", self._on_snapshot)
        self.hotkey_manager.register_callback("start_recording", self._on_start_recording)
        self.hotkey_manager.register_callback("stop_recording", self._on_stop_recording)
        self.hotkey_manager.register_callback("pause_recording", self._on_pause_recording)
        self.hotkey_manager.register_callback("show_hide_window", self._toggle_window_visibility)
        self.hotkey_manager.start()

        # Update timer for health monitoring
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_ui)
        self.update_timer.start(1000)  # Update every second

        # Stats refresh timer
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.stats_panel.refresh_stats)
        self.stats_timer.start(30000)  # Refresh every 30 seconds

        # Initialize UI
        self._initialize_ui()

        # Log startup
        self.log_viewer.add_log_simple("service", "GUI started successfully")

    def _create_menu_bar(self) -> None:
        """Create application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        settings_action = QAction("Settings", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Stream menu
        stream_menu = menubar.addMenu("Stream")

        connect_action = QAction("Connect", self)
        connect_action.triggered.connect(self._on_connect)
        stream_menu.addAction(connect_action)

        disconnect_action = QAction("Disconnect", self)
        disconnect_action.triggered.connect(self._on_disconnect)
        stream_menu.addAction(disconnect_action)

        # Recording menu
        recording_menu = menubar.addMenu("Recording")

        start_rec_action = QAction("Start Recording", self)
        start_rec_action.setShortcut(QKeySequence(self.config["ui"]["hotkeys"]["start_recording"]))
        start_rec_action.triggered.connect(self._on_start_recording)
        recording_menu.addAction(start_rec_action)

        stop_rec_action = QAction("Stop Recording", self)
        stop_rec_action.setShortcut(QKeySequence(self.config["ui"]["hotkeys"]["stop_recording"]))
        stop_rec_action.triggered.connect(self._on_stop_recording)
        recording_menu.addAction(stop_rec_action)

        # View menu
        view_menu = menubar.addMenu("View")

        fullscreen_action = QAction("Fullscreen", self)
        fullscreen_action.setShortcut(QKeySequence("F11"))
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        always_on_top_action = QAction("Always on Top", self)
        always_on_top_action.setCheckable(True)
        always_on_top_action.setChecked(self.config["ui"]["window"].get("always_on_top", False))
        always_on_top_action.triggered.connect(self._toggle_always_on_top)
        view_menu.addAction(always_on_top_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _initialize_ui(self) -> None:
        """Initialize UI components with current state."""
        self.control_panel.update_stream_url(self.config["stream"]["url"])
        self.status_bar_widget.reset()
        self.log_viewer.add_log_simple("info", "Ready to connect")

    def _update_ui(self) -> None:
        """Update UI components periodically."""
        # This will be called by external health monitor
        pass

    def _on_connect(self) -> None:
        """Handle connect button click."""
        url = self.config["stream"]["url"]
        self.log_viewer.add_log_simple("info", f"Connecting to {url}")

        # Start video stream
        fps_limit = self.config.get("ui", {}).get("preview", {}).get("fps_limit", 30)
        success = self.video_widget.start_stream(url, fps_limit)

        if success:
            self.status_bar_widget.update_connection_status("running")
            self.log_viewer.add_log_simple("service", "Stream connected")
            if self.tray_icon:
                self.tray_icon.update_status("running", False)
        else:
            self.status_bar_widget.update_connection_status("stopped")
            self.log_viewer.add_log_simple("error", "Failed to connect to stream")

    def _on_disconnect(self) -> None:
        """Handle disconnect button click."""
        self.video_widget.stop_stream()
        self.status_bar_widget.update_connection_status("stopped")
        self.log_viewer.add_log_simple("service", "Stream disconnected")
        if self.tray_icon:
            self.tray_icon.update_status("stopped", False)

    def _on_reconnect(self) -> None:
        """Handle reconnect button click."""
        self.log_viewer.add_log_simple("info", "Reconnecting to stream...")
        self.status_bar_widget.update_connection_status("reconnecting")

        success = self.video_widget.reconnect()

        if success:
            self.status_bar_widget.update_connection_status("running")
            self.log_viewer.add_log_simple("service", "Stream reconnected")
            if self.tray_icon:
                self.tray_icon.update_status("running", False)
        else:
            self.status_bar_widget.update_connection_status("stopped")
            self.log_viewer.add_log_simple("error", "Reconnection failed")

    def _on_start_recording(self) -> None:
        """Handle start recording."""
        self.log_viewer.add_log_simple("service", "Recording started")
        self.control_panel.set_recording_state(True, False)
        self.status_bar_widget.update_recording_status(True, False)
        if self.tray_icon:
            self.tray_icon.update_recording_state(True, False)
            self.tray_icon.update_status("running", True)
        self.recording_start_requested.emit()

    def _on_stop_recording(self) -> None:
        """Handle stop recording."""
        self.log_viewer.add_log_simple("service", "Recording stopped")
        self.control_panel.set_recording_state(False, False)
        self.status_bar_widget.update_recording_status(False, False)
        if self.tray_icon:
            self.tray_icon.update_recording_state(False, False)
            self.tray_icon.update_status("running", False)
        self.recording_stop_requested.emit()

    def _on_pause_recording(self) -> None:
        """Handle pause/resume recording."""
        is_paused = not self.control_panel.is_paused

        if is_paused:
            self.log_viewer.add_log_simple("info", "Recording paused")
            self.recording_pause_requested.emit()
        else:
            self.log_viewer.add_log_simple("service", "Recording resumed")
            self.recording_resume_requested.emit()

        self.control_panel.set_recording_state(True, is_paused)
        self.status_bar_widget.update_recording_status(True, is_paused)
        if self.tray_icon:
            self.tray_icon.update_recording_state(True, is_paused)

    def _on_resume_recording(self) -> None:
        """Handle resume recording from pause."""
        self.log_viewer.add_log_simple("service", "Recording resumed")
        self.control_panel.set_recording_state(True, False)
        self.status_bar_widget.update_recording_status(True, False)
        if self.tray_icon:
            self.tray_icon.update_recording_state(True, False)
        self.recording_resume_requested.emit()

    def _on_snapshot(self) -> None:
        """Handle snapshot request."""
        self.log_viewer.add_log_simple("service", "Snapshot captured")
        self.stats_panel.increment_snapshot_count()
        self.snapshot_requested.emit()

    def _toggle_window_visibility(self) -> None:
        """Toggle window visibility (for hotkey)."""
        if self.isVisible():
            self.hide()
            if self.tray_icon:
                self.tray_icon.set_window_visible(False)
        else:
            self.show()
            self.activateWindow()
            if self.tray_icon:
                self.tray_icon.set_window_visible(True)

    def _toggle_always_on_top(self, checked: bool) -> None:
        """Toggle always on top window flag."""
        if checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()  # Need to show after changing flags

    def toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode."""
        if self.is_fullscreen:
            # Exit fullscreen
            self.showNormal()
            if self.normal_geometry:
                self.setGeometry(self.normal_geometry)
            self.is_fullscreen = False
            self.log_viewer.add_log_simple("info", "Exited fullscreen")
        else:
            # Enter fullscreen
            self.normal_geometry = self.geometry()
            self.showFullScreen()
            self.is_fullscreen = True
            self.log_viewer.add_log_simple("info", "Entered fullscreen")

    def _open_settings(self) -> None:
        """Open settings dialog."""
        dialog = SettingsDialog(self.config, self)
        dialog.settings_changed.connect(self._apply_settings)
        dialog.exec_()

    def _apply_settings(self, new_config: Dict[str, Any]) -> None:
        """
        Apply new settings.

        Args:
            new_config: Updated configuration dictionary
        """
        self.config = new_config

        # Apply theme
        theme_name = new_config["ui"]["window"]["theme"]
        self.setStyleSheet(get_theme(theme_name))

        # Update stream URL
        self.control_panel.update_stream_url(new_config["stream"]["url"])

        # Restart hotkey manager with new settings
        self.hotkey_manager.stop()
        self.hotkey_manager = HotkeyManager(new_config.get("ui", {}))
        self.hotkey_manager.register_callback("snapshot", self._on_snapshot)
        self.hotkey_manager.register_callback("start_recording", self._on_start_recording)
        self.hotkey_manager.register_callback("stop_recording", self._on_stop_recording)
        self.hotkey_manager.register_callback("pause_recording", self._on_pause_recording)
        self.hotkey_manager.register_callback("show_hide_window", self._toggle_window_visibility)
        self.hotkey_manager.start()

        self.log_viewer.add_log_simple("service", "Settings applied")

    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Aqua Stream Monitor",
            "<h3>Aqua Stream Monitor</h3>"
            "<p>Version 1.0.0</p>"
            "<p>RTMP stream monitoring and recording application</p>"
            "<p>Built with PyQt5 and OpenCV</p>"
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handle window close event.

        Args:
            event: Close event
        """
        close_to_tray = self.config.get("ui", {}).get("system_tray", {}).get("close_to_tray", True)

        if close_to_tray and self.tray_icon and self.tray_icon.isVisible():
            # Minimize to tray instead of closing
            event.ignore()
            self.hide()
            if self.tray_icon:
                self.tray_icon.set_window_visible(False)
                self.tray_icon.showMessage(
                    "Aqua Stream Monitor",
                    "Application minimized to tray",
                    QSystemTrayIcon.Information,
                    2000
                )
        else:
            # Actually close
            self._cleanup()
            event.accept()

    def _cleanup(self) -> None:
        """Cleanup resources before exit."""
        self.log_viewer.add_log_simple("service", "Shutting down...")

        # Stop video stream
        self.video_widget.stop_stream()

        # Stop hotkeys
        self.hotkey_manager.stop()

        # Hide tray icon
        if self.tray_icon:
            self.tray_icon.hide()

    def update_health_status(self, health_data: Dict[str, Any]) -> None:
        """
        Update UI with health data from external monitor.

        Args:
            health_data: Health status dictionary
        """
        # Update status bar
        stream_status = health_data.get("stream", {}).get("status", "stopped")
        self.status_bar_widget.update_connection_status(stream_status)

        fps = health_data.get("fps", 0.0)
        self.status_bar_widget.update_fps(fps)

        uptime = int(health_data.get("stream", {}).get("uptime_s", 0))
        self.status_bar_widget.update_uptime(uptime)

        # Update disk space
        disk_free = health_data.get("disk_free_mib", 0) / 1024  # Convert to GB
        disk_total = 100.0  # TODO: Get actual total from system
        self.control_panel.update_disk_space(disk_free, disk_total)

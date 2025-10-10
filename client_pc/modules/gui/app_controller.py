"""
Application controller for bridging GUI and recording/snapshot modules.

Connects MainWindow signals to Recorder and Snapshotter instances.
"""

from typing import Dict, Any
from PyQt5.QtCore import QObject, QTimer
from pathlib import Path

from ..recorder import Recorder
from ..snapshotter import Snapshotter
from ..logging_json import JsonLogger


class AppController(QObject):
    """
    Controller that bridges GUI and backend functionality.

    Manages:
    - Recording start/stop/pause/resume
    - Snapshot capture
    - Disk space monitoring
    - Health status updates
    """

    def __init__(self, main_window, config: Dict[str, Any], logger: JsonLogger):
        """
        Initialize application controller.

        Args:
            main_window: MainWindow instance
            config: Application configuration
            logger: JSON logger instance
        """
        super().__init__()

        self.main_window = main_window
        self.config = config
        self.logger = logger

        # Initialize backend modules
        self.recorder = Recorder(config, logger)
        self.snapshotter = Snapshotter(config, logger)

        # Connect signals from main window
        self._connect_signals()

        # Setup periodic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start(1000)  # Update every second

        # Track recording state
        self.recording_start_time = 0

    def _connect_signals(self) -> None:
        """Connect MainWindow signals to controller methods."""
        self.main_window.recording_start_requested.connect(self.start_recording)
        self.main_window.recording_stop_requested.connect(self.stop_recording)
        self.main_window.recording_pause_requested.connect(self.pause_recording)
        self.main_window.recording_resume_requested.connect(self.resume_recording)
        self.main_window.snapshot_requested.connect(self.take_snapshot)

    def start_recording(self) -> None:
        """Start recording."""
        try:
            self.recorder.start()
            self.recording_start_time = 0
            self.logger.log("service", "gui_controller", "recording_started",
                          {}, "Recording started from GUI")
        except Exception as e:
            self.logger.log("error", "gui_controller", "recording_start_failed",
                          {"error": str(e)}, f"Failed to start recording: {e}")
            self.main_window.log_viewer.add_log_simple("error",
                                                       f"Failed to start recording: {e}")
            # Reset UI state on failure
            self.main_window.control_panel.set_recording_state(False, False)
            self.main_window.status_bar_widget.update_recording_status(False, False)

    def stop_recording(self) -> None:
        """Stop recording."""
        try:
            self.recorder.stop()
            self.recording_start_time = 0
            self.logger.log("service", "gui_controller", "recording_stopped",
                          {}, "Recording stopped from GUI")
        except Exception as e:
            self.logger.log("error", "gui_controller", "recording_stop_failed",
                          {"error": str(e)}, f"Failed to stop recording: {e}")
            self.main_window.log_viewer.add_log_simple("error",
                                                       f"Failed to stop recording: {e}")

    def pause_recording(self) -> None:
        """Pause recording."""
        try:
            # Since FFmpeg doesn't support pausing, we stop recording
            self.recorder.stop()
            self.recorder.is_paused = True
            self.logger.log("info", "gui_controller", "recording_paused",
                          {}, "Recording paused from GUI")
        except Exception as e:
            self.logger.log("error", "gui_controller", "recording_pause_failed",
                          {"error": str(e)}, f"Failed to pause recording: {e}")
            self.main_window.log_viewer.add_log_simple("error",
                                                       f"Failed to pause recording: {e}")

    def resume_recording(self) -> None:
        """Resume recording."""
        try:
            self.recorder.is_paused = False
            self.recorder.start()
            self.logger.log("service", "gui_controller", "recording_resumed",
                          {}, "Recording resumed from GUI")
        except Exception as e:
            self.logger.log("error", "gui_controller", "recording_resume_failed",
                          {"error": str(e)}, f"Failed to resume recording: {e}")
            self.main_window.log_viewer.add_log_simple("error",
                                                       f"Failed to resume recording: {e}")

    def take_snapshot(self) -> None:
        """Take a snapshot."""
        try:
            snapshot_path = self.snapshotter.capture()
            self.logger.log("service", "gui_controller", "snapshot_captured",
                          {"path": str(snapshot_path)}, f"Snapshot saved: {snapshot_path.name}")
            self.main_window.log_viewer.add_log_simple("service",
                                                       f"Snapshot saved: {snapshot_path.name}")
        except Exception as e:
            self.logger.log("error", "gui_controller", "snapshot_failed",
                          {"error": str(e)}, f"Failed to take snapshot: {e}")
            self.main_window.log_viewer.add_log_simple("error",
                                                       f"Failed to take snapshot: {e}")

    def _update_status(self) -> None:
        """Update GUI status displays periodically."""
        try:
            # Monitor recorder process
            self.recorder.monitor()

            # Update disk space
            disk_free_mib = self.recorder.get_disk_free_mib()
            disk_free_gb = disk_free_mib / 1024

            # Get total disk space
            import psutil
            usage = psutil.disk_usage(str(self.recorder.output_dir))
            disk_total_gb = usage.total / (1024 ** 3)

            # Update control panel disk space
            self.main_window.control_panel.update_disk_space(disk_free_gb, disk_total_gb)

            # Update recording state
            is_recording = self.recorder.is_running()

            # If recording state changed unexpectedly, update UI
            if is_recording != self.main_window.control_panel.is_recording:
                if not is_recording and self.main_window.control_panel.is_recording:
                    # Recording stopped unexpectedly
                    self.main_window.log_viewer.add_log_simple("error",
                                                               "Recording stopped unexpectedly")
                    self.main_window.control_panel.set_recording_state(False, False)
                    self.main_window.status_bar_widget.update_recording_status(False, False)
                    if self.main_window.tray_icon:
                        self.main_window.tray_icon.update_recording_state(False, False)

            # Update recording progress if recording
            if is_recording:
                segment_seconds = self.config["recording"]["segment_seconds"]
                self.recording_start_time += 1
                elapsed = self.recording_start_time % segment_seconds
                self.main_window.control_panel.update_segment_progress(elapsed, segment_seconds)

        except Exception as e:
            self.logger.log("error", "gui_controller", "update_status_failed",
                          {"error": str(e)}, f"Failed to update status: {e}")

    def cleanup(self) -> None:
        """Cleanup resources."""
        self.update_timer.stop()

        # Stop recording if active
        if self.recorder.is_running():
            self.recorder.stop()

"""
RTP-enabled GUI application entry point.

Integrates RTP streaming, recording, and Raspberry Pi health monitoring.
"""

import sys
import logging
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from modules.config import load_config
from modules.gui.main_window import MainWindow
from modules.rtp_receiver import RTPReceiver
from modules.rtp_recorder import RTPRecorder, RTPSnapshotCapture
from modules.pi_health_monitor import PiHealthMonitor


class RTPApplication:
    """
    Main RTP application with GUI.

    Integrates all RTP streaming, recording, and monitoring components.
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize RTP application.

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = load_config(config_path)

        # Setup logging
        log_config = self.config.get("logging", {})
        log_file = Path(log_config.get("file", "logs/client.log"))
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Configure logging
        log_level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "service": logging.INFO,
            "error": logging.ERROR
        }
        log_level = log_level_map.get(log_config.get("level", "info").lower(), logging.INFO)

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Initialize Qt application
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Aqua RTP Monitor")

        # Get configuration sections
        stream_config = self.config.get("stream", {})
        rtp_config = stream_config.get("rtp", {})
        pi_health_config = self.config.get("health", {}).get("pi_health", {})
        recording_config = self.config.get("recording", {})
        quality_config = recording_config.get("quality", {})

        # Initialize RTP receiver
        self.rtp_receiver = RTPReceiver(
            server_ip=rtp_config.get("server_ip", "192.168.100.23"),
            logger=self.logger
        )

        # Initialize RTP recorder
        self.rtp_recorder = RTPRecorder(
            output_dir=recording_config.get("output_dir", "records/videos"),
            quality=quality_config.get("preset", "high"),
            logger=self.logger
        )

        # Initialize snapshot capture
        self.snapshot_capture = RTPSnapshotCapture(
            output_dir=self.config.get("snapshots", {}).get("output_dir", "records/snapshots"),
            logger=self.logger
        )

        # Initialize Pi health monitor
        if pi_health_config.get("enabled", True):
            self.pi_health = PiHealthMonitor(
                pi_ip=rtp_config.get("server_ip", "192.168.100.23"),
                logger=self.logger
            )
        else:
            self.pi_health = None

        # Initialize main window
        self.main_window = MainWindow(self.config)

        # Connect signals
        self._connect_signals()

        # Setup timers
        self._setup_timers()

        # Always use manual SDP for simplicity
        manual_sdp = rtp_config.get("manual_sdp", "")
        if manual_sdp:
            self.logger.info("Using manual SDP configuration")
            self.rtp_receiver.use_manual_sdp(manual_sdp)
            self._setup_manual_sdp()
        else:
            self.logger.warning("No manual SDP configured in config.yaml")

    def _connect_signals(self) -> None:
        """Connect GUI signals to handlers."""
        # Recording controls
        self.main_window.recording_start_requested.connect(self._on_start_recording)
        self.main_window.recording_stop_requested.connect(self._on_stop_recording)
        self.main_window.recording_pause_requested.connect(self._on_pause_recording)
        self.main_window.recording_resume_requested.connect(self._on_resume_recording)

        # Snapshot
        self.main_window.snapshot_requested.connect(self._on_snapshot)

        # Stream controls
        self.main_window.stream_start_requested.connect(self._on_start_stream)
        self.main_window.stream_stop_requested.connect(self._on_stop_stream)

    def _setup_timers(self) -> None:
        """Setup periodic update timers."""
        # Pi health update timer
        if self.pi_health:
            self.pi_health_timer = QTimer()
            self.pi_health_timer.timeout.connect(self._update_pi_health)

            update_interval = self.config.get("health", {}).get("pi_health", {}).get("update_interval", 5)
            self.pi_health_timer.start(update_interval * 1000)  # Convert to ms

    def _setup_manual_sdp(self) -> None:
        """Setup manual SDP configuration."""
        # Get stream URL from config
        stream_url = self.rtp_receiver.get_stream_url()
        if stream_url:
            self.logger.info(f"Stream URL ready: {stream_url}")
            self.main_window.control_panel.update_stream_url(stream_url)
            self.main_window.log_viewer.add_log_simple("service", f"Manual SDP configured: {stream_url}")
        else:
            self.logger.error("Failed to get stream URL from SDP")
            self.main_window.log_viewer.add_log_simple("error", "No stream URL available")

    def _update_pi_health(self) -> None:
        """Update Raspberry Pi health metrics."""
        if not self.pi_health:
            return

        health_data = self.pi_health.fetch_health()
        if health_data:
            # Get health summary
            summary = self.pi_health.get_summary()

            # Update control panel
            self.main_window.control_panel.update_pi_health(summary)

            # Check for critical conditions
            status = summary.get('status')
            if status == 'critical':
                self.main_window.log_viewer.add_log_simple(
                    "error",
                    f"Pi health critical! Temp: {summary.get('temperature', 'N/A')}°C, "
                    f"CPU: {summary.get('cpu_usage', 'N/A')}%"
                )
        else:
            # Connection lost
            self.main_window.control_panel.update_pi_health({
                'status': 'disconnected',
                'temperature': None,
                'cpu_usage': None,
                'uptime_formatted': None
            })

    def _on_start_stream(self) -> None:
        """Handle stream start request."""
        stream_url = self.rtp_receiver.get_stream_url()
        if not stream_url:
            self.logger.error("No stream URL available")
            self.main_window.log_viewer.add_log_simple("error", "No stream URL - check SDP configuration")
            return

        self.logger.info(f"Starting RTP stream: {stream_url}")
        self.main_window.log_viewer.add_log_simple("info", f"Starting stream: {stream_url}")

        # Start RTP receiver
        if self.rtp_receiver.start():
            # Start video widget with RTP stream
            fps_limit = self.config.get("ui", {}).get("preview", {}).get("fps_limit", 30)
            success = self.main_window.video_widget.start_stream(stream_url, 'rtp', fps_limit)

            if success:
                self.main_window.log_viewer.add_log_simple("service", "RTP stream connected")
            else:
                self.main_window.log_viewer.add_log_simple("error", "Failed to start video preview")
        else:
            self.main_window.log_viewer.add_log_simple("error", "Failed to start RTP receiver")

    def _on_stop_stream(self) -> None:
        """Handle stream stop request."""
        self.logger.info("Stopping RTP stream")
        self.rtp_receiver.stop()
        self.main_window.video_widget.stop_stream()
        self.main_window.log_viewer.add_log_simple("service", "Stream stopped")

    def _on_start_recording(self) -> None:
        """Handle recording start request."""
        stream_url = self.rtp_receiver.get_stream_url()
        if not stream_url:
            self.logger.error("No stream URL available for recording")
            self.main_window.log_viewer.add_log_simple("error", "Cannot record - no stream URL")
            return

        self.logger.info("Starting RTP recording")

        # Get segment duration
        segment_duration = self.config.get("recording", {}).get("segment_seconds")

        # Start recording
        if self.rtp_recorder.start_recording(stream_url, segment_duration=segment_duration):
            self.main_window.log_viewer.add_log_simple("service", "Recording started")

            # Update UI with filename
            status = self.rtp_recorder.get_status()
            if status.get('current_file'):
                filename = Path(status['current_file']).name
                self.main_window.control_panel.update_recording_file(filename)
        else:
            self.main_window.log_viewer.add_log_simple("error", "Failed to start recording")

    def _on_stop_recording(self) -> None:
        """Handle recording stop request."""
        self.logger.info("Stopping recording")

        if self.rtp_recorder.stop_recording():
            self.main_window.log_viewer.add_log_simple("service", "Recording stopped")
            self.main_window.control_panel.update_recording_file("")
        else:
            self.main_window.log_viewer.add_log_simple("error", "Failed to stop recording")

    def _on_pause_recording(self) -> None:
        """Handle recording pause request."""
        self.rtp_recorder.pause_recording()
        self.main_window.log_viewer.add_log_simple("info", "Recording paused")

    def _on_resume_recording(self) -> None:
        """Handle recording resume request."""
        self.rtp_recorder.resume_recording()
        self.main_window.log_viewer.add_log_simple("service", "Recording resumed")

    def _on_snapshot(self) -> None:
        """Handle snapshot request."""
        stream_url = self.rtp_receiver.get_stream_url()
        if not stream_url:
            self.logger.error("No stream URL available for snapshot")
            self.main_window.log_viewer.add_log_simple("error", "Cannot take snapshot - no stream")
            return

        self.logger.info("Capturing snapshot")
        self.main_window.log_viewer.add_log_simple("info", "Capturing snapshot...")

        snapshot_path = self.snapshot_capture.capture_snapshot(stream_url)
        if snapshot_path:
            self.main_window.log_viewer.add_log_simple("service", f"Snapshot saved: {Path(snapshot_path).name}")
        else:
            self.main_window.log_viewer.add_log_simple("error", "Snapshot capture failed")

    def run(self) -> int:
        """
        Run the application.

        Returns:
            Application exit code
        """
        self.main_window.show()
        self.logger.info("RTP GUI application started")

        # Start initial health check
        if self.pi_health:
            self._update_pi_health()

        return self.app.exec_()

    def cleanup(self) -> None:
        """Cleanup resources before exit."""
        self.logger.info("Cleaning up...")

        if self.rtp_recorder.is_recording:
            self.rtp_recorder.stop_recording()

        self.rtp_receiver.stop()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Aqua RTP Monitor GUI")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file"
    )
    args = parser.parse_args()

    app = RTPApplication(args.config)

    try:
        exit_code = app.run()
    finally:
        app.cleanup()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

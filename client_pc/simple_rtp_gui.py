"""
Simplified RTP GUI - Minimal complexity version.

Uses manual SDP configuration and direct FFmpeg/FFplay for streaming.
"""

import sys
import logging
import subprocess
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer

from modules.config import load_config
from modules.rtp_receiver import RTPReceiver


class SimpleRTPWindow(QMainWindow):
    """Simple RTP streaming window."""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)

        # RTP receiver
        rtp_config = config.get("stream", {}).get("rtp", {})
        self.rtp_receiver = RTPReceiver(
            server_ip=rtp_config.get("server_ip", "192.168.100.23"),
            logger=self.logger
        )

        # Setup manual SDP
        manual_sdp = rtp_config.get("manual_sdp", "")
        if manual_sdp:
            self.rtp_receiver.use_manual_sdp(manual_sdp)
            self.logger.info("Manual SDP loaded")

        # FFplay process
        self.ffplay_process = None

        self.setup_ui()

    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Simple RTP Stream Viewer")
        self.setMinimumSize(800, 600)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Info group
        info_group = QGroupBox("Stream Information")
        info_layout = QVBoxLayout()

        stream_url = self.rtp_receiver.get_stream_url()
        self.url_label = QLabel(f"Stream URL: {stream_url or 'Not configured'}")
        info_layout.addWidget(self.url_label)

        sdp_info = self.rtp_receiver.get_info()
        if sdp_info.get('sdp_params'):
            params = sdp_info['sdp_params']
            info_text = f"Port: {params.get('port', 'N/A')}, Codec: {params.get('codec', 'N/A')}"
            self.info_label = QLabel(info_text)
            info_layout.addWidget(self.info_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Control buttons
        button_group = QGroupBox("Controls")
        button_layout = QHBoxLayout()

        self.play_button = QPushButton("▶ Play Stream with FFplay")
        self.play_button.clicked.connect(self.play_stream)
        self.play_button.setMinimumHeight(50)
        button_layout.addWidget(self.play_button)

        self.stop_button = QPushButton("⏹ Stop")
        self.stop_button.clicked.connect(self.stop_stream)
        self.stop_button.setEnabled(False)
        self.stop_button.setMinimumHeight(50)
        button_layout.addWidget(self.stop_button)

        button_group.setLayout(button_layout)
        layout.addWidget(button_group)

        # Log viewer
        log_group = QGroupBox("Logs")
        log_layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # Instructions
        instructions = QLabel(
            "Instructions:\n"
            "1. Make sure your Raspberry Pi is streaming to UDP port 5000\n"
            "2. Add Windows Firewall rule: netsh advfirewall firewall add rule name=\"RTP Port 5000\" dir=in action=allow protocol=UDP localport=5000\n"
            "3. Click 'Play Stream' to view the video\n\n"
            "Note: FFplay will open in a separate window"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(instructions)

        self.log("Application started")
        self.log(f"Stream URL: {stream_url}")

    def log(self, message):
        """Add message to log viewer."""
        self.log_text.append(message)
        self.logger.info(message)

    def play_stream(self):
        """Play the RTP stream using FFplay with SDP file."""
        stream_url = self.rtp_receiver.get_stream_url()

        if not stream_url:
            self.log("ERROR: No stream URL available")
            return

        # Create SDP file for FFplay
        sdp_file = Path("stream.sdp")
        try:
            if self.rtp_receiver.save_sdp_file(str(sdp_file)):
                self.log(f"SDP file created: {sdp_file}")
            else:
                self.log("WARNING: Could not create SDP file, using direct URL")
                sdp_file = None
        except Exception as e:
            self.log(f"WARNING: SDP file creation failed: {e}")
            sdp_file = None

        # Use SDP file if available, otherwise use direct URL
        if sdp_file and sdp_file.exists():
            input_source = str(sdp_file)
            self.log(f"Starting FFplay with SDP file: {input_source}")
        else:
            input_source = stream_url
            self.log(f"Starting FFplay with URL: {input_source}")

        try:
            # FFplay command with minimal buffering and fast startup
            cmd = [
                'ffplay',
                '-protocol_whitelist', 'file,udp,rtp',
                '-fflags', 'nobuffer',
                '-flags', 'low_delay',
                '-framedrop',
                '-probesize', '32',           # Reduce probe size for faster startup
                '-analyzeduration', '0',      # Don't wait to analyze stream
                '-sync', 'ext',               # External clock sync
                '-i', input_source,
                '-window_title', 'RTP Stream from Raspberry Pi'
            ]

            self.log(f"Command: {' '.join(cmd)}")

            # Start FFplay process
            self.ffplay_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            self.log("FFplay started successfully")
            self.log("Video should appear in a separate window")

            self.play_button.setEnabled(False)
            self.stop_button.setEnabled(True)

            # Monitor process
            QTimer.singleShot(1000, self.check_process)

        except FileNotFoundError:
            self.log("ERROR: FFplay not found!")
            self.log("Please install FFmpeg and add to PATH")
            self.log("Download from: https://ffmpeg.org/download.html")
        except Exception as e:
            self.log(f"ERROR: {e}")

    def check_process(self):
        """Check if FFplay process is still running."""
        if self.ffplay_process:
            if self.ffplay_process.poll() is None:
                # Still running
                QTimer.singleShot(1000, self.check_process)
            else:
                # Process exited
                self.log("FFplay exited")
                self.play_button.setEnabled(True)
                self.stop_button.setEnabled(False)

                # Try to get error output
                try:
                    stderr = self.ffplay_process.stderr.read().decode('utf-8', errors='ignore')
                    if stderr:
                        self.log(f"FFplay errors:\n{stderr[-500:]}")  # Last 500 chars
                except:
                    pass

    def stop_stream(self):
        """Stop the FFplay process."""
        if self.ffplay_process:
            self.log("Stopping FFplay...")
            self.ffplay_process.terminate()
            try:
                self.ffplay_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.ffplay_process.kill()

            self.ffplay_process = None
            self.log("FFplay stopped")

        self.play_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def closeEvent(self, event):
        """Handle window close."""
        self.stop_stream()
        event.accept()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Simple RTP Stream Viewer")
    parser.add_argument("--config", default="config.yaml", help="Config file path")
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/simple_rtp.log"),
            logging.StreamHandler()
        ]
    )

    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    # Load config
    config = load_config(args.config)

    # Create application
    app = QApplication(sys.argv)
    window = SimpleRTPWindow(config)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

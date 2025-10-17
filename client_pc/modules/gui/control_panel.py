"""
Control panel widget for recording and snapshot controls.

Provides buttons and controls for managing recording, snapshots, and reconnection.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QGroupBox, QLabel, QProgressBar
)
from PyQt5.QtCore import pyqtSignal, Qt


class ControlPanel(QWidget):
    """
    Control panel with recording and snapshot controls.

    Signals:
        start_recording: Emitted when user clicks start recording
        stop_recording: Emitted when user clicks stop recording
        pause_recording: Emitted when user clicks pause recording
        resume_recording: Emitted when user clicks resume recording
        take_snapshot: Emitted when user clicks snapshot button
        reconnect_stream: Emitted when user clicks reconnect button
    """

    start_recording = pyqtSignal()
    stop_recording = pyqtSignal()
    pause_recording = pyqtSignal()
    resume_recording = pyqtSignal()
    take_snapshot = pyqtSignal()
    reconnect_stream = pyqtSignal()

    def __init__(self, parent=None):
        """Initialize control panel."""
        super().__init__(parent)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        # Recording controls group
        recording_group = QGroupBox("Recording Controls")
        recording_layout = QHBoxLayout()

        # Start/Stop Recording button
        self.record_button = QPushButton("▶️ Start Recording")
        self.record_button.setObjectName("recordButton")
        self.record_button.setMinimumHeight(40)
        self.record_button.clicked.connect(self._on_record_clicked)
        recording_layout.addWidget(self.record_button)

        # Pause/Resume button
        self.pause_button = QPushButton("⏸️ Pause")
        self.pause_button.setMinimumHeight(40)
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self._on_pause_clicked)
        recording_layout.addWidget(self.pause_button)

        # Stop button
        self.stop_button = QPushButton("⏹️ Stop")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        recording_layout.addWidget(self.stop_button)

        recording_group.setLayout(recording_layout)
        main_layout.addWidget(recording_group)

        # Quick actions group
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout()

        # Snapshot button
        self.snapshot_button = QPushButton("📷 Take Snapshot")
        self.snapshot_button.setObjectName("snapshotButton")
        self.snapshot_button.setMinimumHeight(40)
        self.snapshot_button.clicked.connect(self.take_snapshot.emit)
        actions_layout.addWidget(self.snapshot_button)

        # Reconnect button
        self.reconnect_button = QPushButton("🔌 Reconnect Stream")
        self.reconnect_button.setMinimumHeight(40)
        self.reconnect_button.clicked.connect(self.reconnect_stream.emit)
        actions_layout.addWidget(self.reconnect_button)

        actions_group.setLayout(actions_layout)
        main_layout.addWidget(actions_group)

        # Raspberry Pi Health group
        pi_health_group = QGroupBox("🍓 Raspberry Pi Health")
        pi_health_layout = QVBoxLayout()

        # Pi connection status
        self.pi_status_label = QLabel("Status: Disconnected")
        pi_health_layout.addWidget(self.pi_status_label)

        # Temperature
        self.pi_temp_label = QLabel("Temperature: N/A")
        pi_health_layout.addWidget(self.pi_temp_label)

        # Temperature progress bar
        self.pi_temp_progress = QProgressBar()
        self.pi_temp_progress.setMaximum(100)
        self.pi_temp_progress.setValue(0)
        self.pi_temp_progress.setTextVisible(True)
        self.pi_temp_progress.setFormat("%v°C")
        pi_health_layout.addWidget(self.pi_temp_progress)

        # CPU usage
        self.pi_cpu_label = QLabel("CPU Usage: N/A")
        pi_health_layout.addWidget(self.pi_cpu_label)

        # CPU usage progress bar
        self.pi_cpu_progress = QProgressBar()
        self.pi_cpu_progress.setMaximum(100)
        self.pi_cpu_progress.setValue(0)
        self.pi_cpu_progress.setTextVisible(True)
        self.pi_cpu_progress.setFormat("%p%")
        pi_health_layout.addWidget(self.pi_cpu_progress)

        # Uptime
        self.pi_uptime_label = QLabel("Uptime: N/A")
        pi_health_layout.addWidget(self.pi_uptime_label)

        pi_health_group.setLayout(pi_health_layout)
        main_layout.addWidget(pi_health_group)

        # Local Health info group
        health_group = QGroupBox("💻 Local System")
        health_layout = QVBoxLayout()

        # Stream URL display
        self.stream_url_label = QLabel("Stream: Not connected")
        health_layout.addWidget(self.stream_url_label)

        # Quality info
        self.quality_label = QLabel("Quality: N/A")
        health_layout.addWidget(self.quality_label)

        # Disk space info
        self.disk_label = QLabel("Disk Free: N/A")
        health_layout.addWidget(self.disk_label)

        # Disk space progress bar
        self.disk_progress = QProgressBar()
        self.disk_progress.setMaximum(100)
        self.disk_progress.setValue(0)
        self.disk_progress.setTextVisible(True)
        self.disk_progress.setFormat("%p%")
        health_layout.addWidget(self.disk_progress)

        # Current recording file
        self.recording_file_label = QLabel("Recording: N/A")
        health_layout.addWidget(self.recording_file_label)

        # Segment progress
        self.segment_label = QLabel("Segment: N/A")
        health_layout.addWidget(self.segment_label)

        # Segment progress bar
        self.segment_progress = QProgressBar()
        self.segment_progress.setMaximum(100)
        self.segment_progress.setValue(0)
        self.segment_progress.setTextVisible(True)
        self.segment_progress.setFormat("%p%")
        health_layout.addWidget(self.segment_progress)

        health_group.setLayout(health_layout)
        main_layout.addWidget(health_group)

        main_layout.addStretch()
        self.setLayout(main_layout)

        # Track recording state
        self.is_recording = False
        self.is_paused = False

    def _on_record_clicked(self) -> None:
        """Handle record button click."""
        if not self.is_recording:
            self.start_recording.emit()
        else:
            # This shouldn't happen, but handle it anyway
            self.stop_recording.emit()

    def _on_pause_clicked(self) -> None:
        """Handle pause button click."""
        if self.is_paused:
            self.resume_recording.emit()
        else:
            self.pause_recording.emit()

    def _on_stop_clicked(self) -> None:
        """Handle stop button click."""
        self.stop_recording.emit()

    def set_recording_state(self, is_recording: bool, is_paused: bool = False) -> None:
        """
        Update UI based on recording state.

        Args:
            is_recording: Whether recording is active
            is_paused: Whether recording is paused
        """
        self.is_recording = is_recording
        self.is_paused = is_paused

        if is_recording:
            self.record_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.pause_button.setEnabled(True)

            if is_paused:
                self.pause_button.setText("▶️ Resume")
            else:
                self.pause_button.setText("⏸️ Pause")
        else:
            self.record_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.pause_button.setEnabled(False)
            self.pause_button.setText("⏸️ Pause")

    def update_stream_url(self, url: str) -> None:
        """
        Update stream URL display.

        Args:
            url: RTMP stream URL
        """
        self.stream_url_label.setText(f"Stream: {url}")

    def update_quality(self, resolution: str, bitrate: str) -> None:
        """
        Update video quality display.

        Args:
            resolution: Video resolution (e.g., "1920x1080")
            bitrate: Video bitrate (e.g., "2.5 Mbps")
        """
        self.quality_label.setText(f"Quality: {resolution} @ {bitrate}")

    def update_disk_space(self, free_gb: float, total_gb: float) -> None:
        """
        Update disk space display.

        Args:
            free_gb: Free disk space in GB
            total_gb: Total disk space in GB
        """
        self.disk_label.setText(f"Disk Free: {free_gb:.1f} GB / {total_gb:.1f} GB")

        # Update progress bar
        used_percent = int(((total_gb - free_gb) / total_gb) * 100) if total_gb > 0 else 0
        self.disk_progress.setValue(used_percent)

        # Color coding based on free space
        if free_gb < 1.0:  # Less than 1 GB
            self.disk_progress.setStyleSheet("QProgressBar::chunk { background-color: #f44336; }")
        elif free_gb < 5.0:  # Less than 5 GB
            self.disk_progress.setStyleSheet("QProgressBar::chunk { background-color: #ff9800; }")
        else:
            self.disk_progress.setStyleSheet("QProgressBar::chunk { background-color: #4caf50; }")

    def update_recording_file(self, filename: str) -> None:
        """
        Update current recording filename display.

        Args:
            filename: Current recording filename
        """
        if filename:
            self.recording_file_label.setText(f"Recording: {filename}")
        else:
            self.recording_file_label.setText("Recording: N/A")

    def update_segment_progress(self, elapsed_seconds: int, total_seconds: int) -> None:
        """
        Update segment progress display.

        Args:
            elapsed_seconds: Elapsed time in current segment
            total_seconds: Total segment duration
        """
        elapsed_h = elapsed_seconds // 3600
        elapsed_m = (elapsed_seconds % 3600) // 60
        elapsed_s = elapsed_seconds % 60

        total_h = total_seconds // 3600
        total_m = (total_seconds % 3600) // 60
        total_s = total_seconds % 60

        self.segment_label.setText(
            f"Segment: {elapsed_h:02d}:{elapsed_m:02d}:{elapsed_s:02d} / "
            f"{total_h:02d}:{total_m:02d}:{total_s:02d}"
        )

        # Update progress bar
        progress_percent = int((elapsed_seconds / total_seconds) * 100) if total_seconds > 0 else 0
        self.segment_progress.setValue(progress_percent)

    def update_pi_health(self, health_data: dict) -> None:
        """
        Update Raspberry Pi health display.

        Args:
            health_data: Dictionary containing Pi health metrics
        """
        # Update connection status
        status = health_data.get('status', 'disconnected')
        if status == 'healthy':
            self.pi_status_label.setText("Status: ✅ Healthy")
            self.pi_status_label.setStyleSheet("color: #4caf50;")
        elif status == 'warning':
            self.pi_status_label.setText("Status: ⚠️ Warning")
            self.pi_status_label.setStyleSheet("color: #ff9800;")
        elif status == 'critical':
            self.pi_status_label.setText("Status: ❌ Critical")
            self.pi_status_label.setStyleSheet("color: #f44336;")
        else:
            self.pi_status_label.setText("Status: Disconnected")
            self.pi_status_label.setStyleSheet("color: #666;")

        # Update temperature
        temperature = health_data.get('temperature')
        if temperature is not None:
            temp_int = int(temperature)
            self.pi_temp_label.setText(f"Temperature: {temperature:.1f}°C")
            self.pi_temp_progress.setValue(temp_int)

            # Color coding
            if temp_int > 80:
                self.pi_temp_progress.setStyleSheet("QProgressBar::chunk { background-color: #f44336; }")
            elif temp_int > 70:
                self.pi_temp_progress.setStyleSheet("QProgressBar::chunk { background-color: #ff9800; }")
            else:
                self.pi_temp_progress.setStyleSheet("QProgressBar::chunk { background-color: #4caf50; }")
        else:
            self.pi_temp_label.setText("Temperature: N/A")
            self.pi_temp_progress.setValue(0)

        # Update CPU usage
        cpu_usage = health_data.get('cpu_usage')
        if cpu_usage is not None:
            cpu_int = int(cpu_usage)
            self.pi_cpu_label.setText(f"CPU Usage: {cpu_usage:.1f}%")
            self.pi_cpu_progress.setValue(cpu_int)

            # Color coding
            if cpu_int > 90:
                self.pi_cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #f44336; }")
            elif cpu_int > 70:
                self.pi_cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #ff9800; }")
            else:
                self.pi_cpu_progress.setStyleSheet("QProgressBar::chunk { background-color: #4caf50; }")
        else:
            self.pi_cpu_label.setText("CPU Usage: N/A")
            self.pi_cpu_progress.setValue(0)

        # Update uptime
        uptime_str = health_data.get('uptime_formatted')
        if uptime_str:
            self.pi_uptime_label.setText(f"Uptime: {uptime_str}")
        else:
            self.pi_uptime_label.setText("Uptime: N/A")

    def reset(self) -> None:
        """Reset all displays to default state."""
        self.set_recording_state(False)
        self.stream_url_label.setText("Stream: Not connected")
        self.quality_label.setText("Quality: N/A")
        self.disk_label.setText("Disk Free: N/A")
        self.disk_progress.setValue(0)
        self.recording_file_label.setText("Recording: N/A")
        self.segment_label.setText("Segment: N/A")
        self.segment_progress.setValue(0)

        # Reset Pi health
        self.pi_status_label.setText("Status: Disconnected")
        self.pi_status_label.setStyleSheet("color: #666;")
        self.pi_temp_label.setText("Temperature: N/A")
        self.pi_temp_progress.setValue(0)
        self.pi_cpu_label.setText("CPU Usage: N/A")
        self.pi_cpu_progress.setValue(0)
        self.pi_uptime_label.setText("Uptime: N/A")

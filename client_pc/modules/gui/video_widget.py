"""
Video display widget for live RTMP stream preview.

Displays live video feed using OpenCV for frame capture and Qt for rendering.
"""

import cv2
import numpy as np
from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from typing import Optional


class VideoWidget(QLabel):
    """
    Widget for displaying live video stream.

    Captures frames from RTMP stream using OpenCV and displays them
    in a QLabel with proper aspect ratio handling.

    Signals:
        double_clicked: Emitted when widget is double-clicked (for fullscreen toggle)
    """

    double_clicked = pyqtSignal()

    def __init__(self, parent=None):
        """Initialize video widget."""
        super().__init__(parent)

        # Widget configuration
        self.setObjectName("videoLabel")
        self.setAlignment(Qt.AlignCenter)
        self.setScaledContents(False)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(320, 240)

        # Display placeholder
        self.setText("No Video Stream")
        self.setStyleSheet("background-color: black; color: #666;")

        # Video capture
        self.capture: Optional[cv2.VideoCapture] = None
        self.stream_url: Optional[str] = None
        self.is_streaming = False

        # Frame update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)
        self.fps_limit = 30

        # Track connection state
        self.connection_attempts = 0
        self.max_connection_attempts = 3

    def start_stream(self, url: str, fps_limit: int = 30) -> bool:
        """
        Start displaying video stream from URL.

        Args:
            url: RTMP stream URL
            fps_limit: Maximum FPS for display (default 30)

        Returns:
            True if stream started successfully, False otherwise
        """
        self.stream_url = url
        self.fps_limit = fps_limit

        # Stop existing stream if any
        self.stop_stream()

        try:
            # Open video capture with CAP_FFMPEG backend
            self.capture = cv2.VideoCapture(self.stream_url, cv2.CAP_FFMPEG)

            if not self.capture.isOpened():
                self.setText("Failed to connect to stream")
                return False

            # Start frame update timer
            interval_ms = int(1000 / self.fps_limit)
            self.timer.start(interval_ms)
            self.is_streaming = True
            self.connection_attempts = 0

            return True

        except Exception as e:
            self.setText(f"Error: {str(e)}")
            return False

    def stop_stream(self) -> None:
        """Stop the video stream."""
        self.is_streaming = False
        self.timer.stop()

        if self.capture is not None:
            self.capture.release()
            self.capture = None

        self.setText("No Video Stream")

    def _update_frame(self) -> None:
        """Update the displayed frame from video capture."""
        if self.capture is None or not self.is_streaming:
            return

        try:
            ret, frame = self.capture.read()

            if not ret:
                # Try to reconnect
                self.connection_attempts += 1
                if self.connection_attempts >= self.max_connection_attempts:
                    self.setText("Stream connection lost")
                    self.stop_stream()
                return

            # Reset connection attempts on successful read
            self.connection_attempts = 0

            # Convert frame from BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Get frame dimensions
            height, width, channels = frame_rgb.shape
            bytes_per_line = channels * width

            # Create QImage from frame data
            q_image = QImage(
                frame_rgb.data,
                width,
                height,
                bytes_per_line,
                QImage.Format_RGB888
            )

            # Scale to widget size while maintaining aspect ratio
            scaled_pixmap = QPixmap.fromImage(q_image).scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            self.setPixmap(scaled_pixmap)

        except Exception as e:
            self.connection_attempts += 1
            if self.connection_attempts >= self.max_connection_attempts:
                self.setText(f"Stream error: {str(e)}")
                self.stop_stream()

    def mouseDoubleClickEvent(self, event) -> None:
        """
        Handle double-click event.

        Args:
            event: Mouse event
        """
        self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)

    def get_current_frame(self) -> Optional[np.ndarray]:
        """
        Get the current frame as numpy array.

        Returns:
            Current frame in BGR format, or None if not available
        """
        if self.capture is None or not self.is_streaming:
            return None

        ret, frame = self.capture.read()
        if ret:
            return frame
        return None

    def is_active(self) -> bool:
        """
        Check if video stream is active.

        Returns:
            True if streaming, False otherwise
        """
        return self.is_streaming and self.capture is not None

    def reconnect(self) -> bool:
        """
        Attempt to reconnect to the stream.

        Returns:
            True if reconnection successful, False otherwise
        """
        if self.stream_url is None:
            return False

        self.setText("Reconnecting...")
        self.connection_attempts = 0
        return self.start_stream(self.stream_url, self.fps_limit)

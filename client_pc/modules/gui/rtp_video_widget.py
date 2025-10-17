"""
Enhanced video display widget with RTP stream support.

Displays live video from both RTMP and RTP streams using OpenCV and GStreamer.
"""

import cv2
import numpy as np
from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from typing import Optional
import logging


class RTPVideoWidget(QLabel):
    """
    Widget for displaying live video stream from RTP or RTMP.

    Captures frames from RTP/RTMP stream using OpenCV and displays them
    in a QLabel with proper aspect ratio handling.

    Signals:
        double_clicked: Emitted when widget is double-clicked (for fullscreen toggle)
    """

    double_clicked = pyqtSignal()

    def __init__(self, parent=None, logger: Optional[logging.Logger] = None):
        """Initialize video widget."""
        super().__init__(parent)

        self.logger = logger or logging.getLogger(__name__)

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
        self.stream_type: Optional[str] = None  # 'rtmp', 'rtp', 'udp'
        self.is_streaming = False

        # Frame update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)
        self.fps_limit = 30

        # Track connection state
        self.connection_attempts = 0
        self.max_connection_attempts = 3

        # Performance tracking
        self.frames_received = 0
        self.frames_dropped = 0

    def start_stream(self, url: str, stream_type: str = 'auto', fps_limit: int = 30) -> bool:
        """
        Start displaying video stream from URL.

        Args:
            url: Stream URL (RTMP, RTP, or UDP)
            stream_type: Stream type ('rtmp', 'rtp', 'udp', or 'auto')
            fps_limit: Maximum FPS for display (default 30)

        Returns:
            True if stream started successfully, False otherwise
        """
        self.stream_url = url
        self.fps_limit = fps_limit

        # Auto-detect stream type
        if stream_type == 'auto':
            if url.startswith('rtmp://'):
                stream_type = 'rtmp'
            elif url.startswith('udp://'):
                stream_type = 'udp'
            elif url.startswith('rtp://'):
                stream_type = 'rtp'
            else:
                stream_type = 'rtmp'  # Default

        self.stream_type = stream_type

        # Stop existing stream if any
        self.stop_stream()

        try:
            # Configure OpenCV based on stream type
            if stream_type == 'udp' or stream_type == 'rtp':
                # For RTP/UDP, we might need GStreamer pipeline
                success = self._start_rtp_stream(url)
            else:
                # For RTMP, use FFmpeg backend
                success = self._start_rtmp_stream(url)

            if success:
                # Start frame update timer
                interval_ms = int(1000 / self.fps_limit)
                self.timer.start(interval_ms)
                self.is_streaming = True
                self.connection_attempts = 0
                self.frames_received = 0
                self.frames_dropped = 0

                self.logger.info(f"Stream started: {url} (type: {stream_type})")
                return True
            else:
                self.setText("Failed to connect to stream")
                return False

        except Exception as e:
            self.logger.error(f"Stream start error: {e}")
            self.setText(f"Error: {str(e)}")
            return False

    def _start_rtmp_stream(self, url: str) -> bool:
        """
        Start RTMP stream using FFmpeg backend.

        Args:
            url: RTMP stream URL

        Returns:
            True if successful
        """
        try:
            self.capture = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
            return self.capture.isOpened()
        except Exception as e:
            self.logger.error(f"RTMP stream error: {e}")
            return False

    def _start_rtp_stream(self, url: str) -> bool:
        """
        Start RTP/UDP stream using GStreamer or FFmpeg.

        Args:
            url: RTP/UDP stream URL

        Returns:
            True if successful
        """
        try:
            # Try GStreamer first (better for RTP)
            gst_pipeline = self._build_gstreamer_pipeline(url)
            if gst_pipeline:
                self.logger.debug(f"Using GStreamer pipeline: {gst_pipeline}")
                self.capture = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

                if self.capture.isOpened():
                    return True

            # Fallback to FFmpeg
            self.logger.debug("GStreamer failed, trying FFmpeg")
            self.capture = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
            return self.capture.isOpened()

        except Exception as e:
            self.logger.error(f"RTP stream error: {e}")
            return False

    def _build_gstreamer_pipeline(self, url: str) -> Optional[str]:
        """
        Build GStreamer pipeline for RTP stream.

        Args:
            url: RTP/UDP stream URL

        Returns:
            GStreamer pipeline string, or None if not applicable
        """
        # Extract port from UDP URL
        if url.startswith('udp://@:'):
            port = url.split(':')[-1]
            # GStreamer pipeline for H264 RTP
            pipeline = (
                f"udpsrc port={port} "
                f"caps=\"application/x-rtp,media=(string)video,clock-rate=(int)90000,"
                f"encoding-name=(string)H264,payload=(int)96\" ! "
                "rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! appsink"
            )
            return pipeline

        return None

    def stop_stream(self) -> None:
        """Stop the video stream."""
        self.is_streaming = False
        self.timer.stop()

        if self.capture is not None:
            self.capture.release()
            self.capture = None

        self.setText("No Video Stream")
        self.logger.info("Stream stopped")

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
                else:
                    self.frames_dropped += 1
                return

            # Reset connection attempts on successful read
            self.connection_attempts = 0
            self.frames_received += 1

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
            self.logger.error(f"Frame update error: {e}")
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
        return self.start_stream(self.stream_url, self.stream_type or 'auto', self.fps_limit)

    def get_stats(self) -> dict:
        """
        Get streaming statistics.

        Returns:
            Dictionary with streaming stats
        """
        return {
            'is_streaming': self.is_streaming,
            'stream_url': self.stream_url,
            'stream_type': self.stream_type,
            'frames_received': self.frames_received,
            'frames_dropped': self.frames_dropped,
            'fps_limit': self.fps_limit
        }

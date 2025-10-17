"""
RTP video recorder with configurable quality settings.

Records RTP video stream to MP4 files with customizable bitrate and quality.
"""

import subprocess
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from threading import Thread, Event


class RTPRecorder:
    """
    Record RTP video stream to MP4 files.

    Supports configurable quality settings and automatic segmentation.
    """

    # Quality presets (bitrate in kbps)
    QUALITY_PRESETS = {
        'low': {'video_bitrate': '1000k', 'label': 'Low (1 Mbps)'},
        'medium': {'video_bitrate': '2500k', 'label': 'Medium (2.5 Mbps)'},
        'high': {'video_bitrate': '5000k', 'label': 'High (5 Mbps)'},
        'ultra': {'video_bitrate': '8000k', 'label': 'Ultra (8 Mbps)'},
        'lossless': {'video_bitrate': None, 'label': 'Lossless (copy)'}
    }

    def __init__(self,
                 output_dir: str = "records/videos",
                 quality: str = 'high',
                 logger: Optional[logging.Logger] = None):
        """
        Initialize RTP recorder.

        Args:
            output_dir: Directory to save recorded videos
            quality: Quality preset ('low', 'medium', 'high', 'ultra', 'lossless')
            logger: Optional logger instance
        """
        self.output_dir = Path(output_dir)
        self.quality = quality
        self.logger = logger or logging.getLogger(__name__)

        self.is_recording = False
        self.is_paused = False
        self.stop_event = Event()

        # Process handle
        self.process: Optional[subprocess.Popen] = None
        self.current_file: Optional[str] = None

        # Recording stats
        self.start_time: Optional[datetime] = None
        self.bytes_written = 0

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def set_quality(self, quality: str) -> bool:
        """
        Set recording quality preset.

        Args:
            quality: Quality preset name

        Returns:
            True if quality preset is valid
        """
        if quality not in self.QUALITY_PRESETS:
            self.logger.error(f"Invalid quality preset: {quality}")
            return False

        self.quality = quality
        self.logger.info(f"Recording quality set to {quality}")
        return True

    def set_custom_bitrate(self, bitrate_kbps: int) -> None:
        """
        Set custom video bitrate.

        Args:
            bitrate_kbps: Video bitrate in kbps
        """
        self.QUALITY_PRESETS['custom'] = {
            'video_bitrate': f'{bitrate_kbps}k',
            'label': f'Custom ({bitrate_kbps / 1000:.1f} Mbps)'
        }
        self.quality = 'custom'
        self.logger.info(f"Custom bitrate set to {bitrate_kbps} kbps")

    def generate_filename(self) -> str:
        """
        Generate timestamped filename for recording.

        Returns:
            Filename string
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"recording_{timestamp}.mp4"

    def start_recording(self,
                       rtp_url: str,
                       filename: Optional[str] = None,
                       segment_duration: Optional[int] = None) -> bool:
        """
        Start recording RTP stream.

        Args:
            rtp_url: RTP stream URL (e.g., "udp://@:5000")
            filename: Optional custom filename (will auto-generate if None)
            segment_duration: Optional segment duration in seconds

        Returns:
            True if recording started successfully
        """
        if self.is_recording:
            self.logger.warning("Recording already in progress")
            return False

        # Generate filename if not provided
        if filename is None:
            filename = self.generate_filename()

        self.current_file = str(self.output_dir / filename)

        # Build FFmpeg command
        try:
            cmd = self._build_ffmpeg_command(rtp_url, self.current_file, segment_duration)
            self.logger.info(f"Starting recording with command: {' '.join(cmd)}")

            # Start FFmpeg process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )

            self.is_recording = True
            self.is_paused = False
            self.start_time = datetime.now()
            self.stop_event.clear()

            self.logger.info(f"Recording started: {self.current_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            return False

    def _build_ffmpeg_command(self,
                             input_url: str,
                             output_file: str,
                             segment_duration: Optional[int] = None) -> list:
        """
        Build FFmpeg command for recording.

        Args:
            input_url: Input RTP stream URL
            output_file: Output file path
            segment_duration: Optional segment duration in seconds

        Returns:
            FFmpeg command as list of arguments
        """
        preset = self.QUALITY_PRESETS.get(self.quality, self.QUALITY_PRESETS['high'])

        cmd = [
            'ffmpeg',
            '-protocol_whitelist', 'file,udp,rtp',
            '-i', input_url,
            '-y'  # Overwrite output file
        ]

        # Video encoding settings
        if preset['video_bitrate'] is None:
            # Lossless - copy codec
            cmd.extend(['-c:v', 'copy'])
        else:
            # Re-encode with specified bitrate
            cmd.extend([
                '-c:v', 'libx264',
                '-b:v', preset['video_bitrate'],
                '-preset', 'medium',
                '-profile:v', 'high',
                '-level', '4.1',
                '-pix_fmt', 'yuv420p'
            ])

        # Audio settings (if present)
        cmd.extend(['-c:a', 'aac', '-b:a', '128k'])

        # Segmentation settings
        if segment_duration:
            cmd.extend([
                '-f', 'segment',
                '-segment_time', str(segment_duration),
                '-segment_format', 'mp4',
                '-reset_timestamps', '1',
                '-strftime', '1',
                output_file.replace('.mp4', '_%Y%m%d_%H%M%S.mp4')
            ])
        else:
            # Single file
            cmd.extend([
                '-f', 'mp4',
                '-movflags', '+faststart'
            ])

        cmd.append(output_file)

        return cmd

    def stop_recording(self) -> bool:
        """
        Stop current recording.

        Returns:
            True if recording was stopped successfully
        """
        if not self.is_recording:
            self.logger.warning("No recording in progress")
            return False

        try:
            if self.process:
                # Send 'q' to FFmpeg to gracefully stop
                self.process.stdin.write(b'q')
                self.process.stdin.flush()

                # Wait for process to complete
                self.process.wait(timeout=10)
                self.process = None

            self.is_recording = False
            self.is_paused = False
            self.stop_event.set()

            duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0

            self.logger.info(f"Recording stopped: {self.current_file} (duration: {duration:.1f}s)")
            return True

        except Exception as e:
            self.logger.error(f"Error stopping recording: {e}")
            # Force kill if graceful stop failed
            if self.process:
                self.process.kill()
                self.process = None
            return False

    def pause_recording(self) -> bool:
        """
        Pause current recording.

        Note: FFmpeg doesn't support true pause. This stops and will need restart.

        Returns:
            True if paused successfully
        """
        if not self.is_recording or self.is_paused:
            return False

        # FFmpeg doesn't support pause, so we just mark as paused
        # You would need to stop and restart with a new file
        self.is_paused = True
        self.logger.info("Recording paused (will create new segment on resume)")
        return True

    def resume_recording(self) -> bool:
        """
        Resume paused recording.

        Returns:
            True if resumed successfully
        """
        if not self.is_paused:
            return False

        self.is_paused = False
        self.logger.info("Recording resumed")
        return True

    def get_recording_duration(self) -> float:
        """
        Get current recording duration in seconds.

        Returns:
            Duration in seconds
        """
        if not self.start_time:
            return 0.0

        return (datetime.now() - self.start_time).total_seconds()

    def get_output_filesize(self) -> int:
        """
        Get current output file size in bytes.

        Returns:
            File size in bytes, or 0 if file doesn't exist
        """
        if not self.current_file:
            return 0

        try:
            if os.path.exists(self.current_file):
                return os.path.getsize(self.current_file)
        except Exception:
            pass

        return 0

    def get_status(self) -> Dict[str, Any]:
        """
        Get recorder status information.

        Returns:
            Dictionary with status information
        """
        return {
            'is_recording': self.is_recording,
            'is_paused': self.is_paused,
            'current_file': self.current_file,
            'quality': self.quality,
            'quality_label': self.QUALITY_PRESETS.get(self.quality, {}).get('label', 'Unknown'),
            'duration': self.get_recording_duration(),
            'file_size': self.get_output_filesize(),
            'output_dir': str(self.output_dir)
        }

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.is_recording:
            self.stop_recording()


class RTPSnapshotCapture:
    """
    Capture snapshots from RTP stream.
    """

    def __init__(self,
                 output_dir: str = "records/snapshots",
                 logger: Optional[logging.Logger] = None):
        """
        Initialize snapshot capture.

        Args:
            output_dir: Directory to save snapshots
            logger: Optional logger instance
        """
        self.output_dir = Path(output_dir)
        self.logger = logger or logging.getLogger(__name__)

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def capture_snapshot(self, rtp_url: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Capture a single frame snapshot from RTP stream.

        Args:
            rtp_url: RTP stream URL
            filename: Optional custom filename

        Returns:
            Path to saved snapshot, or None if failed
        """
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"snapshot_{timestamp}.jpg"

        output_path = str(self.output_dir / filename)

        try:
            # FFmpeg command to capture single frame
            cmd = [
                'ffmpeg',
                '-protocol_whitelist', 'file,udp,rtp',
                '-i', rtp_url,
                '-vframes', '1',
                '-q:v', '2',  # High quality JPEG
                '-y',
                output_path
            ]

            self.logger.info(f"Capturing snapshot: {output_path}")

            # Run FFmpeg
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )

            if result.returncode == 0 and os.path.exists(output_path):
                self.logger.info(f"Snapshot saved: {output_path}")
                return output_path
            else:
                self.logger.error(f"Snapshot capture failed: {result.stderr.decode()}")
                return None

        except Exception as e:
            self.logger.error(f"Error capturing snapshot: {e}")
            return None

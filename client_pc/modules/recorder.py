"""
Video recorder using FFmpeg segment muxer.

Records incoming RTMP stream to segmented MP4 files with automatic rotation.
Includes disk space monitoring and guard logic.
"""

import subprocess
import time
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import psutil


class Recorder:
    """
    Records RTMP stream to MP4 files using FFmpeg segment muxer.

    Features:
    - Automatic 3-hour segment rotation
    - Disk space monitoring and guard
    - No re-encoding (copy codec)
    - Fast-start MP4 for immediate playback
    """

    def __init__(self, config: Dict[str, Any], logger) -> None:
        """
        Initialize recorder.

        Args:
            config: Configuration dictionary with recording settings.
            logger: JSON logger instance.
        """
        self.config = config
        self.logger = logger
        self.rtmp_url = config["stream"]["url"]
        self.output_dir = Path(config["recording"]["output_dir"])
        self.segment_seconds = config["recording"]["segment_seconds"]
        self.disk_free_floor_mib = config["recording"]["disk_free_floor_mib"]
        self.disk_free_resume_mib = config["recording"].get("disk_free_resume_mib", 1024)

        self.process: Optional[subprocess.Popen] = None
        self.current_segment: Optional[str] = None
        self.is_paused = False

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_disk_free_mib(self) -> float:
        """
        Get free disk space in MiB for the recording drive.

        Returns:
            Free space in MiB.
        """
        usage = psutil.disk_usage(str(self.output_dir))
        return usage.free / (1024 * 1024)

    def check_disk_space(self) -> bool:
        """
        Check if there's enough disk space to continue recording.

        Returns:
            True if safe to record, False if below floor.
        """
        free_mib = self.get_disk_free_mib()

        if self.is_paused:
            # Check for resume threshold
            if free_mib > self.disk_free_resume_mib:
                self.logger.log("service", "recorder", "disk_space_resumed", {
                    "free_mib": free_mib,
                    "resume_threshold_mib": self.disk_free_resume_mib
                }, f"Disk space recovered to {free_mib:.0f} MiB, resuming recording")
                self.is_paused = False
                return True
            return False
        else:
            # Check for pause threshold
            if free_mib < self.disk_free_floor_mib:
                self.logger.log("error", "recorder", "disk_space_low", {
                    "free_mib": free_mib,
                    "floor_mib": self.disk_free_floor_mib
                }, f"Disk space below {self.disk_free_floor_mib} MiB, pausing recording")
                self.is_paused = True
                return False
            return True

    def build_ffmpeg_command(self) -> list:
        """
        Build FFmpeg command for segmented recording.

        Returns:
            List of command arguments.
        """
        # Pattern for output files: rec_YYYYMMDD_HHMMSS.mp4
        output_pattern = str(self.output_dir / "rec_%Y%m%d_%H%M%S.mp4")

        cmd = [
            "ffmpeg",
            "-rtmp_live", "live",               # Specify live stream mode for RTMP
            "-err_detect", "ignore_err",        # Ignore decoding errors (corrupted frames)
            "-fflags", "+genpts+discardcorrupt", # Generate PTS and discard corrupt packets
            "-i", self.rtmp_url,
            "-c:v", "copy",                     # Copy H.264 stream without re-encoding
            "-movflags", "+faststart",          # Write index at beginning for instant playback
            "-f", "segment",                    # Use segment muxer
            "-segment_time", str(self.segment_seconds),  # 3 hours = 10800 seconds
            "-reset_timestamps", "1",           # Reset timestamps for each segment
            "-strftime", "1",                   # Enable strftime in output pattern
            output_pattern
        ]

        return cmd

    def start(self) -> None:
        """
        Start recording the RTMP stream.

        Raises:
            RuntimeError: If FFmpeg fails to start or disk space is low.
        """
        if self.is_running():
            self.logger.log("info", "recorder", "already_running", {},
                          "Recorder already running")
            return

        # Check disk space before starting
        if not self.check_disk_space():
            raise RuntimeError(f"Insufficient disk space (< {self.disk_free_floor_mib} MiB)")

        self.logger.log("info", "recorder", "segment_open", {
            "output_dir": str(self.output_dir),
            "segment_seconds": self.segment_seconds,
            "url": self.rtmp_url
        }, "Starting segmented recording")

        try:
            cmd = self.build_ffmpeg_command()

            self.logger.log("info", "recorder", "ffmpeg_command", {
                "command": " ".join(cmd)
            }, f"Starting FFmpeg: {' '.join(cmd[:5])}")

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr into stdout for easier monitoring
                stdin=subprocess.PIPE,
                cwd=str(self.output_dir.parent)  # Set working directory
            )

            # Wait a moment to see if process starts successfully
            import time
            time.sleep(0.5)

            if self.process.poll() is not None:
                # Process already died
                output = self.process.stdout.read().decode('utf-8', errors='replace')
                raise RuntimeError(f"FFmpeg died immediately: {output[-500:]}")

            self.logger.log("service", "recorder", "recording_started", {
                "pid": self.process.pid,
                "output_dir": str(self.output_dir),
                "running": self.is_running()
            }, "Recording started successfully")

        except Exception as e:
            self.logger.log("error", "recorder", "start_failed", {
                "error": str(e)
            }, f"Failed to start recorder: {e}")
            raise RuntimeError(f"Failed to start recorder: {e}")

    def is_running(self) -> bool:
        """
        Check if the recorder process is running.

        Returns:
            True if process is alive, False otherwise.
        """
        return self.process is not None and self.process.poll() is None

    def monitor(self) -> None:
        """
        Monitor the recording process and handle disk space.

        This should be called periodically (e.g., every few seconds).
        """
        if not self.is_running():
            return

        # Check if process died unexpectedly
        if self.process and self.process.poll() is not None:
            # Process ended, check for errors
            try:
                stdout_output = self.process.stdout.read().decode('utf-8', errors='replace') if self.process.stdout else ""

                # Try to extract meaningful error from FFmpeg output
                error_lines = []
                if stdout_output:
                    lines = stdout_output.split('\n')
                    # Get last 20 lines which usually contain the error
                    error_lines = [l for l in lines[-20:] if l.strip() and ('error' in l.lower() or 'failed' in l.lower() or 'invalid' in l.lower())]

                error_summary = '\n'.join(error_lines[-5:]) if error_lines else stdout_output[-300:]

                self.logger.log("error", "recorder", "process_died", {
                    "returncode": self.process.returncode,
                    "ffmpeg_output": stdout_output[-2000:] if stdout_output else "",
                    "error_lines": error_lines[-5:] if error_lines else [],
                    "pid": self.process.pid if self.process.pid else "unknown"
                }, f"Recording process died unexpectedly (code {self.process.returncode}). Error: {error_summary if error_summary else 'No error output'}")
            except Exception as e:
                self.logger.log("error", "recorder", "process_died", {
                    "returncode": self.process.returncode,
                    "error": str(e)
                }, f"Recording process died unexpectedly (code {self.process.returncode})")
            self.process = None
            return

        # Check disk space
        if not self.check_disk_space():
            self.logger.log("service", "recorder", "pausing", {},
                          "Pausing recording due to low disk space")
            self.stop()
            return

        # Log segment rotation (detected by checking output directory)
        # In a more sophisticated implementation, we would parse FFmpeg output
        # to detect segment creation events

    def stop(self) -> None:
        """Stop the recorder process gracefully."""
        if not self.process:
            return

        self.logger.log("info", "recorder", "stopping", {
            "pid": self.process.pid
        }, "Stopping recorder")

        # Send 'q' to FFmpeg for graceful shutdown
        try:
            if self.process.stdin:
                self.process.stdin.write(b'q')
                self.process.stdin.flush()
        except:
            pass

        # Wait for process to exit
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.logger.log("info", "recorder", "killing", {},
                          "Force killing recorder")
            self.process.kill()

        self.process = None

        self.logger.log("service", "recorder", "stopped", {},
                      "Recorder stopped")

    def get_status(self) -> Dict[str, Any]:
        """
        Get current recorder status.

        Returns:
            Dictionary with status information.
        """
        return {
            "is_running": self.is_running(),
            "is_paused": self.is_paused,
            "output_dir": str(self.output_dir),
            "segment_seconds": self.segment_seconds,
            "disk_free_mib": self.get_disk_free_mib(),
            "disk_floor_mib": self.disk_free_floor_mib
        }

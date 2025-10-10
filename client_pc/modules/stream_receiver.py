"""
RTMP stream receiver using FFmpeg.

Manages the FFmpeg subprocess that receives the RTMP stream from the Pi.
Handles reconnection on failures and monitors stream health.
"""

import subprocess
import time
from typing import Optional, Dict, Any
from pathlib import Path


class StreamReceiver:
    """
    Receives RTMP stream from Raspberry Pi using FFmpeg.

    Launches FFmpeg to pull the RTMP stream and provides monitoring
    and reconnection capabilities.
    """

    def __init__(self, config: Dict[str, Any], logger) -> None:
        """
        Initialize stream receiver.

        Args:
            config: Configuration dictionary with stream settings.
            logger: JSON logger instance.
        """
        self.config = config
        self.logger = logger
        self.rtmp_url = config["stream"]["url"]
        self.read_timeout = config["stream"].get("read_timeout_seconds", 10)
        self.process: Optional[subprocess.Popen] = None
        self.start_time: Optional[float] = None

    def build_ffmpeg_command(self, output_pipe: bool = True) -> list:
        """
        Build FFmpeg command to receive RTMP stream.

        Args:
            output_pipe: If True, output to pipe; otherwise to null.

        Returns:
            List of command arguments.
        """
        cmd = [
            "ffmpeg",
            "-re",                          # Read at native frame rate
            "-rtmp_live", "live",           # Specify live stream mode
            "-i", self.rtmp_url,
            "-c:v", "copy",                 # Copy video stream without re-encoding
            "-f", "null" if not output_pipe else "rawvideo",
            "-" if output_pipe else "NUL"   # Windows null device
        ]

        return cmd

    def start(self) -> None:
        """
        Start receiving the RTMP stream.

        Raises:
            RuntimeError: If FFmpeg fails to start.
        """
        if self.is_running():
            self.logger.log("info", "stream_receiver", "already_running", {},
                          "Stream receiver already running")
            return

        self.logger.log("info", "stream_receiver", "E_INPUT_OPEN", {
            "url": self.rtmp_url,
            "timeout_s": self.read_timeout
        }, "Opening RTMP input stream")

        try:
            # For monitoring without actual output, we just test connectivity
            cmd = self.build_ffmpeg_command(output_pipe=False)

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL
            )

            self.start_time = time.time()

            self.logger.log("service", "stream_receiver", "input_opened", {
                "pid": self.process.pid,
                "url": self.rtmp_url
            }, "RTMP stream opened successfully")

        except Exception as e:
            self.logger.log("error", "stream_receiver", "start_failed", {
                "error": str(e)
            }, f"Failed to start stream receiver: {e}")
            raise RuntimeError(f"Failed to start stream receiver: {e}")

    def is_running(self) -> bool:
        """
        Check if the receiver process is running.

        Returns:
            True if process is alive, False otherwise.
        """
        return self.process is not None and self.process.poll() is None

    def check_health(self) -> Dict[str, Any]:
        """
        Check stream health and return status.
        Also logs if process died unexpectedly.

        Returns:
            Dictionary with health metrics.
        """
        # Check if process died unexpectedly
        if self.process and self.process.poll() is not None:
            # Process ended, capture error details
            try:
                stderr = self.process.stderr.read().decode('utf-8', errors='replace') if self.process.stderr else ""
                stdout = self.process.stdout.read().decode('utf-8', errors='replace') if self.process.stdout else ""

                self.logger.log("error", "stream_receiver", "process_died", {
                    "returncode": self.process.returncode,
                    "stderr": stderr[-1000:] if stderr else "",
                    "stdout": stdout[-500:] if stdout else "",
                    "uptime_s": time.time() - self.start_time if self.start_time else 0
                }, f"Stream receiver process died (code {self.process.returncode}). Error: {stderr[-300:] if stderr else 'No error output'}")
            except Exception as e:
                self.logger.log("error", "stream_receiver", "process_died", {
                    "returncode": self.process.returncode,
                    "error": str(e)
                }, f"Stream receiver process died (code {self.process.returncode})")

            self.process = None
            self.start_time = None

        if not self.is_running():
            return {
                "status": "stopped",
                "uptime_s": 0
            }

        uptime = time.time() - self.start_time if self.start_time else 0

        return {
            "status": "running",
            "uptime_s": uptime,
            "pid": self.process.pid
        }

    def wait_for_exit(self, timeout: Optional[float] = None) -> int:
        """
        Wait for the process to exit.

        Args:
            timeout: Optional timeout in seconds.

        Returns:
            Process return code.

        Raises:
            RuntimeError: If process exits with error or timeout occurs.
        """
        if not self.process:
            raise RuntimeError("No process running")

        try:
            returncode = self.process.wait(timeout=timeout)

            # Capture stderr for diagnostics
            stderr = ""
            if self.process.stderr:
                stderr = self.process.stderr.read().decode("utf-8", errors="replace")

            if returncode != 0:
                self.logger.log("error", "stream_receiver", "E_STREAM_DROP", {
                    "returncode": returncode,
                    "stderr": stderr[:500]
                }, f"Stream dropped with code {returncode}")

                raise RuntimeError(f"Stream exited with code {returncode}")

            return returncode

        except subprocess.TimeoutExpired:
            self.logger.log("error", "stream_receiver", "READ_TIMEOUT", {
                "timeout_s": timeout
            }, "Stream read timeout")
            raise RuntimeError("Stream read timeout")

    def stop(self) -> None:
        """Stop the receiver process gracefully."""
        if not self.process:
            return

        self.logger.log("info", "stream_receiver", "stopping", {
            "pid": self.process.pid
        }, "Stopping stream receiver")

        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.logger.log("info", "stream_receiver", "killing", {},
                          "Force killing stream receiver")
            self.process.kill()

        self.process = None
        self.start_time = None

        self.logger.log("service", "stream_receiver", "stopped", {},
                      "Stream receiver stopped")

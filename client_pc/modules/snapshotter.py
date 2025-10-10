"""
Snapshot capture module.

Extracts single frames from the RTMP stream and saves them as JPEG files.
Supports hotkey triggers, CLI commands, and periodic intervals.
"""

import subprocess
import time
from typing import Dict, Any
from pathlib import Path
from datetime import datetime


class Snapshotter:
    """
    Captures single-frame snapshots from RTMP stream.

    Features:
    - On-demand snapshot capture
    - Periodic snapshot intervals
    - Low-latency frame extraction (<300ms)
    - Organized snapshot directory
    """

    def __init__(self, config: Dict[str, Any], logger) -> None:
        """
        Initialize snapshotter.

        Args:
            config: Configuration dictionary with snapshot settings.
            logger: JSON logger instance.
        """
        self.config = config
        self.logger = logger
        self.rtmp_url = config["stream"]["url"]
        self.output_dir = Path(config["snapshots"]["output_dir"])
        self.interval_seconds = config["snapshots"].get("interval_seconds", 0)

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.last_snapshot_time = 0.0

    def generate_filename(self) -> str:
        """
        Generate filename for snapshot.

        Returns:
            Filename string (e.g., "snap_20251003_143022_123.jpg").
        """
        now = datetime.now()
        milliseconds = int((now.timestamp() % 1) * 1000)

        filename = now.strftime(f"snap_%Y%m%d_%H%M%S_{milliseconds:03d}.jpg")
        return filename

    def capture(self) -> Path:
        """
        Capture a single frame from the stream.

        Returns:
            Path to the saved snapshot file.

        Raises:
            RuntimeError: If snapshot capture fails.
        """
        filename = self.generate_filename()
        output_path = self.output_dir / filename

        self.logger.log("info", "snapshotter", "snapshot_capture", {
            "filename": filename
        }, f"Capturing snapshot: {filename}")

        start_time = time.time()

        try:
            cmd = [
                "ffmpeg",
                "-y",                       # Overwrite output file
                "-rtmp_live", "live",       # Specify live stream mode for RTMP
                "-err_detect", "ignore_err", # Ignore decoding errors
                "-i", self.rtmp_url,
                "-frames:v", "1",           # Extract one frame
                "-q:v", "2",                # High quality JPEG
                str(output_path)
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5  # 5 second timeout
            )

            elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds

            if result.returncode != 0:
                stderr = result.stderr.decode("utf-8", errors="replace")
                self.logger.log("error", "snapshotter", "E_SNAPSHOT_WRITE", {
                    "returncode": result.returncode,
                    "stderr": stderr[:500],
                    "path": str(output_path)
                }, f"Failed to capture snapshot: {stderr[:100]}")
                raise RuntimeError(f"FFmpeg failed with code {result.returncode}")

            self.logger.log("service", "snapshotter", "snapshot_saved", {
                "path": str(output_path),
                "latency_ms": elapsed,
                "size_bytes": output_path.stat().st_size
            }, f"Snapshot saved in {elapsed:.0f}ms: {filename}")

            self.last_snapshot_time = time.time()

            return output_path

        except subprocess.TimeoutExpired:
            self.logger.log("error", "snapshotter", "snapshot_timeout", {
                "path": str(output_path)
            }, "Snapshot capture timed out after 5s")
            raise RuntimeError("Snapshot capture timeout")

        except Exception as e:
            self.logger.log("error", "snapshotter", "E_SNAPSHOT_WRITE", {
                "error": str(e),
                "path": str(output_path)
            }, f"Snapshot capture failed: {e}")
            raise RuntimeError(f"Snapshot capture failed: {e}")

    def should_capture_interval(self) -> bool:
        """
        Check if it's time to capture based on interval setting.

        Returns:
            True if interval has elapsed, False otherwise.
        """
        if self.interval_seconds <= 0:
            return False

        elapsed = time.time() - self.last_snapshot_time
        return elapsed >= self.interval_seconds

    def get_snapshots(self, limit: int = 10) -> list:
        """
        Get list of recent snapshots.

        Args:
            limit: Maximum number of snapshots to return.

        Returns:
            List of snapshot file paths, newest first.
        """
        snapshots = sorted(
            self.output_dir.glob("snap_*.jpg"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        return snapshots[:limit]

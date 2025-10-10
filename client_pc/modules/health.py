"""
Health monitoring module for the client application.

Periodically checks stream health, FPS, disk space, and other metrics.
"""

import time
import threading
from typing import Dict, Any, Optional


class HealthMonitor:
    """
    Monitors system and stream health.

    Runs periodic checks and maintains current status that can be
    queried by the CLI or other components.
    """

    def __init__(self, config: Dict[str, Any], stream_receiver, recorder, logger) -> None:
        """
        Initialize health monitor.

        Args:
            config: Configuration dictionary.
            stream_receiver: StreamReceiver instance to monitor.
            recorder: Recorder instance to monitor.
            logger: JSON logger instance.
        """
        self.config = config
        self.stream_receiver = stream_receiver
        self.recorder = recorder
        self.logger = logger

        self.check_interval = config["health"]["check_interval_seconds"]
        self.status: Dict[str, Any] = {
            "stream": {"status": "stopped", "uptime_s": 0},
            "recorder": {"status": "stopped"},
            "fps": 0.0,
            "disk_free_mib": 0.0,
            "last_check": None
        }

        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.frame_count = 0
        self.last_frame_time = 0.0

    def start(self) -> None:
        """Start the health monitoring thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

        self.logger.log("service", "health", "monitor_started", {
            "interval_s": self.check_interval
        }, "Health monitor started")

    def stop(self) -> None:
        """Stop the health monitoring thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

        self.logger.log("info", "health", "monitor_stopped", {},
                      "Health monitor stopped")

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.running:
            try:
                self._update_status()
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.log("error", "health", "monitor_error", {
                    "error": str(e)
                }, f"Health monitor error: {e}")

    def _update_status(self) -> None:
        """Update health status by querying all components."""
        # Update stream status
        self.status["stream"] = self.stream_receiver.check_health()

        # Update recorder status
        self.status["recorder"] = self.recorder.get_status()

        # Update disk free space
        self.status["disk_free_mib"] = self.recorder.get_disk_free_mib()

        # Calculate approximate FPS (simplified)
        # In a real implementation, we would parse FFmpeg stats output
        self.status["fps"] = self._estimate_fps()

        # Update timestamp
        self.status["last_check"] = time.time()

    def _estimate_fps(self) -> float:
        """
        Estimate current FPS from stream.

        This is a simplified version. A real implementation would
        parse FFmpeg's progress output or use a frame counter callback.

        Returns:
            Estimated FPS.
        """
        # For now, return configured FPS if stream is running
        if self.status["stream"]["status"] == "running":
            return 30.0  # Assume 30 FPS
        return 0.0

    def get_status(self) -> Dict[str, Any]:
        """
        Get current health status.

        Returns:
            Dictionary with all health metrics.
        """
        return self.status.copy()

    def get_summary(self) -> str:
        """
        Get human-readable status summary.

        Returns:
            Multi-line status summary string.
        """
        s = self.status

        stream_status = s["stream"]["status"]
        stream_uptime = s["stream"].get("uptime_s", 0)
        recorder_running = s["recorder"]["is_running"]
        recorder_paused = s["recorder"].get("is_paused", False)
        fps = s["fps"]
        disk_free = s["disk_free_mib"]

        lines = [
            f"Stream: {stream_status.upper()}",
            f"  Uptime: {stream_uptime:.0f}s",
            f"  FPS: {fps:.1f}",
            "",
            f"Recorder: {'RUNNING' if recorder_running else 'STOPPED'}",
        ]

        if recorder_paused:
            lines.append("  Status: PAUSED (low disk space)")

        lines.extend([
            f"  Output: {s['recorder']['output_dir']}",
            "",
            f"Disk Free: {disk_free:.0f} MiB",
        ])

        return "\n".join(lines)

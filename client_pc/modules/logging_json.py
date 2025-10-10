"""
JSON structured logger for Windows client.

Mirrors the Pi's logging implementation with Windows-compatible file paths.
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path


class JsonLogger:
    """
    Structured JSON logger with size-based rotation.

    Log entries follow the format:
    {
      "ts": "2025-10-03T12:34:56.789Z",
      "lvl": "info",
      "comp": "stream_receiver",
      "evt": "input_open",
      "ctx": {"url": "rtmp://..."},
      "msg": "Opened RTMP stream"
    }
    """

    LEVELS = ["debug", "info", "service", "error"]

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the JSON logger.

        Args:
            config: Configuration dictionary with logging settings.
        """
        self.log_file = Path(config["logging"]["file"])
        self.level = config["logging"]["level"]
        self.max_bytes = config["logging"]["rotate_max_mb"] * 1024 * 1024
        self.backup_count = config["logging"]["rotate_backups"]

        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        self.file_handle: Optional[Any] = None
        self._open_log_file()

    def _open_log_file(self) -> None:
        """Open the log file for appending."""
        self.file_handle = open(self.log_file, "a", encoding="utf-8")

    def _should_rotate(self) -> bool:
        """Check if log file exceeds size limit."""
        if not self.log_file.exists():
            return False
        return self.log_file.stat().st_size >= self.max_bytes

    def _rotate(self) -> None:
        """
        Rotate log files.

        Renames current log to .1, shifts existing backups, and removes oldest.
        """
        if self.file_handle:
            self.file_handle.close()

        # Remove oldest backup if it exists
        oldest = Path(f"{self.log_file}.{self.backup_count}")
        if oldest.exists():
            oldest.unlink()

        # Shift existing backups
        for i in range(self.backup_count - 1, 0, -1):
            src = Path(f"{self.log_file}.{i}")
            dst = Path(f"{self.log_file}.{i + 1}")
            if src.exists():
                src.rename(dst)

        # Rename current log to .1
        if self.log_file.exists():
            self.log_file.rename(f"{self.log_file}.1")

        # Open new log file
        self._open_log_file()

    def log(self, level: str, component: str, event: str, context: Dict[str, Any], message: str) -> None:
        """
        Write a structured log entry.

        Args:
            level: Log level (debug, info, service, error).
            component: Component name (e.g., stream_receiver, recorder).
            event: Event name (e.g., input_open, segment_rotated).
            context: Dictionary with additional context data.
            message: Human-readable message.
        """
        # Check log level
        if self.LEVELS.index(level) < self.LEVELS.index(self.level):
            return

        # Check rotation before writing
        if self._should_rotate():
            self._rotate()

        # Build log entry
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "lvl": level,
            "comp": component,
            "evt": event,
            "ctx": context,
            "msg": message
        }

        # Write JSON line
        self.file_handle.write(json.dumps(entry) + "\n")
        self.file_handle.flush()

    def close(self) -> None:
        """Close the log file."""
        if self.file_handle:
            self.file_handle.close()

"""
Utility functions for the client application.
"""

import random
from typing import List, Iterator


def backoff_iterator(schedule: List[int]) -> Iterator[float]:
    """
    Generate backoff delays with jitter.

    Args:
        schedule: List of base delays in seconds.

    Yields:
        Delay values with ±10% jitter. After exhausting the schedule,
        continues yielding the last value indefinitely.
    """
    index = 0
    while True:
        if index < len(schedule):
            base_delay = schedule[index]
            index += 1
        else:
            base_delay = schedule[-1]

        # Add ±10% jitter
        jitter = random.uniform(-0.1, 0.1)
        delay = base_delay * (1.0 + jitter)

        yield max(0.1, delay)


def format_bytes(bytes_value: int) -> str:
    """
    Format bytes as human-readable string.

    Args:
        bytes_value: Number of bytes.

    Returns:
        Formatted string (e.g., "1.5 GB", "500 MB").
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def format_duration(seconds: float) -> str:
    """
    Format duration as human-readable string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted string (e.g., "2h 30m 15s").
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)

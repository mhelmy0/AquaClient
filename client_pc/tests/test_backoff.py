"""
Unit tests for backoff iterator logic.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))

from utils import backoff_iterator


def test_backoff_sequence():
    """Test that backoff iterator produces expected sequence."""
    schedule = [1, 2, 5, 10, 20, 30]
    backoff = backoff_iterator(schedule)

    # Collect first 10 values
    values = [next(backoff) for _ in range(10)]

    # First 6 values should be close to schedule (with jitter)
    for i in range(6):
        expected = schedule[i]
        actual = values[i]
        # Check that jitter is within ±10%
        assert expected * 0.9 <= actual <= expected * 1.1

    # Values 7-10 should be close to last value (30)
    for i in range(6, 10):
        actual = values[i]
        assert 30 * 0.9 <= actual <= 30 * 1.1


def test_backoff_jitter_variance():
    """Test that jitter produces different values."""
    schedule = [5]
    backoff = backoff_iterator(schedule)

    # Generate multiple values
    values = [next(backoff) for _ in range(10)]

    # Not all values should be exactly the same (due to jitter)
    # Note: Theoretically they could all be the same, but probability is negligible
    unique_values = len(set(values))
    assert unique_values > 1  # At least 2 different values


def test_backoff_minimum_value():
    """Test that backoff never returns values below minimum."""
    schedule = [0.05]  # Very small value that would become negative with jitter
    backoff = backoff_iterator(schedule)

    values = [next(backoff) for _ in range(5)]

    # All values should be >= 0.1 (minimum enforced)
    for value in values:
        assert value >= 0.1


def test_backoff_exhaustion():
    """Test that backoff continues with last value after schedule is exhausted."""
    schedule = [1, 2, 3]
    backoff = backoff_iterator(schedule)

    # Consume schedule
    next(backoff)  # 1
    next(backoff)  # 2
    next(backoff)  # 3

    # Next values should all be close to 3
    for _ in range(5):
        value = next(backoff)
        assert 3 * 0.9 <= value <= 3 * 1.1

"""Tests for app/example.py."""

import pytest

from app.example import average, highest


def test_average_normal():
    """average() returns the mean for a typical list."""
    # Arrange + Act + Assert pattern
    assert average([2, 4, 6]) == 4


def test_average_single_element():
    """average() of a one-element list is that element."""
    assert average([10]) == 10


def test_average_empty_list_raises():
    """average() raises ValueError on an empty list."""
    # Assert the expected exception (like TS `expect(() => ...).toThrow()`)
    with pytest.raises(ValueError):
        average([])


def test_highest_normal():
    """highest() returns the largest element."""
    assert highest([3, 9, 5]) == 9


def test_highest_empty_list_raises():
    """highest() raises ValueError on an empty list."""
    with pytest.raises(ValueError):
        highest([])

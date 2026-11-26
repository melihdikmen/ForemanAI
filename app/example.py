"""Phase 0 — tiny example to confirm pytest works. Safe to delete later."""


def average(numbers: list[float]) -> float:
    """Return the arithmetic mean of a list of numbers.

    Raises ValueError on an empty list (to avoid division by zero).
    """
    if not numbers:  # empty list: [] is falsy — like TS `if (!arr.length)`
        raise ValueError("Cannot take the average of an empty list")
    return sum(numbers) / len(numbers)


def highest(numbers: list[float]) -> float:
    """Return the highest number in list.

    Raises ValueError on an empty list.
    """
    if not numbers:  # empty list: [] is falsy — like TS `if (!arr.length)`
        raise ValueError("Cannot take the highest of an empty list")
    return max(numbers)

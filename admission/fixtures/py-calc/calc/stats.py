"""Statistics helpers used by the reporting module."""


def mean(values):
    """Arithmetic mean of a non-empty sequence of numbers."""
    data = list(values)
    if not data:
        raise ValueError("mean() of empty data")
    return sum(data) / len(data)


def median(values):
    """Median of a non-empty sequence of numbers."""
    data = sorted(values)
    n = len(data)
    if n == 0:
        raise ValueError("median() of empty data")
    mid = n // 2
    if n % 2 == 1:
        return data[mid]
    return data[mid]

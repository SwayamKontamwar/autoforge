"""Machine‑learning utilities for the toolkit.

Currently provides a simple k‑nearest‑neighbour classifier using Euclidean
distance. The implementation is deliberately lightweight and has no external
dependencies.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Sequence, Tuple


def euclidean_knn(
    point: Sequence[float],
    data: Sequence[Tuple[Sequence[float], Any]],
    k: int,
) -> Any:
    """Classify ``point`` by majority label among its *k* nearest neighbours.

    Parameters
    ----------
    point:
        Sequence of numeric coordinates representing the query point.
    data:
        Iterable of ``(features, label)`` pairs where ``features`` is a sequence
        of the same dimension as ``point``.
    k:
        Number of neighbours to consider. Must satisfy ``1 <= k <= len(data)``.

    Returns
    -------
    The label that appears most frequently among the *k* nearest neighbours.

    Raises
    ------
    ValueError
        If ``k`` is not positive, exceeds the size of ``data``, or ``data`` is
        empty.
    """
    if k <= 0:
        raise ValueError("k must be positive")
    if not data:
        raise ValueError("data must not be empty")
    if k > len(data):
        raise ValueError("k cannot be larger than the dataset size")

    def _sq_dist(a: Sequence[float], b: Sequence[float]) -> float:
        return sum((x - y) ** 2 for x, y in zip(a, b))

    distances = [(_sq_dist(point, features), label) for features, label in data]
    distances.sort(key=lambda pair: pair[0])
    nearest_labels = [label for _, label in distances[:k]]
    most_common = Counter(nearest_labels).most_common(1)[0][0]
    return most_common

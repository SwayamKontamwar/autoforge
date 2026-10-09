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


def linear_fit_gd(
    xs: Sequence[float],
    ys: Sequence[float],
    *,
    lr: float = 0.01,
    epochs: int = 1000,
) -> Tuple[float, float]:
    """Fit a line ``y = m * x + b`` to data using gradient descent.

    Parameters
    ----------
    xs, ys:
        Sequences of equal length containing the x‑ and y‑coordinates of the
        training data.
    lr:
        Learning rate for gradient descent. Must be positive.
    epochs:
        Number of gradient‑descent iterations to perform. Must be positive.

    Returns
    -------
    Tuple[float, float]
        The slope ``m`` and intercept ``b`` that (approximately) minimise the
        mean‑squared error.

    Raises
    ------
    ValueError
        If ``xs`` and ``ys`` have different lengths, are empty, or if ``lr``
        or ``epochs`` are not positive.
    """
    if len(xs) != len(ys):
        raise ValueError("xs and ys must have the same length")
    if not xs:
        raise ValueError("xs and ys must not be empty")
    if lr <= 0:
        raise ValueError("learning rate must be positive")
    if epochs <= 0:
        raise ValueError("epochs must be positive")

    m = 0.0
    b = 0.0
    n = float(len(xs))

    for _ in range(epochs):
        # Compute predictions and errors
        preds = [m * x + b for x in xs]
        errors = [y - p for y, p in zip(ys, preds)]

        # Gradients of MSE w.r.t. m and b
        dm = (-2.0 / n) * sum(x * e for x, e in zip(xs, errors))
        db = (-2.0 / n) * sum(errors)

        # Update parameters
        m -= lr * dm
        b -= lr * db

    return m, b

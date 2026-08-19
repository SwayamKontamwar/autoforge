import pytest

from app.toolkit.ml import euclidean_knn


def test_euclidean_knn_typical() -> None:
    data = [
        ((0, 0), "A"),
        ((1, 1), "A"),
        ((2, 2), "B"),
        ((3, 3), "B"),
        ((0, 2), "C"),
    ]
    # Point close to (0,0) should be classified as "A" when k=3
    assert euclidean_knn((0.1, 0.1), data, 3) == "A"


def test_euclidean_knn_edge_cases() -> None:
    data = [((0, 0), "X")]
    # k=1 works
    assert euclidean_knn((5, 5), data, 1) == "X"
    # k=0 raises ValueError
    with pytest.raises(ValueError):
        euclidean_knn((0, 0), data, 0)
    # k larger than dataset raises ValueError
    with pytest.raises(ValueError):
        euclidean_knn((0, 0), data, 2)

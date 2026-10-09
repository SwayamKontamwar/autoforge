import pytest

from app.toolkit.ml import euclidean_knn, linear_fit_gd


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


def test_linear_fit_gd_typical() -> None:
    # Points lie exactly on y = 2*x + 1
    xs = [0.0, 1.0, 2.0, 3.0]
    ys = [1.0, 3.0, 5.0, 7.0]
    m, b = linear_fit_gd(xs, ys, lr=0.1, epochs=2000)
    assert abs(m - 2.0) < 0.01
    assert abs(b - 1.0) < 0.01


def test_linear_fit_gd_edge_cases() -> None:
    # Mismatched lengths
    with pytest.raises(ValueError):
        linear_fit_gd([0, 1], [1], lr=0.1, epochs=10)
    # Empty data
    with pytest.raises(ValueError):
        linear_fit_gd([], [], lr=0.1, epochs=10)

import pytest

from app.toolkit.physics import work_done


def test_work_done_typical() -> None:
    # 10 N force over 5 m displacement → 50 J
    assert work_done(10, 5) == pytest.approx(50.0, rel=1e-12)


def test_work_done_edge_cases() -> None:
    # Zero force yields zero work
    assert work_done(0, 100) == 0.0
    # Negative force opposite displacement → negative work
    assert work_done(-10, 2) == pytest.approx(-20.0, rel=1e-12)
    # Type validation
    with pytest.raises(TypeError):
        work_done("force", 2)
    with pytest.raises(TypeError):
        work_done(2, None)

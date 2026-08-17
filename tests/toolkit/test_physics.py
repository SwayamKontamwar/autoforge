import pytest

from app.toolkit.physics import kinetic_energy


def test_kinetic_energy_typical() -> None:
    # mass = 10 kg, velocity = 5 m/s → 0.5 · 10 · 25 = 125 J
    assert kinetic_energy(10, 5) == pytest.approx(125.0, rel=1e-12)
    # velocity can be negative; square removes sign
    assert kinetic_energy(2, -3) == pytest.approx(9.0, rel=1e-12)


def test_kinetic_energy_edge_cases() -> None:
    # Zero mass yields zero energy regardless of velocity
    assert kinetic_energy(0, 100) == 0.0
    # Zero velocity yields zero energy
    assert kinetic_energy(5, 0) == 0.0
    # Negative mass is invalid
    with pytest.raises(ValueError):
        kinetic_energy(-1, 2)
    # Non‑numeric inputs raise TypeError
    with pytest.raises(TypeError):
        kinetic_energy("mass", 2)
    with pytest.raises(TypeError):
        kinetic_energy(2, "fast")

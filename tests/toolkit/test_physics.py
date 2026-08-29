import pytest

from app.toolkit.physics import kinetic_energy, potential_energy


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


def test_potential_energy_typical() -> None:
    # mass = 10 kg, height = 5 m → 10 · 9.80665 · 5 = 490.3325 J
    expected = 10 * 9.80665 * 5
    assert potential_energy(10, 5) == pytest.approx(expected, rel=1e-12)
    # custom gravity (e.g., Moon ~1.62 m·s⁻²)
    assert potential_energy(2, 3, g=1.62) == pytest.approx(2 * 1.62 * 3, rel=1e-12)


def test_potential_energy_edge_cases() -> None:
    # Zero mass yields zero energy regardless of height
    assert potential_energy(0, 100) == 0.0
    # Zero height yields zero energy
    assert potential_energy(5, 0) == 0.0
    # Negative height yields negative energy (below reference)
    assert potential_energy(5, -2) == pytest.approx(5 * 9.80665 * -2, rel=1e-12)
    # Negative mass is invalid
    with pytest.raises(ValueError):
        potential_energy(-1, 10)
    # Non‑numeric inputs raise TypeError
    with pytest.raises(TypeError):
        potential_energy("mass", 10)
    with pytest.raises(TypeError):
        potential_energy(10, "height")
    with pytest.raises(TypeError):
        potential_energy(10, 5, g="gravity")

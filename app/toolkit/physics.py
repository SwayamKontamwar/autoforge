"""Physics‑related utility functions.

Provides calculators for kinetic energy, gravitational potential energy,
and mechanical work.

The kinetic energy (in joules) of an object with mass *m* (kg) moving at
velocity *v* (m/s) is given by:

    KE = ½ · m · v²

The potential energy (in joules) of an object with mass *m* (kg) at height
*h* (m) in a gravitational field of strength *g* (m·s⁻²) is:

    PE = m · g · h

The work (in joules) done by a constant force *F* (N) moving an object
through a displacement *d* (m) is:

    W = F · d

Both *mass* and *velocity* must be real numbers.  A negative mass is
physically undefined and therefore raises :class:`ValueError`.  For
*force* and *displacement*, any real numbers are accepted; the result may
be negative if the force opposes the displacement.

All functions raise :class:`TypeError` for non‑numeric inputs.
"""

from __future__ import annotations

from numbers import Real


def _ensure_real(value: Real, name: str) -> None:
    """Validate that *value* is a real number (int or float)."""
    if not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number, got {type(value)!r}")


def kinetic_energy(mass: Real, velocity: Real) -> float:
    """Return the kinetic energy (J) for *mass* (kg) and *velocity* (m/s).

    Raises:
        TypeError: If *mass* or *velocity* is not a real number.
        ValueError: If *mass* is negative.
    """
    _ensure_real(mass, "mass")
    _ensure_real(velocity, "velocity")
    if mass < 0:
        raise ValueError("mass cannot be negative")
    return 0.5 * mass * velocity * velocity


def potential_energy(mass: Real, height: Real, g: Real = 9.80665) -> float:
    """Return the gravitational potential energy (J).

    *mass* is in kilograms, *height* in meters, and *g* is the gravitational
    acceleration (default is standard Earth gravity).

    Raises:
        TypeError: If any argument is not a real number.
        ValueError: If *mass* is negative.
    """
    _ensure_real(mass, "mass")
    _ensure_real(height, "height")
    _ensure_real(g, "g")
    if mass < 0:
        raise ValueError("mass cannot be negative")
    return mass * g * height


def work_done(force: Real, displacement: Real) -> float:
    """Return the mechanical work (J) done by *force* (N) over *displacement* (m).

    Both arguments must be real numbers.  The sign of the result indicates
    whether the force assists (positive) or opposes (negative) the motion.

    Raises:
        TypeError: If *force* or *displacement* is not a real number.
    """
    _ensure_real(force, "force")
    _ensure_real(displacement, "displacement")
    return force * displacement

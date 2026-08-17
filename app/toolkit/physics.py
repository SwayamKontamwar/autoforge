"""Physics‑related utility functions.

Currently provides a simple kinetic energy calculator.

The kinetic energy (in joules) of an object with mass *m* (kg) moving at
velocity *v* (m/s) is given by:

    KE = ½ · m · v²

Both *mass* and *velocity* must be real numbers.  A negative mass is
physically undefined and therefore raises :class:`ValueError`.  Velocity
may be negative; the square eliminates the sign.
"""

from __future__ import annotations

from numbers import Real


def kinetic_energy(mass: Real, velocity: Real) -> float:
    """Return the kinetic energy (½ · mass · velocity²).

    Args:
        mass: Mass of the object in kilograms. Must be non‑negative.
        velocity: Velocity of the object in metres per second.

    Returns:
        Kinetic energy in joules as a float.

    Raises:
        TypeError: If *mass* or *velocity* is not a real number.
        ValueError: If *mass* is negative.
    """
    if not isinstance(mass, Real):
        raise TypeError("mass must be a real number")
    if not isinstance(velocity, Real):
        raise TypeError("velocity must be a real number")
    if mass < 0:
        raise ValueError("mass cannot be negative")
    # Using float conversion ensures the result is a float even for int inputs.
    return 0.5 * float(mass) * (float(velocity) ** 2)

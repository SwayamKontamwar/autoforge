"""Physics‑related utility functions.

Currently provides a simple kinetic energy calculator and a gravitational
potential energy calculator.

The kinetic energy (in joules) of an object with mass *m* (kg) moving at
velocity *v* (m/s) is given by:

    KE = ½ · m · v²

Both *mass* and *velocity* must be real numbers.  A negative mass is
physically undefined and therefore raises :class:`ValueError`.  Velocity
may be negative; the square eliminates the sign.

The gravitational potential energy (in joules) of an object with mass *m*
(kg) at height *h* (m) above a reference level is given by:

    PE = m · g · h

where *g* is the standard acceleration due to gravity (9.80665 m·s⁻²).
*mass* must be non‑negative; *height* may be any real number.
"""

from __future__ import annotations

from numbers import Real

# Standard gravity in m·s⁻²
_STANDARD_GRAVITY = 9.80665


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


def potential_energy(mass: Real, height: Real, *, g: Real = _STANDARD_GRAVITY) -> float:
    """Return the gravitational potential energy (mass · g · height).

    Args:
        mass: Mass of the object in kilograms. Must be non‑negative.
        height: Height above the reference level in metres. May be any real.
        g: Acceleration due to gravity (m·s⁻²). Defaults to standard gravity.

    Returns:
        Potential energy in joules as a float.

    Raises:
        TypeError: If *mass*, *height*, or *g* is not a real number.
        ValueError: If *mass* is negative.
    """
    if not isinstance(mass, Real):
        raise TypeError("mass must be a real number")
    if not isinstance(height, Real):
        raise TypeError("height must be a real number")
    if not isinstance(g, Real):
        raise TypeError("g must be a real number")
    if mass < 0:
        raise ValueError("mass cannot be negative")
    return float(mass) * float(g) * float(height)

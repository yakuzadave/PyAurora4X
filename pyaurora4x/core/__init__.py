"""
Core module for PyAurora 4X

Contains shared data models, enums, utilities, and event systems.
"""

from pyaurora4x.core.models import (
    Empire,
    Fleet,
    Ship,
    Colony,
    StarSystem,
    Planet,
    Vector3D,
    AsteroidBelt,
    Technology,
)
from pyaurora4x.core.enums import (
    PlanetType,
    StarType,
    FleetStatus,
    TechnologyType,
    ShipType,
)
from pyaurora4x.core.events import EventManager, GameEvent
from pyaurora4x.core.utils import distance_3d, angle_between_vectors

__all__ = [
    "Empire",
    "Fleet",
    "Ship",
    "Colony",
    "StarSystem",
    "Planet",
    "AsteroidBelt",
    "Vector3D",
    "Technology",
    "PlanetType",
    "StarType",
    "FleetStatus",
    "TechnologyType",
    "ShipType",
    "EventManager",
    "GameEvent",
    "distance_3d",
    "angle_between_vectors",
]

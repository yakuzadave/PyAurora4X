"""
Engine module for PyAurora 4X

Contains the core simulation logic, orbital mechanics, scheduling,
and game state management.
"""

from pyaurora4x.engine.simulation import GameSimulation
from pyaurora4x.engine.scheduler import GameScheduler
from pyaurora4x.engine.orbital_mechanics import OrbitalMechanics
from pyaurora4x.engine.star_system import StarSystemGenerator
from pyaurora4x.engine.turn_manager import GameTurnManager
from pyaurora4x.engine.shipyard_manager import ShipyardManager

__all__ = [
    "GameSimulation",
    "GameScheduler",
    "OrbitalMechanics",
    "StarSystemGenerator",
    "GameTurnManager",
    "ShipyardManager",
]

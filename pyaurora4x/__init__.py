"""
PyAurora 4X - A Python-based 4X space strategy game

This package provides a modular architecture for building a space strategy game
with realistic orbital mechanics, terminal UI, and extensible gameplay systems.
"""

__version__ = "0.1.0"
__author__ = "PyAurora4X Development Team"
__description__ = "Terminal-based 4X space strategy game with realistic orbital mechanics"

# Package-level imports for convenience
from pyaurora4x.core.models import Empire, Fleet, Ship, Colony, StarSystem, Planet
from pyaurora4x.engine.simulation import GameSimulation
from pyaurora4x.ui.main_app import PyAurora4XApp

__all__ = [
    "Empire",
    "Fleet", 
    "Ship",
    "Colony",
    "StarSystem",
    "Planet",
    "GameSimulation",
    "PyAurora4XApp",
]

"""
PyAurora 4X - A Python-based 4X space strategy game

This package provides a modular architecture for building a space strategy game
with realistic orbital mechanics, terminal UI, and extensible gameplay systems.
"""

__version__ = "0.1.0"
__author__ = "PyAurora4X Development Team"
__description__ = "Terminal-based 4X space strategy game with realistic orbital mechanics"

# Minimal package-level exports to avoid heavy import side effects
from pyaurora4x.core.models import Empire, Fleet, Ship, Colony, StarSystem, Planet

__all__ = [
    "__version__",
    "Empire",
    "Fleet",
    "Ship",
    "Colony",
    "StarSystem",
    "Planet",
]

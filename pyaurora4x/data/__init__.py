"""
Data management module for PyAurora 4X

Handles save/load operations, technology trees, ship components,
and other game data management.
"""

from pyaurora4x.data.save_manager import SaveManager
from pyaurora4x.data.tech_tree import TechTreeManager
from pyaurora4x.data.ship_components import ShipComponentManager

__all__ = [
    "SaveManager",
    "TechTreeManager",
    "ShipComponentManager",
]


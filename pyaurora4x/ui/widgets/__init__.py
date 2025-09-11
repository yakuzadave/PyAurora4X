"""
UI Widgets for PyAurora 4X

Custom Textual widgets for displaying game information and controls.
"""

from pyaurora4x.ui.widgets.star_system_view import StarSystemView
from pyaurora4x.ui.widgets.fleet_panel import FleetPanel
from pyaurora4x.ui.widgets.research_panel import ResearchPanel
from pyaurora4x.ui.widgets.empire_stats import EmpireStatsWidget
from pyaurora4x.ui.widgets.load_dialog import LoadGameDialog
from pyaurora4x.ui.widgets.planet_select_dialog import PlanetSelectDialog
from pyaurora4x.ui.widgets.ship_design_panel import ShipDesignPanel
from pyaurora4x.ui.widgets.colony_management_panel import ColonyManagementPanel

__all__ = [
    "StarSystemView",
    "FleetPanel", 
    "ResearchPanel",
    "EmpireStatsWidget",
    "LoadGameDialog",
    "PlanetSelectDialog",
    "ShipDesignPanel",
    "ColonyManagementPanel",
]

"""
Colony Management Panel for PyAurora 4X

Provides comprehensive colony infrastructure management including building
construction, resource production, and construction queue management.
"""

from typing import Optional, Dict, List, Any
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Label, Button, DataTable, ProgressBar, Select
from textual.reactive import reactive
from textual.message import Message
from textual.binding import Binding

from pyaurora4x.core.models import Colony, Empire
from pyaurora4x.core.enums import BuildingType, ConstructionStatus
from pyaurora4x.core.infrastructure import BuildingTemplate, Building, ConstructionProject
from pyaurora4x.engine.infrastructure_manager import ColonyInfrastructureManager
from pyaurora4x.core.events import EventManager, EventCategory


class ColonyManagementPanel(Static):
    """
    Comprehensive colony management interface.
    
    Features:
    - Colony overview with population and resources
    - Building list with production details
    - Construction queue management
    - Available buildings for construction
    - Resource production summary
    """
    
    BINDINGS = [
        Binding("b", "build_menu", "Build", show=True),
        Binding("c", "cancel_construction", "Cancel", show=True),
        Binding("d", "demolish_building", "Demolish", show=True),
        Binding("u", "upgrade_building", "Upgrade", show=True),
    ]
    
    selected_colony = reactive(None)
    selected_empire = reactive(None)
    
    def __init__(self, infrastructure_manager: Optional[ColonyInfrastructureManager] = None,
                 event_manager: Optional[EventManager] = None, **kwargs):
        super().__init__(**kwargs)
        self.infrastructure_manager = infrastructure_manager
        self.event_manager = event_manager
        self.current_colony: Optional[Colony] = None
        self.current_empire: Optional[Empire] = None
        
        # UI state
        self.selected_building_row: Optional[int] = None
        self.selected_construction_row: Optional[int] = None
    
    def compose(self) -> ComposeResult:
        """Compose the colony management layout."""
        with Container(id="colony_management_container"):
            yield Label("Colony Management", classes="panel-title")
            
            with Horizontal(id="colony_main_layout"):
                # Left panel - Colony overview and buildings
                with Vertical(id="colony_left_panel", classes="panel"):
                    yield Label("Colony Overview", classes="section-title")
                    yield Static("", id="colony_overview", classes="info-section")
                    
                    yield Label("Buildings", classes="section-title")
                    with Container(id="buildings_container"):
                        yield DataTable(id="buildings_table", classes="data-table")
                        
                    yield Label("Resource Production", classes="section-title")
                    yield Static("", id="resource_production", classes="info-section")
                
                # Right panel - Construction and available buildings
                with Vertical(id="colony_right_panel", classes="panel"):
                    yield Label("Construction Queue", classes="section-title")
                    with Container(id="construction_container"):
                        yield DataTable(id="construction_table", classes="data-table")
                    
                    with Horizontal(id="construction_controls"):
                        yield Button("Build", id="build_button", variant="success")
                        yield Button("Cancel", id="cancel_button", variant="outline")
                        yield Button("Priority ↑", id="priority_up_button", variant="outline")
                        yield Button("Priority ↓", id="priority_down_button", variant="outline")
                    
                    yield Label("Available Buildings", classes="section-title")
                    with Container(id="available_buildings_container"):
                        yield DataTable(id="available_buildings_table", classes="data-table")
    
    def on_mount(self) -> None:
        """Initialize the widget when mounted."""
        self._setup_tables()
        self._update_display()
    
    def _setup_tables(self) -> None:
        """Setup data table columns."""
        # Buildings table
        buildings_table = self.query_one("#buildings_table", DataTable)
        buildings_table.add_columns("Building", "Status", "Production", "Efficiency", "Actions")
        buildings_table.cursor_type = "row"
        
        # Construction table
        construction_table = self.query_one("#construction_table", DataTable)
        construction_table.add_columns("Building", "Progress", "ETA", "Priority")
        construction_table.cursor_type = "row"
        
        # Available buildings table
        available_table = self.query_one("#available_buildings_table", DataTable)
        available_table.add_columns("Building", "Cost", "Time", "Requirements")
        available_table.cursor_type = "row"
    
    def update_colony(self, colony: Colony, empire: Empire) -> None:
        """Update the displayed colony and empire."""
        self.current_colony = colony
        self.current_empire = empire
        self.selected_colony = colony
        self.selected_empire = empire
        self._update_display()
    
    def _update_display(self) -> None:
        """Update all display sections."""
        if not self.current_colony or not self.current_empire or not self.infrastructure_manager:
            self._show_no_colony()
            return
        
        self._update_colony_overview()
        self._update_buildings_table()
        self._update_construction_table()
        self._update_available_buildings()
        self._update_resource_production()
    
    def _show_no_colony(self) -> None:
        """Show message when no colony is selected."""
        try:
            overview = self.query_one("#colony_overview", Static)
            overview.update("No colony selected")
            
            # Clear tables
            buildings_table = self.query_one("#buildings_table", DataTable)
            buildings_table.clear()
            
            construction_table = self.query_one("#construction_table", DataTable)
            construction_table.clear()
            
            available_table = self.query_one("#available_buildings_table", DataTable)
            available_table.clear()
            
            production = self.query_one("#resource_production", Static)
            production.update("")
        except Exception:
            pass  # Widgets might not be ready yet
    
    def _update_colony_overview(self) -> None:
        """Update colony overview information."""
        colony = self.current_colony
        if not colony:
            return
        
        lines = []
        lines.append(f"Colony: {colony.name}")
        lines.append(f"Population: {colony.population:,}/{colony.max_population:,}")
        lines.append(f"Growth Rate: {colony.growth_rate:.2f}")
        lines.append(f"Happiness: {colony.happiness:.1f}%")
        lines.append(f"Efficiency: {colony.efficiency:.1%}")
        
        # Power status
        lines.append("")
        lines.append(f"Power: {colony.power_generation:.1f}/{colony.power_consumption:.1f}")
        power_status = "Sufficient" if colony.power_generation >= colony.power_consumption else "Deficit"
        lines.append(f"Status: {power_status}")
        
        # Defense
        lines.append(f"Defense: {colony.defense_rating:.0f}")
        
        # Stockpiles
        if colony.stockpiles:
            lines.append("")
            lines.append("Resources:")
            for resource, amount in colony.stockpiles.items():
                lines.append(f"  {resource.title()}: {amount:.1f}")
        
        text = "\\n".join(lines)
        
        try:
            overview = self.query_one("#colony_overview", Static)
            overview.update(text)
        except Exception:
            pass
    
    def _update_buildings_table(self) -> None:
        """Update the buildings table."""
        buildings_table = self.query_one("#buildings_table", DataTable)
        buildings_table.clear()
        
        if not self.infrastructure_manager or not self.current_colony:
            return
        
        state = self.infrastructure_manager.get_colony_state(self.current_colony.id)
        if not state:
            return
        
        # Add buildings to table
        for building_id, building in state.buildings.items():
            template = self.infrastructure_manager.building_templates.get(building.template_id)
            if not template:
                continue
            
            # Format production info
            production_info = []
            for resource, amount in template.resource_production.items():
                production_info.append(f"+{amount:.1f} {resource}/day")
            for resource, amount in template.resource_consumption.items():
                production_info.append(f"-{amount:.1f} {resource}/day")
            
            production_text = ", ".join(production_info) if production_info else "None"
            
            # Status and efficiency
            status = building.status.title()
            efficiency = f"{building.efficiency:.1%}"
            
            # Actions (simplified for display)
            actions = "Upgrade" if template.can_upgrade_to else "Demolish"
            
            buildings_table.add_row(
                template.name,
                status,
                production_text,
                efficiency,
                actions,
                key=building_id
            )
    
    def _update_construction_table(self) -> None:
        """Update the construction queue table."""
        construction_table = self.query_one("#construction_table", DataTable)
        construction_table.clear()
        
        if not self.infrastructure_manager or not self.current_colony:
            return
        
        state = self.infrastructure_manager.get_colony_state(self.current_colony.id)
        if not state:
            return
        
        # Add construction projects to table
        for project_id in state.construction_queue:
            project = state.construction_projects.get(project_id)
            if not project:
                continue
                
            template = self.infrastructure_manager.building_templates.get(project.building_template_id)
            if not template:
                continue
            
            # Format progress
            progress_text = f"{project.progress * 100:.1f}%"
            
            # ETA calculation (simplified)
            if project.status == ConstructionStatus.IN_PROGRESS:
                remaining_time = project.construction_time * (1.0 - project.progress)
                eta_hours = remaining_time / 3600
                eta_text = f"{eta_hours:.1f}h"
            else:
                eta_text = "Waiting"
            
            construction_table.add_row(
                template.name,
                progress_text,
                eta_text,
                str(project.priority),
                key=project_id
            )
    
    def _update_available_buildings(self) -> None:
        """Update the available buildings table."""
        available_table = self.query_one("#available_buildings_table", DataTable)
        available_table.clear()
        
        if not self.infrastructure_manager or not self.current_empire:
            return
        
        available_buildings = self.infrastructure_manager.get_available_buildings(self.current_empire)
        
        for template in available_buildings:
            # Format cost
            cost_info = []
            for resource, amount in template.construction_cost.items():
                cost_info.append(f"{amount:.0f} {resource}")
            cost_text = ", ".join(cost_info)
            
            # Format time
            time_hours = template.construction_time / 3600
            time_text = f"{time_hours:.1f}h"
            
            # Format requirements
            requirements = []
            if template.tech_requirements:
                requirements.extend([f"{tech.value}" for tech in template.tech_requirements])
            if template.population_requirement > 0:
                requirements.append(f"{template.population_requirement} pop")
            requirements_text = ", ".join(requirements) if requirements else "None"
            
            # Check if can build
            can_build, reason = self.infrastructure_manager.can_build(
                self.current_colony, self.current_empire, template.id
            ) if self.current_colony else (False, "No colony")
            
            # Add styling based on buildability
            building_name = template.name
            if not can_build:
                building_name = f"[dim]{building_name}[/dim]"
            
            available_table.add_row(
                building_name,
                cost_text,
                time_text,
                requirements_text,
                key=template.id
            )
    
    def _update_resource_production(self) -> None:
        """Update resource production summary."""
        if not self.infrastructure_manager or not self.current_colony:
            return
        
        state = self.infrastructure_manager.get_colony_state(self.current_colony.id)
        if not state:
            return
        
        lines = []
        lines.append("=== Daily Production ===")
        
        # Production
        if state.daily_production:
            lines.append("")
            lines.append("Production:")
            for resource, amount in state.daily_production.items():
                lines.append(f"  +{amount:.1f} {resource.title()}")
        
        # Consumption
        if state.daily_consumption:
            lines.append("")
            lines.append("Consumption:")
            for resource, amount in state.daily_consumption.items():
                lines.append(f"  -{amount:.1f} {resource.title()}")
        
        # Net production
        if state.net_production:
            lines.append("")
            lines.append("Net Production:")
            for resource, amount in state.net_production.items():
                sign = "+" if amount >= 0 else ""
                color = "green" if amount >= 0 else "red"
                lines.append(f"  [{color}]{sign}{amount:.1f} {resource.title()}[/{color}]")
        
        if not lines or len(lines) == 1:
            lines.append("No production configured")
        
        text = "\\n".join(lines)
        
        try:
            production = self.query_one("#resource_production", Static)
            production.update(text)
        except Exception:
            pass
    
    # Event handlers
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "build_button":
            self._handle_build_action()
        elif event.button.id == "cancel_button":
            self._handle_cancel_construction()
        elif event.button.id == "priority_up_button":
            self._handle_priority_change(1)
        elif event.button.id == "priority_down_button":
            self._handle_priority_change(-1)
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle table row selections."""
        if event.data_table.id == "buildings_table":
            self.selected_building_row = event.row_index
        elif event.data_table.id == "construction_table":
            self.selected_construction_row = event.row_index
        elif event.data_table.id == "available_buildings_table":
            self._handle_build_selection(event)
    
    def _handle_build_selection(self, event: DataTable.RowSelected) -> None:
        """Handle selection of an available building."""
        if not self.infrastructure_manager or not self.current_colony or not self.current_empire:
            return
        
        # Get the building template ID from the selected row
        row_key = event.data_table.get_row_at(event.row_index).key
        if not row_key:
            return
        
        template_id = str(row_key)
        template = self.infrastructure_manager.building_templates.get(template_id)
        if not template:
            return
        
        # Attempt to start construction
        success, message = self.infrastructure_manager.start_construction(
            self.current_colony, self.current_empire, template_id
        )
        
        # Show notification
        if self.event_manager:
            category = EventCategory.COLONY if success else EventCategory.SYSTEM
            self.event_manager.add_event(
                category=category,
                title=f"Construction: {template.name}",
                description=message,
                empire_id=self.current_empire.id
            )
        
        # Update display
        self._update_display()
    
    def _handle_build_action(self) -> None:
        """Handle build button press."""
        # This would typically open a build menu or dialog
        # For now, we'll just show available buildings focus
        available_table = self.query_one("#available_buildings_table", DataTable)
        available_table.focus()
    
    def _handle_cancel_construction(self) -> None:
        """Handle construction cancellation."""
        if (not self.infrastructure_manager or not self.current_colony or 
            self.selected_construction_row is None):
            return
        
        construction_table = self.query_one("#construction_table", DataTable)
        if self.selected_construction_row >= construction_table.row_count:
            return
        
        # Get project ID from selected row
        row_key = construction_table.get_row_at(self.selected_construction_row).key
        if not row_key:
            return
        
        project_id = str(row_key)
        success = self.infrastructure_manager.cancel_construction(self.current_colony.id, project_id)
        
        if success and self.event_manager:
            self.event_manager.add_event(
                category=EventCategory.COLONY,
                title="Construction Cancelled",
                description=f"Cancelled construction project in {self.current_colony.name}",
                empire_id=self.current_empire.id if self.current_empire else ""
            )
        
        self._update_display()
    
    def _handle_priority_change(self, delta: int) -> None:
        """Handle construction priority changes."""
        if (not self.infrastructure_manager or not self.current_colony or 
            self.selected_construction_row is None):
            return
        
        # Implementation would adjust construction priority
        # For now, just refresh display
        self._update_display()
    
    def action_build_menu(self) -> None:
        """Show build menu."""
        self._handle_build_action()
    
    def action_cancel_construction(self) -> None:
        """Cancel selected construction."""
        self._handle_cancel_construction()
    
    def action_demolish_building(self) -> None:
        """Demolish selected building."""
        if (not self.infrastructure_manager or not self.current_colony or 
            self.selected_building_row is None):
            return
        
        buildings_table = self.query_one("#buildings_table", DataTable)
        if self.selected_building_row >= buildings_table.row_count:
            return
        
        # Get building ID from selected row
        row_key = buildings_table.get_row_at(self.selected_building_row).key
        if not row_key:
            return
        
        building_id = str(row_key)
        success = self.infrastructure_manager.demolish_building(self.current_colony, building_id)
        
        if success and self.event_manager:
            self.event_manager.add_event(
                category=EventCategory.COLONY,
                title="Building Demolished",
                description=f"Demolished building in {self.current_colony.name}",
                empire_id=self.current_empire.id if self.current_empire else ""
            )
        
        self._update_display()
    
    def action_upgrade_building(self) -> None:
        """Upgrade selected building."""
        if (not self.infrastructure_manager or not self.current_colony or not self.current_empire or
            self.selected_building_row is None):
            return
        
        buildings_table = self.query_one("#buildings_table", DataTable)
        if self.selected_building_row >= buildings_table.row_count:
            return
        
        # Get building ID from selected row
        row_key = buildings_table.get_row_at(self.selected_building_row).key
        if not row_key:
            return
        
        building_id = str(row_key)
        success, message = self.infrastructure_manager.upgrade_building(
            self.current_colony, self.current_empire, building_id
        )
        
        if self.event_manager:
            category = EventCategory.COLONY if success else EventCategory.SYSTEM
            self.event_manager.add_event(
                category=category,
                title="Building Upgrade",
                description=message,
                empire_id=self.current_empire.id
            )
        
        self._update_display()
    
    def watch_selected_colony(self, colony: Colony) -> None:
        """React to colony selection changes."""
        if colony and self.current_empire:
            self.update_colony(colony, self.current_empire)
    
    def watch_selected_empire(self, empire: Empire) -> None:
        """React to empire selection changes."""
        if empire and self.current_colony:
            self.update_colony(self.current_colony, empire)

"""Ship Design Panel Widget.

Provides a comprehensive interface for creating and managing ship designs
from available components with validation, cost calculation, and persistence.
"""

from typing import List, Optional, Dict, Any
from textual.widgets import (
    Static, DataTable, Button, Label, Input, Select, 
    OptionList, Collapsible, ListView, ListItem, ProgressBar
)
from textual.containers import Vertical, Horizontal, Container, Grid
from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.validation import ValidationResult, Validator
from textual import events

from pyaurora4x.core.models import Empire, ShipDesign, ShipComponent, Technology
from pyaurora4x.core.enums import ShipType
from pyaurora4x.data.ship_components import ShipComponentManager


class DesignNameValidator(Validator):
    """Validates ship design names."""
    
    def validate(self, value: str) -> ValidationResult:
        """Validate design name."""
        if not value.strip():
            return self.failure("Design name cannot be empty")
        if len(value) > 50:
            return self.failure("Design name too long (max 50 characters)")
        return self.success()


class ShipDesignPanel(Static):
    """Comprehensive widget for managing ship designs."""
    
    # Reactive attributes for real-time updates
    current_design_cost = reactive(0)
    current_design_mass = reactive(0.0)
    current_crew_required = reactive(0)
    design_valid = reactive(True)
    validation_errors = reactive([])
    validation_warnings = reactive([])

    def __init__(self, component_manager: ShipComponentManager, **kwargs):
        super().__init__(**kwargs)
        self.component_manager = component_manager
        self.empire: Optional[Empire] = None
        self.selected_components: List[str] = []
        self.current_design: Optional[ShipDesign] = None
        self.researched_techs: set[str] = set()
        self.available_components: List[ShipComponent] = []
        self.component_filter: str = "all"

    def compose(self) -> ComposeResult:
        """Compose the ship design panel layout."""
        with Container(id="design_container", classes="panel"):
            # Top section: Design info and controls
            with Container(id="design_header"):
                with Horizontal():
                    with Vertical(id="design_info"):
                        yield Label("Ship Design System", classes="title")
                        with Horizontal():
                            yield Label("Design Name:", classes="label")
                            yield Input(
                                placeholder="Enter design name",
                                id="design_name",
                                validators=[DesignNameValidator()]
                            )
                        with Horizontal():
                            yield Label("Ship Type:", classes="label")
                            yield Select(
                                [(ship_type.value.title(), ship_type) for ship_type in ShipType],
                                id="ship_type",
                                value=ShipType.FRIGATE
                            )
                    
                    with Vertical(id="design_stats"):
                        yield Label("Design Statistics", classes="subtitle")
                        yield Label("Cost: 0", id="cost_display")
                        yield Label("Mass: 0.0 tons", id="mass_display")
                        yield Label("Crew: 0", id="crew_display")
                        yield ProgressBar(total=100, show_eta=False, id="design_progress")
            
            # Main content area
            with Horizontal(id="main_content"):
                # Left panel: Available components
                with Vertical(id="components_panel", classes="panel"):
                    yield Label("Available Components", classes="subtitle")
                    with Horizontal():
                        yield Select(
                            [
                                ("All Components", "all"),
                                ("Engines", "engine"),
                                ("Power Plants", "power_plant"),
                                ("Weapons", "weapon"),
                                ("Shields", "shield"),
                                ("Sensors", "sensor"),
                                ("Life Support", "crew_quarters"),
                                ("Cargo", "cargo_bay"),
                                ("Other", "other")
                            ],
                            id="component_filter",
                            value="all"
                        )
                        yield Button("Refresh", id="refresh_components", variant="default")
                    yield DataTable(id="component_table")
                
                # Center panel: Selected components and design preview
                with Vertical(id="design_panel", classes="panel"):
                    yield Label("Current Design", classes="subtitle")
                    yield DataTable(id="selected_table")
                    
                    with Horizontal():
                        yield Button("Remove Selected", id="remove_component", variant="warning")
                        yield Button("Clear All", id="clear_design", variant="error")
                
                # Right panel: Validation and saved designs
                with Vertical(id="validation_panel", classes="panel"):
                    with Collapsible(title="Design Validation", collapsed=False):
                        yield Label("✓ Design Valid", id="validation_status")
                        yield ListView(id="validation_messages")
                    
                    with Collapsible(title="Saved Designs", collapsed=True):
                        yield DataTable(id="saved_designs")
                        yield Button("Load Design", id="load_design", variant="default")
                        yield Button("Delete Design", id="delete_design", variant="error")
            
            # Bottom section: Action buttons
            with Container(id="design_actions"):
                with Horizontal():
                    yield Button("Save Design", id="save_design", variant="success")
                    yield Button("Build Ship", id="build_ship", variant="primary")
                    yield Button("Export Design", id="export_design", variant="default")
                    yield Button("Reset", id="reset_panel", variant="warning")

    def on_mount(self) -> None:
        """Initialize the panel on mount."""
        self._setup_component_table()
        self._setup_selected_table()
        self._setup_saved_designs_table()
        self._refresh_components()
        self._update_design_stats()
    
    def _setup_component_table(self) -> None:
        """Set up the available components table."""
        table = self.query_one("#component_table", DataTable)
        table.add_columns("Component", "Type", "Cost", "Mass", "Tech Req")
        table.cursor_type = "row"
    
    def _setup_selected_table(self) -> None:
        """Set up the selected components table."""
        table = self.query_one("#selected_table", DataTable)
        table.add_columns("Component", "Type", "Cost", "Mass", "Qty")
        table.cursor_type = "row"
    
    def _setup_saved_designs_table(self) -> None:
        """Set up the saved designs table."""
        table = self.query_one("#saved_designs", DataTable)
        table.add_columns("Name", "Type", "Cost", "Mass")
        table.cursor_type = "row"

    def _refresh_components(self) -> None:
        """Refresh the available components list based on current filter and tech."""
        if not self.empire:
            self.available_components = list(self.component_manager.components.values())
        else:
            # Get researched technologies
            self.researched_techs = {
                tech_id for tech_id, tech in self.empire.technologies.items() 
                if tech.is_researched
            }
            self.available_components = self.component_manager.get_available_components(
                list(self.researched_techs)
            )
        
        # Apply type filter
        if self.component_filter != "all":
            if self.component_filter == "other":
                filtered = [
                    c for c in self.available_components 
                    if c.component_type not in {
                        "engine", "power_plant", "weapon", "shield", 
                        "sensor", "crew_quarters", "cargo_bay"
                    }
                ]
            else:
                filtered = [
                    c for c in self.available_components 
                    if c.component_type == self.component_filter
                ]
            self.available_components = filtered
        
        self._populate_component_table()
    
    def _populate_component_table(self) -> None:
        """Populate the components table with available components."""
        table = self.query_one("#component_table", DataTable)
        table.clear()
        
        for comp in self.available_components:
            tech_req = ", ".join(comp.tech_requirements) if comp.tech_requirements else "None"
            table.add_row(
                comp.name,
                comp.component_type.title(),
                str(comp.cost),
                f"{comp.mass:.1f}",
                tech_req,
                key=comp.id
            )
    
    def _update_selected_table(self) -> None:
        """Update the selected components table."""
        table = self.query_one("#selected_table", DataTable)
        table.clear()
        
        # Count component quantities
        component_counts: Dict[str, int] = {}
        for comp_id in self.selected_components:
            component_counts[comp_id] = component_counts.get(comp_id, 0) + 1
        
        for comp_id, count in component_counts.items():
            comp = self.component_manager.get_component(comp_id)
            if comp:
                table.add_row(
                    comp.name,
                    comp.component_type.title(),
                    str(comp.cost * count),
                    f"{comp.mass * count:.1f}",
                    str(count),
                    key=comp_id
                )
    
    def _update_design_stats(self) -> None:
        """Update design statistics and validation."""
        # Calculate totals
        total_cost = 0
        total_mass = 0.0
        total_crew = 0
        
        selected_components = []
        for comp_id in self.selected_components:
            comp = self.component_manager.get_component(comp_id)
            if comp:
                selected_components.append(comp)
                total_cost += comp.cost
                total_mass += comp.mass
                total_crew += comp.crew_requirement
        
        # Update reactive attributes
        self.current_design_cost = total_cost
        self.current_design_mass = total_mass
        self.current_crew_required = total_crew
        
        # Update display labels
        self.query_one("#cost_display", Label).update(f"Cost: {total_cost:,}")
        self.query_one("#mass_display", Label).update(f"Mass: {total_mass:.1f} tons")
        self.query_one("#crew_display", Label).update(f"Crew: {total_crew}")
        
        # Validate design
        self._validate_design(selected_components)
        
        # Update progress bar (example: based on design completeness)
        progress = min(100, len(self.selected_components) * 10)
        self.query_one("#design_progress", ProgressBar).update(progress=progress)
    
    def _validate_design(self, components: List[ShipComponent]) -> None:
        """Validate the current design and update validation display."""
        if not components:
            self.design_valid = True
            self.validation_errors = []
            self.validation_warnings = []
            self._update_validation_display()
            return
        
        # Get ship type for validation context
        ship_type = self.query_one("#ship_type", Select).value
        
        # Use component manager validation
        validation = self.component_manager._validate_ship_design(components, ship_type)
        
        self.design_valid = validation["valid"]
        self.validation_errors = validation["errors"]
        self.validation_warnings = validation["warnings"]
        
        self._update_validation_display()
    
    def _update_validation_display(self) -> None:
        """Update the validation status display."""
        status_label = self.query_one("#validation_status", Label)
        messages_list = self.query_one("#validation_messages", ListView)
        
        if self.design_valid:
            status_label.update("✓ Design Valid")
            status_label.remove_class("error")
            status_label.add_class("success")
        else:
            status_label.update("✗ Design Invalid")
            status_label.remove_class("success")
            status_label.add_class("error")
        
        # Clear and repopulate messages
        messages_list.clear()
        
        for error in self.validation_errors:
            messages_list.append(ListItem(Label(f"❌ {error}", classes="error")))
        
        for warning in self.validation_warnings:
            messages_list.append(ListItem(Label(f"⚠️  {warning}", classes="warning")))
        
        if not self.validation_errors and not self.validation_warnings:
            messages_list.append(ListItem(Label("No issues found", classes="success")))
    
    def _refresh_saved_designs(self) -> None:
        """Refresh the saved designs table."""
        table = self.query_one("#saved_designs", DataTable)
        table.clear()
        
        for design_id, design in self.component_manager.designs.items():
            table.add_row(
                design.name,
                design.ship_type.value.title(),
                str(design.total_cost),
                f"{design.total_mass:.1f}",
                key=design_id
            )
    
    def set_empire(self, empire: Empire) -> None:
        """Set the current empire and refresh available components."""
        self.empire = empire
        self._refresh_components()
        self._refresh_saved_designs()
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in data tables."""
        if event.data_table.id == "component_table":
            # Add component to design
            comp_id = event.row_key.value if hasattr(event.row_key, 'value') else str(event.row_key)
            self.selected_components.append(comp_id)
            self._update_selected_table()
            self._update_design_stats()
        
        elif event.data_table.id == "selected_table":
            # Remove one instance of selected component
            comp_id = event.row_key.value if hasattr(event.row_key, 'value') else str(event.row_key)
            if comp_id in self.selected_components:
                self.selected_components.remove(comp_id)
                self._update_selected_table()
                self._update_design_stats()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select widget changes."""
        if event.select.id == "component_filter":
            self.component_filter = event.value
            self._refresh_components()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes for real-time validation."""
        if event.input.id == "design_name":
            # Real-time name validation happens automatically via validator
            pass
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "refresh_components":
            self._refresh_components()
        
        elif button_id == "remove_component":
            # Remove selected component from design
            selected_table = self.query_one("#selected_table", DataTable)
            if selected_table.cursor_row >= 0:
                row_key = selected_table.get_row_at(selected_table.cursor_row)[0]  # Get component name
                # Find and remove one instance
                for i, comp_id in enumerate(self.selected_components):
                    comp = self.component_manager.get_component(comp_id)
                    if comp and comp.name == row_key:
                        self.selected_components.pop(i)
                        break
                self._update_selected_table()
                self._update_design_stats()
        
        elif button_id == "clear_design":
            self.selected_components.clear()
            self._update_selected_table()
            self._update_design_stats()
        
        elif button_id == "save_design":
            self._save_current_design()
        
        elif button_id == "load_design":
            self._load_selected_design()
        
        elif button_id == "delete_design":
            self._delete_selected_design()
        
        elif button_id == "build_ship":
            self._build_ship_from_design()
        
        elif button_id == "export_design":
            self._export_design()
        
        elif button_id == "reset_panel":
            self._reset_panel()
    
    def _save_current_design(self) -> None:
        """Save the current design."""
        design_name = self.query_one("#design_name", Input).value.strip()
        ship_type = self.query_one("#ship_type", Select).value
        
        if not design_name:
            self.notify("Please enter a design name", severity="error")
            return
        
        if not self.selected_components:
            self.notify("Cannot save empty design", severity="error")
            return
        
        if not self.design_valid:
            self.notify("Cannot save invalid design", severity="error")
            return
        
        # Create unique design ID
        design_id = f"design_{len(self.component_manager.designs)}_{design_name.replace(' ', '_').lower()}"
        
        design = self.component_manager.create_ship_design(
            design_id,
            design_name,
            ship_type,
            self.selected_components
        )
        
        if design:
            if self.empire:
                self.empire.ship_designs.append(design.id)
            self._refresh_saved_designs()
            self.notify(f"Design '{design_name}' saved successfully!", severity="information")
        else:
            self.notify("Failed to save design", severity="error")
    
    def _load_selected_design(self) -> None:
        """Load a selected design from the saved designs table."""
        table = self.query_one("#saved_designs", DataTable)
        if table.cursor_row >= 0:
            design_id = list(table.rows.keys())[table.cursor_row]
            design = self.component_manager.get_ship_design(str(design_id))
            
            if design:
                # Load design into editor
                self.query_one("#design_name", Input).value = design.name
                self.query_one("#ship_type", Select).value = design.ship_type
                self.selected_components = design.components.copy()
                
                self._update_selected_table()
                self._update_design_stats()
                
                self.notify(f"Design '{design.name}' loaded", severity="information")
        else:
            self.notify("Please select a design to load", severity="warning")
    
    def _delete_selected_design(self) -> None:
        """Delete the selected design."""
        table = self.query_one("#saved_designs", DataTable)
        if table.cursor_row >= 0:
            design_id = list(table.rows.keys())[table.cursor_row]
            design = self.component_manager.get_ship_design(str(design_id))
            
            if design:
                # Remove from component manager
                if str(design_id) in self.component_manager.designs:
                    del self.component_manager.designs[str(design_id)]
                
                # Remove from empire if applicable
                if self.empire and design.id in self.empire.ship_designs:
                    self.empire.ship_designs.remove(design.id)
                
                self._refresh_saved_designs()
                self.notify(f"Design '{design.name}' deleted", severity="information")
        else:
            self.notify("Please select a design to delete", severity="warning")
    
    def _build_ship_from_design(self) -> None:
        """Build a ship from the current design."""
        if not self.empire:
            self.notify("No empire selected", severity="error")
            return
        
        design_name = self.query_one("#design_name", Input).value.strip()
        if not design_name:
            self.notify("Please enter a design name first", severity="error")
            return
        
        if not self.design_valid:
            self.notify("Cannot build ship from invalid design", severity="error")
            return
        
        # This would integrate with the shipbuilding system
        construction_time = 0
        if self.current_design:
            construction_time = self.component_manager.calculate_construction_time(
                self.current_design
            )
        
        self.notify(
            f"Ship construction would take {construction_time/3600:.1f} hours",
            severity="information"
        )
    
    def _export_design(self) -> None:
        """Export the current design (placeholder for future implementation)."""
        design_name = self.query_one("#design_name", Input).value.strip()
        if not design_name:
            self.notify("Please enter a design name first", severity="warning")
            return
        
        self.notify(f"Design '{design_name}' export feature coming soon!", severity="information")
    
    def _reset_panel(self) -> None:
        """Reset the entire panel to initial state."""
        self.selected_components.clear()
        self.query_one("#design_name", Input).value = ""
        self.query_one("#ship_type", Select).value = ShipType.FRIGATE
        self.query_one("#component_filter", Select).value = "all"
        self.component_filter = "all"
        
        self._update_selected_table()
        self._update_design_stats()
        self._refresh_components()
        
        self.notify("Panel reset", severity="information")
    
    class DesignCreated(Message):
        """Message sent when a design is created."""
        
        def __init__(self, design: ShipDesign) -> None:
            self.design = design
            super().__init__()
    
    class ShipBuildRequested(Message):
        """Message sent when ship construction is requested."""
        
        def __init__(self, design: ShipDesign, empire: Empire) -> None:
            self.design = design
            self.empire = empire
            super().__init__()


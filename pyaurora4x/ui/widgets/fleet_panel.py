"""
Fleet Panel Widget for PyAurora 4X

Displays fleet information, status, and allows fleet management.
"""

from typing import List, Optional
from textual.widgets import Static, DataTable, Button, Label
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive

from pyaurora4x.core.models import Fleet, Ship
from pyaurora4x.core.enums import FleetStatus
from pyaurora4x.core.utils import format_distance, format_time


class FleetPanel(Static):
    """
    Widget for displaying and managing fleets.
    
    Shows fleet list, detailed information, and provides
    basic fleet management controls.
    """
    
    fleets = reactive([])
    selected_fleet = reactive(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fleet_list: List[Fleet] = []
        self.current_fleet: Optional[Fleet] = None
    
    def compose(self) -> ComposeResult:
        """Compose the fleet panel layout."""
        with Container(id="fleet_container"):
            with Horizontal():
                # Left side - fleet list
                with Vertical(id="fleet_list_panel", classes="panel-section"):
                    yield Label("Fleets", classes="panel-title")
                    yield DataTable(id="fleet_table", cursor_type="row")
                
                # Right side - fleet details
                with Vertical(id="fleet_details_panel", classes="panel-section"):
                    yield Label("Fleet Details", classes="panel-title")
                    yield Static("", id="fleet_info", classes="info-display")
                    
                    # Fleet controls
                    with Horizontal(id="fleet_controls"):
                        yield Button("Move", id="move_fleet", variant="primary")
                        yield Button("Orbit", id="orbit_fleet")
                        yield Button("Survey", id="survey_fleet")
                        yield Button("Stop", id="stop_fleet", variant="error")
    
    def on_mount(self) -> None:
        """Initialize the fleet panel."""
        self._setup_fleet_table()
        self._update_display()
    
    def _setup_fleet_table(self) -> None:
        """Set up the fleet data table."""
        table = self.query_one("#fleet_table", DataTable)
        table.add_columns("Name", "Status", "Ships", "Location", "Fuel")
        table.cursor_type = "row"
    
    def update_fleets(self, fleets: List[Fleet]) -> None:
        """
        Update the fleet list.
        
        Args:
            fleets: List of fleets to display
        """
        self.fleet_list = [f for f in fleets if f is not None]
        self._refresh_fleet_table()
        
        # Select first fleet if none selected
        if self.fleet_list and not self.current_fleet:
            self.current_fleet = self.fleet_list[0]
            self._update_fleet_details()
    
    def _refresh_fleet_table(self) -> None:
        """Refresh the fleet table with current data."""
        table = self.query_one("#fleet_table", DataTable)
        table.clear()
        
        for fleet in self.fleet_list:
            # Format fleet data for display
            name = fleet.name
            status = self._format_fleet_status(fleet.status)
            ship_count = str(len(fleet.ships))
            location = self._format_fleet_location(fleet)
            fuel = f"{fleet.fuel_remaining:.0f}%"
            
            table.add_row(name, status, ship_count, location, fuel, key=fleet.id)
    
    def _format_fleet_status(self, status: FleetStatus) -> str:
        """Format fleet status for display."""
        status_str = status.value if hasattr(status, 'value') else str(status)
        status_symbols = {
            'idle': '⏸️',
            'moving': '🚀',
            'in_transit': '🌌',
            'orbiting': '🔄',
            'surveying': '🔍',
            'mining': '⛏️',
            'exploring': '🗺️',
            'in_combat': '⚔️',
            'repairing': '🔧',
            'refueling': '⛽'
        }
        
        symbol = status_symbols.get(status_str, '❓')
        return f"{symbol} {status_str.title()}"
    
    def _format_fleet_location(self, fleet: Fleet) -> str:
        """Format fleet location for display."""
        if not fleet.position:
            return "Unknown"
        
        # Calculate distance from system center
        distance = (fleet.position.x**2 + fleet.position.y**2 + fleet.position.z**2)**0.5
        return format_distance(distance)
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle fleet selection in the table."""
        if event.data_table.id == "fleet_table":
            fleet_id = event.row_key
            self.current_fleet = next((f for f in self.fleet_list if f.id == fleet_id), None)
            self._update_fleet_details()
    
    def _update_fleet_details(self) -> None:
        """Update the fleet details display."""
        if not self.current_fleet:
            self._show_no_fleet_selected()
            return
        
        fleet = self.current_fleet
        details = self._generate_fleet_details(fleet)
        
        info_widget = self.query_one("#fleet_info", Static)
        info_widget.update(details)
        
        # Update button states
        self._update_fleet_controls()
    
    def _generate_fleet_details(self, fleet: Fleet) -> str:
        """Generate detailed fleet information text."""
        lines = []
        
        # Basic fleet info
        lines.append(f"Fleet: {fleet.name}")
        lines.append(f"Empire: {fleet.empire_id}")
        lines.append("")
        
        # Status and location
        status = fleet.status.value if hasattr(fleet.status, 'value') else str(fleet.status)
        lines.append(f"Status: {status.title()}")
        lines.append(f"System: {fleet.system_id}")
        
        if fleet.position:
            lines.append(f"Position: ({fleet.position.x:.0f}, {fleet.position.y:.0f}, {fleet.position.z:.0f}) km")
        
        if fleet.velocity and fleet.velocity.magnitude() > 0:
            speed = fleet.velocity.magnitude()
            lines.append(f"Speed: {speed:.1f} km/s")
        
        lines.append("")
        
        # Fleet composition
        lines.append(f"Ships: {len(fleet.ships)}")
        lines.append(f"Total Mass: {fleet.total_mass:.0f} tons")
        lines.append(f"Max Speed: {fleet.max_speed:.1f} km/s")
        lines.append(f"Fuel: {fleet.fuel_remaining:.1f}%")
        
        # Current orders
        if fleet.current_orders:
            lines.append("")
            lines.append("Current Orders:")
            for i, order in enumerate(fleet.current_orders[:3]):  # Show first 3 orders
                lines.append(f"  {i+1}. {order}")
            if len(fleet.current_orders) > 3:
                lines.append(f"  ... and {len(fleet.current_orders) - 3} more")
        
        # Destination and ETA
        if fleet.destination and fleet.estimated_arrival:
            lines.append("")
            lines.append("Navigation:")
            lines.append(f"Destination: ({fleet.destination.x:.0f}, {fleet.destination.y:.0f}, {fleet.destination.z:.0f})")
            lines.append(f"ETA: {format_time(fleet.estimated_arrival)}")
        
        return '\n'.join(lines)
    
    def _show_no_fleet_selected(self) -> None:
        """Show message when no fleet is selected."""
        info_widget = self.query_one("#fleet_info", Static)
        info_widget.update("Select a fleet from the list to view details.")
    
    def _update_fleet_controls(self) -> None:
        """Update the state of fleet control buttons."""
        if not self.current_fleet:
            # Disable all buttons if no fleet selected
            for button_id in ["move_fleet", "orbit_fleet", "survey_fleet", "stop_fleet"]:
                try:
                    button = self.query_one(f"#{button_id}", Button)
                    button.disabled = True
                except:
                    pass
            return
        
        # Enable buttons based on fleet status
        fleet = self.current_fleet
        status = fleet.status.value if hasattr(fleet.status, 'value') else str(fleet.status)
        
        try:
            move_btn = self.query_one("#move_fleet", Button)
            orbit_btn = self.query_one("#orbit_fleet", Button)
            survey_btn = self.query_one("#survey_fleet", Button)
            stop_btn = self.query_one("#stop_fleet", Button)
            
            # Basic logic for button states
            move_btn.disabled = status in ['moving', 'in_transit']
            orbit_btn.disabled = status in ['orbiting', 'moving', 'in_transit']
            survey_btn.disabled = status in ['surveying', 'moving', 'in_transit']
            stop_btn.disabled = status in ['idle']
            
        except:
            pass  # Buttons might not be ready yet
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle fleet control button presses."""
        if not self.current_fleet:
            return
        
        button_id = event.button.id
        fleet = self.current_fleet
        
        if button_id == "move_fleet":
            self._handle_move_fleet(fleet)
        elif button_id == "orbit_fleet":
            self._handle_orbit_fleet(fleet)
        elif button_id == "survey_fleet":
            self._handle_survey_fleet(fleet)
        elif button_id == "stop_fleet":
            self._handle_stop_fleet(fleet)
    
    def _handle_move_fleet(self, fleet: Fleet) -> None:
        """Handle move fleet command."""
        # In a full implementation, this would open a destination selection dialog
        # For now, just add a placeholder order
        fleet.current_orders.append("Move to destination (not implemented)")
        fleet.status = FleetStatus.MOVING
        self._update_fleet_details()
        self.post_message_no_wait(FleetCommandEvent("move", fleet.id))
    
    def _handle_orbit_fleet(self, fleet: Fleet) -> None:
        """Handle orbit fleet command."""
        fleet.current_orders.append("Orbit current location")
        fleet.status = FleetStatus.ORBITING
        self._update_fleet_details()
        self.post_message_no_wait(FleetCommandEvent("orbit", fleet.id))
    
    def _handle_survey_fleet(self, fleet: Fleet) -> None:
        """Handle survey fleet command."""
        fleet.current_orders.append("Survey system")
        fleet.status = FleetStatus.SURVEYING
        self._update_fleet_details()
        self.post_message_no_wait(FleetCommandEvent("survey", fleet.id))
    
    def _handle_stop_fleet(self, fleet: Fleet) -> None:
        """Handle stop fleet command."""
        fleet.current_orders.clear()
        fleet.status = FleetStatus.IDLE
        fleet.destination = None
        fleet.estimated_arrival = None
        self._update_fleet_details()
        self.post_message_no_wait(FleetCommandEvent("stop", fleet.id))
    
    def _update_display(self) -> None:
        """Update the entire display."""
        if not self.fleet_list:
            info_widget = self.query_one("#fleet_info", Static)
            info_widget.update("No fleets available.")
        else:
            self._refresh_fleet_table()
            if self.current_fleet:
                self._update_fleet_details()

    def refresh(self) -> None:
        """Refresh fleet information."""
        self._update_display()


class FleetCommandEvent:
    """Event for fleet commands."""
    
    def __init__(self, command: str, fleet_id: str):
        self.command = command
        self.fleet_id = fleet_id


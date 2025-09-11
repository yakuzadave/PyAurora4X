"""
Jump Travel Panel Widget for PyAurora 4X

Provides UI for jump point travel, exploration missions, and jump point management.
"""

from typing import List, Optional, Dict, Any
from textual.widgets import Static, DataTable, Button, Label, Select, ProgressBar
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, Grid
from textual.reactive import reactive
from textual.message import Message

from pyaurora4x.core.models import Fleet, StarSystem
from pyaurora4x.core.utils import format_distance, format_time


class JumpPointSelected(Message):
    """Message sent when a jump point is selected."""
    
    def __init__(self, jump_point_id: str, jump_point_name: str) -> None:
        super().__init__()
        self.jump_point_id = jump_point_id
        self.jump_point_name = jump_point_name


class JumpTravelPanel(Static):
    """
    Widget for managing jump point travel and exploration.
    
    Provides interface for:
    - Viewing available jump points
    - Initiating jump travel
    - Starting exploration missions
    - Surveying jump points
    - Viewing jump/exploration status
    """
    
    current_fleet = reactive(None)
    available_jumps = reactive([])
    jump_status = reactive(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fleet: Optional[Fleet] = None
        self.current_system: Optional[StarSystem] = None
        self.simulation = None
    
    def compose(self) -> ComposeResult:
        """Compose the jump travel panel layout."""
        with Container(id="jump_travel_container"):
            with Vertical():
                yield Label("Jump Point Travel & Exploration", classes="panel-title")
                
                # Jump point information section
                with Container(id="jump_info_section", classes="panel-section"):
                    yield Label("Available Jump Points", classes="section-title")
                    yield DataTable(id="jump_points_table", cursor_type="row")
                    
                    with Horizontal(id="jump_controls"):
                        yield Button("Jump", id="initiate_jump", variant="primary", disabled=True)
                        yield Button("Survey", id="survey_jump_point", variant="default", disabled=True)
                        yield Button("Cancel", id="cancel_jump", variant="error", disabled=True)
                
                # Exploration section
                with Container(id="exploration_section", classes="panel-section"):
                    yield Label("Exploration", classes="section-title")
                    with Horizontal(id="exploration_controls"):
                        yield Button("Explore System", id="start_exploration", variant="success")
                        yield Button("Deep Survey", id="start_deep_survey", variant="default")
                
                # Status section
                with Container(id="status_section", classes="panel-section"):
                    yield Label("Current Operations", classes="section-title")
                    yield Static("", id="operation_status")
                    yield ProgressBar(id="operation_progress", show_eta=True)
                    
                # System information
                with Container(id="system_info_section", classes="panel-section"):
                    yield Label("System Information", classes="section-title")
                    yield Static("", id="system_exploration_info")
    
    def on_mount(self) -> None:
        """Initialize the jump travel panel."""
        self._setup_jump_points_table()
        self._update_display()
    
    def _setup_jump_points_table(self) -> None:
        """Set up the jump points data table."""
        table = self.query_one("#jump_points_table", DataTable)
        table.add_columns(
            "Name", "Target", "Status", "Fuel Cost", "Travel Time", "Difficulty"
        )
        table.cursor_type = "row"
    
    def update_fleet_data(self, fleet: Fleet, system: StarSystem, simulation) -> None:
        """Update the panel with new fleet and system data."""
        self.fleet = fleet
        self.current_system = system
        self.simulation = simulation
        self._update_display()
    
    def _update_display(self) -> None:
        """Update the entire display with current data."""
        if not self.fleet or not self.current_system or not self.simulation:
            self._show_no_data()
            return
        
        # Update available jumps
        self._refresh_jump_points_table()
        
        # Update operation status
        self._update_operation_status()
        
        # Update system exploration info
        self._update_system_info()
        
        # Update button states
        self._update_button_states()
    
    def _show_no_data(self) -> None:
        """Show message when no data is available."""
        table = self.query_one("#jump_points_table", DataTable)
        table.clear()
        
        status_widget = self.query_one("#operation_status", Static)
        status_widget.update("Select a fleet to view jump travel options.")
        
        system_info = self.query_one("#system_exploration_info", Static)
        system_info.update("No system data available.")
    
    def _refresh_jump_points_table(self) -> None:
        """Refresh the jump points table with current data."""
        if not self.fleet or not self.simulation:
            return
        
        table = self.query_one("#jump_points_table", DataTable)
        table.clear()
        
        # Get available jumps
        available_jumps = self.simulation.get_available_jumps(self.fleet.id)
        
        for jump_info in available_jumps:
            name = jump_info.get("jump_point_name", "Unknown")
            target = jump_info.get("target_system_name", jump_info.get("target_system_id", "Unknown"))
            status = "✅ Ready" if jump_info.get("can_jump") else "❌ Blocked"
            fuel_cost = f"{jump_info.get('fuel_cost', 0):.1f}"
            travel_time = format_time(jump_info.get("travel_time", 0))
            
            # Determine difficulty indicator
            stability = jump_info.get("stability", 1.0)
            if stability >= 0.9:
                difficulty = "🟢 Stable"
            elif stability >= 0.7:
                difficulty = "🟡 Moderate"
            else:
                difficulty = "🔴 Unstable"
            
            # Add failure reasons if any
            failure_reasons = jump_info.get("failure_reasons", [])
            if failure_reasons:
                status = f"❌ {failure_reasons[0]}"
            
            table.add_row(
                name, target, status, fuel_cost, travel_time, difficulty,
                key=jump_info.get("jump_point_id", "")
            )
    
    def _update_operation_status(self) -> None:
        """Update the operation status display."""
        if not self.fleet or not self.simulation:
            return
        
        status_widget = self.query_one("#operation_status", Static)
        progress_bar = self.query_one("#operation_progress", ProgressBar)
        
        # Check for active jump operations
        jump_status = self.simulation.get_fleet_jump_status(self.fleet.id)
        
        if jump_status.get("has_operation"):
            operation_type = jump_status.get("operation_type", "unknown")
            progress = jump_status.get("progress", 0.0)
            remaining_time = jump_status.get("remaining_time", 0.0)
            details = jump_status.get("details", {})
            
            if operation_type == "preparation":
                target_system = details.get("target_system", "Unknown")
                fuel_cost = details.get("fuel_cost", 0.0)
                status_text = f"Preparing jump to {target_system} (Fuel: {fuel_cost:.1f})"
            elif operation_type == "jump":
                origin = details.get("origin_system", "Unknown")
                target = details.get("target_system", "Unknown")
                status_text = f"Jumping from {origin} to {target}"
            else:
                status_text = f"Active operation: {operation_type}"
            
            status_widget.update(f"{status_text} - ETA: {format_time(remaining_time)}")
            progress_bar.update(progress=progress * 100)
            progress_bar.display = True
            
        else:
            # Check for exploration missions
            if self.fleet.status.value in ["exploring", "surveying"]:
                status_widget.update(f"Fleet is {self.fleet.status.value}")
                progress_bar.display = False
            else:
                status_widget.update("No active operations")
                progress_bar.display = False
    
    def _update_system_info(self) -> None:
        """Update system exploration information."""
        if not self.current_system or not self.simulation or not self.fleet:
            return
        
        system_info = self.query_one("#system_exploration_info", Static)
        
        exploration_status = self.simulation.get_system_exploration_status(
            self.current_system.id, self.fleet.empire_id
        )
        
        lines = []
        lines.append(f"System: {self.current_system.name}")
        lines.append(f"Exploration Progress: {exploration_status.get('exploration_progress', 0.0) * 100:.1f}%")
        lines.append(f"Survey Completeness: {exploration_status.get('survey_completeness', 0.0) * 100:.1f}%")
        lines.append(f"Known Jump Points: {exploration_status.get('discovered_jump_points', 0)}")
        
        difficulty = exploration_status.get("system_difficulty", 1.0)
        lines.append(f"Exploration Difficulty: {difficulty:.1f}x")
        
        potential_discoveries = exploration_status.get("potential_discoveries", 0)
        if potential_discoveries > 0:
            lines.append(f"Potential Hidden Points: {potential_discoveries}")
        
        system_info.update("\\n".join(lines))
    
    def _update_button_states(self) -> None:
        """Update the state of control buttons."""
        if not self.fleet:
            # Disable all buttons if no fleet selected
            for button_id in ["initiate_jump", "survey_jump_point", "cancel_jump", 
                             "start_exploration", "start_deep_survey"]:
                try:
                    button = self.query_one(f"#{button_id}", Button)
                    button.disabled = True
                except Exception:
                    pass
            return
        
        # Check jump status
        jump_status = self.simulation.get_fleet_jump_status(self.fleet.id) if self.simulation else {}
        has_active_operation = jump_status.get("has_operation", False)
        
        # Check if any jump point is selected
        table = self.query_one("#jump_points_table", DataTable)
        has_selection = table.cursor_coordinate is not None
        
        try:
            # Jump controls
            jump_btn = self.query_one("#initiate_jump", Button)
            survey_btn = self.query_one("#survey_jump_point", Button)
            cancel_btn = self.query_one("#cancel_jump", Button)
            
            # Exploration controls  
            explore_btn = self.query_one("#start_exploration", Button)
            deep_survey_btn = self.query_one("#start_deep_survey", Button)
            
            # Enable/disable based on state
            fleet_busy = self.fleet.status.value in ["exploring", "surveying", "forming_up", "in_transit"]
            
            jump_btn.disabled = not has_selection or has_active_operation or fleet_busy
            survey_btn.disabled = not has_selection or has_active_operation or fleet_busy
            cancel_btn.disabled = not has_active_operation
            explore_btn.disabled = has_active_operation or fleet_busy
            deep_survey_btn.disabled = has_active_operation or fleet_busy
            
        except Exception:
            pass  # Buttons might not be ready yet
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle jump point selection in the table."""
        if event.data_table.id == "jump_points_table":
            self._update_button_states()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if not self.fleet or not self.simulation:
            return
        
        button_id = event.button.id
        
        if button_id == "initiate_jump":
            self._handle_initiate_jump()
        elif button_id == "survey_jump_point":
            self._handle_survey_jump_point()
        elif button_id == "cancel_jump":
            self._handle_cancel_jump()
        elif button_id == "start_exploration":
            self._handle_start_exploration()
        elif button_id == "start_deep_survey":
            self._handle_start_deep_survey()
    
    def _handle_initiate_jump(self) -> None:
        """Handle jump initiation."""
        table = self.query_one("#jump_points_table", DataTable)
        if table.cursor_coordinate is None:
            return
        
        jump_point_id = table.get_row_at(table.cursor_coordinate.row)[0]  # Get row key
        if not jump_point_id:
            return
        
        success, message = self.simulation.initiate_fleet_jump(self.fleet.id, jump_point_id)
        
        # TODO: Show message to user (would need message system)
        # For now, just update the display
        self._update_display()
    
    def _handle_survey_jump_point(self) -> None:
        """Handle jump point survey."""
        table = self.query_one("#jump_points_table", DataTable)
        if table.cursor_coordinate is None:
            return
        
        jump_point_id = table.get_row_at(table.cursor_coordinate.row)[0]  # Get row key
        if not jump_point_id:
            return
        
        success, message = self.simulation.survey_jump_point(self.fleet.id, jump_point_id)
        self._update_display()
    
    def _handle_cancel_jump(self) -> None:
        """Handle jump cancellation."""
        success, message = self.simulation.cancel_fleet_jump(self.fleet.id)
        self._update_display()
    
    def _handle_start_exploration(self) -> None:
        """Handle exploration mission start."""
        success, message = self.simulation.start_fleet_exploration(self.fleet.id, "explore")
        self._update_display()
    
    def _handle_start_deep_survey(self) -> None:
        """Handle deep survey mission start."""
        success, message = self.simulation.start_fleet_exploration(self.fleet.id, "deep_scan")
        self._update_display()
    
    def refresh_data(self) -> None:
        """Refresh the panel data."""
        self._update_display()


class JumpNetworkMap(Static):
    """
    Widget for displaying the jump point network map.
    Shows known systems and their connections.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.empire_id: Optional[str] = None
        self.simulation = None
    
    def compose(self) -> ComposeResult:
        """Compose the network map layout."""
        with Container(id="jump_network_container"):
            with Vertical():
                yield Label("Jump Point Network", classes="panel-title")
                yield Static("", id="network_display", classes="network-map")
                
                with Horizontal(id="network_controls"):
                    yield Button("Refresh", id="refresh_network", variant="default")
                    yield Button("Center on Fleet", id="center_fleet", variant="primary")
    
    def update_network_data(self, empire_id: str, simulation) -> None:
        """Update the network display with empire data."""
        self.empire_id = empire_id
        self.simulation = simulation
        self._update_network_display()
    
    def _update_network_display(self) -> None:
        """Update the network map display."""
        if not self.empire_id or not self.simulation:
            return
        
        network_display = self.query_one("#network_display", Static)
        
        try:
            network_data = self.simulation.get_empire_jump_network(self.empire_id)
            
            lines = []
            lines.append("Known Systems and Connections:")
            lines.append("")
            
            for system_id in network_data.get("known_systems", []):
                connections = network_data.get("system_connections", {}).get(system_id, [])
                if connections:
                    lines.append(f"📍 {system_id}:")
                    for conn in connections:
                        target = conn.get("target_system_id", "Unknown")
                        jp_name = conn.get("jump_point_name", "Unknown")
                        status = conn.get("status", "unknown")
                        lines.append(f"  └─ {jp_name} → {target} ({status})")
                else:
                    lines.append(f"📍 {system_id}: No known connections")
                lines.append("")
            
            # Statistics
            stats = network_data.get("statistics", {})
            lines.append("Statistics:")
            lines.append(f"  Total Jumps: {stats.get('total_jumps', 0)}")
            lines.append(f"  Exploration Missions: {stats.get('exploration_missions', 0)}")
            lines.append(f"  Discovered Jump Points: {stats.get('discovered_jump_points', 0)}")
            
            network_display.update("\\n".join(lines))
            
        except Exception as e:
            network_display.update(f"Error loading network data: {str(e)}")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "refresh_network":
            self._update_network_display()
        elif event.button.id == "center_fleet":
            # TODO: Center map on current fleet position
            pass

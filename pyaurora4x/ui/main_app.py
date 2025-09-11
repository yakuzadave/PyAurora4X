"""
Main Textual application for PyAurora 4X

Provides the terminal-based user interface for the game.
"""

from typing import Optional, Dict, Any
import logging

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header, Footer, Button, Static, Log, Label
)
from textual.binding import Binding
from textual import events

from pyaurora4x.engine.simulation import GameSimulation
from pyaurora4x.ui.widgets.star_system_view import StarSystemView
from pyaurora4x.ui.widgets.fleet_panel import FleetPanel
from pyaurora4x.ui.widgets.research_panel import ResearchPanel
from pyaurora4x.ui.widgets.empire_stats import EmpireStatsWidget
from pyaurora4x.ui.widgets.load_dialog import LoadGameDialog
from pyaurora4x.ui.widgets.ship_design_panel import ShipDesignPanel
from pyaurora4x.ui.widgets.colony_management_panel import ColonyManagementPanel
from pyaurora4x.data.save_manager import SaveManager
from pyaurora4x.data.ship_components import ShipComponentManager

logger = logging.getLogger(__name__)


class TimeControlWidget(Static):
    """Widget for controlling time advancement."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_paused = True
        self.time_scale = 1.0
    
    def compose(self) -> ComposeResult:
        with Horizontal(classes="time-controls"):
            yield Button("⏸️ Pause", id="pause_btn", variant="primary")
            yield Button("⏩ 5s", id="time_5s")
            yield Button("⏩ 30s", id="time_30s") 
            yield Button("⏩ 1m", id="time_1m")
            yield Button("⏩ 1y", id="time_1y")
            yield Label("Paused", id="time_status")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle time control button presses."""
        button_id = event.button.id
        
        if button_id == "pause_btn":
            self.toggle_pause()
        elif button_id == "time_5s":
            self.advance_time(5)
        elif button_id == "time_30s":
            self.advance_time(30)
        elif button_id == "time_1m":
            self.advance_time(60)
        elif button_id == "time_1y":
            self.advance_time(365.25 * 24 * 3600)
    
    def toggle_pause(self) -> None:
        """Toggle pause state."""
        self.is_paused = not self.is_paused
        pause_btn = self.query_one("#pause_btn", Button)
        status_label = self.query_one("#time_status", Label)
        
        if self.is_paused:
            pause_btn.label = "▶️ Resume"
            status_label.update("Paused")
            self.post_message_no_wait(TimeControlEvent("pause"))
        else:
            pause_btn.label = "⏸️ Pause"
            status_label.update("Running")
            self.post_message_no_wait(TimeControlEvent("resume"))
    
    def advance_time(self, seconds: float) -> None:
        """Advance time by specified seconds."""
        self.post_message_no_wait(TimeControlEvent("advance", seconds))
    
    def update_status(self, game_time: float, is_paused: bool) -> None:
        """Update the time status display."""
        status_label = self.query_one("#time_status", Label)
        
        if is_paused:
            status_label.update("Paused")
        else:
            # Format game time nicely
            if game_time < 60:
                time_str = f"{game_time:.1f}s"
            elif game_time < 3600:
                time_str = f"{game_time/60:.1f}m"
            elif game_time < 86400:
                time_str = f"{game_time/3600:.1f}h"
            else:
                time_str = f"{game_time/86400:.1f}d"
            
            status_label.update(f"Time: {time_str}")


class TimeControlEvent:
    """Custom event for time control actions."""
    
    def __init__(self, action: str, value: Optional[float] = None):
        self.action = action
        self.value = value


class PyAurora4XApp(App):
    """
    Main Textual application for PyAurora 4X.
    
    Provides the terminal-based user interface with multiple panels
    for game information and controls.
    """
    
    CSS = """
    .panel {
        border: solid $primary;
        margin: 1;
    }
    
    .hidden {
        display: none;
    }
    
    #main_container {
        height: 100%;
    }
    
    #top_row {
        height: 80%;
    }
    
    #main_view {
        width: 70%;
    }
    
    #side_panel {
        width: 30%;
    }
    
    #bottom_panel {
        height: 20%;
    }
    
    .time-controls {
        padding: 1;
        border: solid $accent;
    }

    Button {
        margin: 0 1;
    }

    #load_dialog {
        align: center middle;
        padding: 2;
        border: solid $accent;
        background: $panel;
    }
    
    /* Ship Design Panel Styles */
    #design_container {
        padding: 1;
    }
    
    #design_header {
        height: auto;
        padding: 1;
        border: solid $primary;
        margin-bottom: 1;
    }
    
    .title {
        color: $accent;
        text-style: bold;
    }
    
    .subtitle {
        color: $primary;
        text-style: bold;
    }
    
    .label {
        width: auto;
        min-width: 12;
    }
    
    #main_content {
        height: 1fr;
    }
    
    #components_panel {
        width: 35%;
        margin-right: 1;
    }
    
    #design_panel {
        width: 35%;
        margin-right: 1;
    }
    
    #validation_panel {
        width: 30%;
    }
    
    #design_actions {
        height: auto;
        padding: 1;
        margin-top: 1;
    }
    
    .success {
        color: $success;
    }
    
    .error {
        color: $error;
    }
    
    .warning {
        color: $warning;
    }
    
    DataTable {
        height: 1fr;
        margin: 1 0;
    }
    
    Input {
        margin: 0 1;
    }
    
    Select {
        margin: 0 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "save_game", "Save Game"),
        Binding("l", "load_game", "Load Game"),
        Binding("space", "toggle_pause", "Pause/Resume"),
        Binding("1", "show_systems", "Systems"),
        Binding("2", "show_fleets", "Fleets"),
        Binding("3", "show_research", "Research"),
        Binding("4", "show_ship_design", "Ship Design"),
        Binding("5", "show_colonies", "Colonies"),
        Binding("f1", "focus_fleet_1", "Fleet 1"),
        Binding("f2", "focus_fleet_2", "Fleet 2"),
        Binding("f3", "focus_fleet_3", "Fleet 3"),
        Binding("f4", "focus_fleet_4", "Fleet 4"),
        Binding("f5", "focus_fleet_5", "Fleet 5"),
        Binding("h", "show_help", "Help"),
    ]
    
    def __init__(self, new_game_systems: int = 3, new_game_empires: int = 2, **kwargs):
        super().__init__(**kwargs)
        self.simulation: Optional[GameSimulation] = None
        self.save_manager = SaveManager()
        self.component_manager = ShipComponentManager()
        self.current_view = "systems"
        self.auto_save_interval = 300  # 5 minutes
        self.last_auto_save = 0
        self.load_file: Optional[str] = None
        self.load_data: Optional[Dict[str, Any]] = None
        self.new_game_systems = new_game_systems
        self.new_game_empires = new_game_empires
    
    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        yield Header(show_clock=True)
        
        with Container(id="main_container"):
            with Horizontal(id="top_row"):
                # Left panel - main view area
                with Vertical(id="main_view", classes="panel"):
                    yield StarSystemView(id="system_view")
                    yield FleetPanel(id="fleet_view", classes="hidden")
                    yield ResearchPanel(id="research_view", classes="hidden")
                    yield ShipDesignPanel(self.component_manager, id="design_view", classes="hidden")
                    yield ColonyManagementPanel(id="colony_view", classes="hidden")
                
                # Right panel - empire stats and controls  
                with Vertical(id="side_panel", classes="panel"):
                    yield EmpireStatsWidget(id="empire_stats")
                    yield TimeControlWidget(id="time_controls")
            
            # Bottom panel - messages and logs
            with Container(id="bottom_panel", classes="panel"):
                yield Log(id="message_log", max_lines=100)
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the application after mounting."""
        self.title = "PyAurora 4X - Terminal Space Strategy"
        self.sub_title = "A Python-based 4X game with realistic orbital mechanics"

        # Periodic UI refresh so widgets stay up to date
        self.set_interval(1.0, self._on_tick)

        logger.info("PyAurora 4X application started")
    
    def on_ready(self) -> None:
        """Called when the app is ready and all widgets are mounted."""
        # Handle load data if provided
        if self.load_data:
            self.load_game_data(self.load_data)
        elif self.simulation is None:
            # Start with a new game if no simulation exists
            self.start_new_game()
    
    def start_new_game(self) -> None:
        """Start a new game."""
        self.simulation = GameSimulation()
        self.simulation.initialize_new_game(
            num_systems=self.new_game_systems,
            num_empires=self.new_game_empires,
        )
        
        # Update UI components with new game data
        self._update_all_widgets()
        
        # Log initial message
        message_log = self.query_one("#message_log", Log)
        message_log.write_line("New game started! Welcome to PyAurora 4X.")
        
        logger.info("New game started")
    
    def load_game_data(self, game_data: Dict[str, Any]) -> None:
        """Load game from data."""
        self.simulation = GameSimulation()
        self.simulation.load_game_state(game_data)
        
        self._update_all_widgets()
        
        message_log = self.query_one("#message_log", Log)
        message_log.write_line("Game loaded successfully.")
        
        logger.info("Game loaded from data")
    
    def _update_all_widgets(self) -> None:
        """Update all widgets with current game state."""
        if not self.simulation:
            return
        
        # Update system view
        system_view = self.query_one("#system_view", StarSystemView)
        if self.simulation.star_systems:
            first_system = list(self.simulation.star_systems.values())[0]
            system_fleets = [f for f in self.simulation.fleets.values() if f.system_id == first_system.id]
            system_view.update_system(first_system, system_fleets)
        system_view.refresh_positions()
        
        # Update fleet panel
        fleet_panel = self.query_one("#fleet_view", FleetPanel)
        player_empire = self.simulation.get_player_empire()
        if player_empire:
            fleets = [self.simulation.get_fleet(fid) for fid in player_empire.fleets if self.simulation.get_fleet(fid) is not None]
            fleet_panel.update_fleets(fleets, self.simulation.current_time)
        fleet_panel.refresh()
        
        # Update research panel
        research_panel = self.query_one("#research_view", ResearchPanel)
        if player_empire:
            research_panel.tech_manager = self.simulation.tech_manager
            research_panel.update_empire(player_empire)
        research_panel.refresh()
        
        # Update ship design panel
        design_panel = self.query_one("#design_view", ShipDesignPanel)
        if player_empire:
            design_panel.set_empire(player_empire)
        design_panel.refresh()
        
        # Update colony management panel
        colony_panel = self.query_one("#colony_view", ColonyManagementPanel)
        if player_empire and player_empire.colonies:
            # Initialize the panel with infrastructure manager and event manager
            if not colony_panel.infrastructure_manager:
                colony_panel.infrastructure_manager = self.simulation.get_infrastructure_manager()
            if not colony_panel.event_manager:
                colony_panel.event_manager = self.simulation.event_manager
            
            # Update with first colony as default
            first_colony_id = player_empire.colonies[0]
            first_colony = self.simulation.get_colony(first_colony_id)
            if first_colony:
                colony_panel.update_colony(first_colony, player_empire)
        colony_panel.refresh()
        
        # Update empire stats
        empire_stats = self.query_one("#empire_stats", EmpireStatsWidget)
        if player_empire:
            empire_stats.event_manager = self.simulation.event_manager
            empire_stats.update_empire(
                player_empire, self.simulation.current_time
            )
        
        # Update time controls
        time_controls = self.query_one("#time_controls", TimeControlWidget)
        time_controls.update_status(
            self.simulation.current_time,
            self.simulation.is_paused
        )

    def _on_tick(self) -> None:
        """Periodic refresh callback."""
        if not self.simulation:
            return

        if not self.simulation.is_paused:
            current_time = self.simulation.current_time
            if current_time - self.last_auto_save > self.auto_save_interval:
                self.action_save_game()
                self.last_auto_save = current_time

        self._update_all_widgets()
    
    def on_time_control_event(self, event: TimeControlEvent) -> None:
        """Handle time control events."""
        if not self.simulation:
            return
        
        message_log = self.query_one("#message_log", Log)
        
        if event.action == "pause":
            self.simulation.pause()
            message_log.write_line("Game paused.")
        elif event.action == "resume":
            self.simulation.resume()
            message_log.write_line("Game resumed.")
        elif event.action == "advance" and event.value:
            self.simulation.advance_time(event.value)
            message_log.write_line(f"Advanced time by {event.value} seconds.")
            self._update_all_widgets()
    
    def action_toggle_pause(self) -> None:
        """Toggle pause via keyboard shortcut."""
        time_controls = self.query_one("#time_controls", TimeControlWidget)
        time_controls.toggle_pause()
    
    def action_save_game(self) -> None:
        """Save the current game."""
        if not self.simulation:
            return
        
        try:
            save_name = f"autosave_{int(self.simulation.current_time)}"
            self.save_manager.save_game(self.simulation.get_game_state(), save_name)
            
            message_log = self.query_one("#message_log", Log)
            message_log.write_line(f"Game saved as {save_name}")
            
            logger.info(f"Game saved: {save_name}")
        except Exception as e:
            logger.error(f"Error saving game: {e}")
    
    def action_load_game(self) -> None:
        """Show a dialog to load a saved game."""
        message_log = self.query_one("#message_log", Log)

        saves = self.save_manager.list_saves()
        if not saves:
            message_log.write_line("No saved games found.")
            return

        def _on_select(save_name: str) -> None:
            try:
                game_data = self.save_manager.load_game(save_name)
                self.load_game_data(game_data)
                message_log.write_line(f"Loaded save '{save_name}'.")
            except Exception as e:
                message_log.write_line(f"Failed to load save '{save_name}': {e}")

        dialog = LoadGameDialog(saves, _on_select)
        self.mount(dialog)
    
    def action_show_systems(self) -> None:
        """Show the star systems view."""
        self._switch_view("systems")
    
    def action_show_fleets(self) -> None:
        """Show the fleets view."""
        self._switch_view("fleets")
    
    def action_show_research(self) -> None:
        """Show the research view."""
        self._switch_view("research")
    
    def action_show_ship_design(self) -> None:
        """Show the ship design view."""
        self._switch_view("ship_design")
    
    def action_show_colonies(self) -> None:
        """Show the colony management view."""
        self._switch_view("colonies")

    def _focus_fleet_index(self, index: int) -> None:
        """Focus and highlight a fleet by index."""
        self._switch_view("fleets")
        fleet_panel = self.query_one("#fleet_view", FleetPanel)
        fleet_panel.highlight_fleet(index)

    def action_focus_fleet_1(self) -> None:
        self._focus_fleet_index(0)

    def action_focus_fleet_2(self) -> None:
        self._focus_fleet_index(1)

    def action_focus_fleet_3(self) -> None:
        self._focus_fleet_index(2)

    def action_focus_fleet_4(self) -> None:
        self._focus_fleet_index(3)

    def action_focus_fleet_5(self) -> None:
        self._focus_fleet_index(4)
    
    def _switch_view(self, view_name: str) -> None:
        """Switch between different main views."""
        # Hide all views
        self.query_one("#system_view").add_class("hidden")
        self.query_one("#fleet_view").add_class("hidden") 
        self.query_one("#research_view").add_class("hidden")
        self.query_one("#design_view").add_class("hidden")
        self.query_one("#colony_view").add_class("hidden")
        
        # Show selected view
        if view_name == "systems":
            self.query_one("#system_view").remove_class("hidden")
        elif view_name == "fleets":
            self.query_one("#fleet_view").remove_class("hidden")
        elif view_name == "research":
            self.query_one("#research_view").remove_class("hidden")
        elif view_name == "ship_design":
            self.query_one("#design_view").remove_class("hidden")
        elif view_name == "colonies":
            self.query_one("#colony_view").remove_class("hidden")
        
        self.current_view = view_name
        
        message_log = self.query_one("#message_log", Log)
        message_log.write_line(f"Switched to {view_name} view.")
    
    def action_show_help(self) -> None:
        """Show help information."""
        message_log = self.query_one("#message_log", Log)
        message_log.write_line("=== PyAurora 4X Help ===")
        message_log.write_line("Keyboard shortcuts:")
        message_log.write_line("  q - Quit game")
        message_log.write_line("  s - Save game")
        message_log.write_line("  l - Load game")
        message_log.write_line("  space - Pause/Resume")
        message_log.write_line("  1 - Show star systems")
        message_log.write_line("  2 - Show fleets")
        message_log.write_line("  3 - Show research")
        message_log.write_line("  4 - Show ship design")
        message_log.write_line("  5 - Show colonies")
        message_log.write_line("  F1-F5 - Focus fleets 1-5")
        message_log.write_line("  h - Show this help")
    
    async def on_timer(self, event) -> None:
        """Handle periodic updates."""
        if self.simulation and not self.simulation.is_paused:
            # Auto-save periodically
            current_time = self.simulation.current_time
            if current_time - self.last_auto_save > self.auto_save_interval:
                self.action_save_game()
                self.last_auto_save = current_time
            
            # Update widgets periodically
            self._update_all_widgets()
    
    def on_key(self, event: events.Key) -> None:
        """Handle key presses."""
        key = event.key
        if key == "1":
            self.action_show_systems()
        elif key == "2":
            self.action_show_fleets()
        elif key == "3":
            self.action_show_research()
        elif key == "4":
            self.action_show_ship_design()
        elif key == "5":
            self.action_show_colonies()
        elif key == "q":
            self.action_quit()
        elif key == "s":
            self.action_save_game()
        elif key == "l":
            self.action_load_game()
        elif key == "h":
            self.action_show_help()
        elif key == "f1":
            self.action_focus_fleet_1()
        elif key == "f2":
            self.action_focus_fleet_2()
        elif key == "f3":
            self.action_focus_fleet_3()
        elif key == "f4":
            self.action_focus_fleet_4()
        elif key == "f5":
            self.action_focus_fleet_5()
        elif key == "space":
            self.action_toggle_pause()
        else:
            return
        event.prevent_default()
    
    async def action_quit(self) -> None:
        """Quit the application."""
        if self.simulation:
            # Auto-save before quitting
            try:
                self.action_save_game()
            except Exception as e:
                logger.error(f"Error auto-saving on quit: {e}")
        
        logger.info("PyAurora 4X application ending")
        self.exit()


# Make TimeControlEvent available to the widget
TimeControlWidget.TimeControlEvent = TimeControlEvent

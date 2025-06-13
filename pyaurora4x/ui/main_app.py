"""
Main Textual application for PyAurora 4X

Provides the terminal-based user interface for the game.
"""

from typing import Optional, Dict, Any
import asyncio
import logging

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header, Footer, Button, Static, Log, Placeholder,
    DataTable, ProgressBar, Label
)
from textual.binding import Binding
from textual.reactive import reactive
from textual import events

from pyaurora4x.engine.simulation import GameSimulation
from pyaurora4x.ui.widgets.star_system_view import StarSystemView
from pyaurora4x.ui.widgets.fleet_panel import FleetPanel
from pyaurora4x.ui.widgets.research_panel import ResearchPanel
from pyaurora4x.ui.widgets.empire_stats import EmpireStatsWidget
from pyaurora4x.data.save_manager import SaveManager

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
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("s", "save_game", "Save Game"),
        Binding("l", "load_game", "Load Game"),
        Binding("space", "toggle_pause", "Pause/Resume"),
        Binding("1", "show_systems", "Systems"),
        Binding("2", "show_fleets", "Fleets"),
        Binding("3", "show_research", "Research"),
        Binding("h", "show_help", "Help"),
    ]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.simulation: Optional[GameSimulation] = None
        self.save_manager = SaveManager()
        self.current_view = "systems"
        self.auto_save_interval = 300  # 5 minutes
        self.last_auto_save = 0
        self.load_file: Optional[str] = None
        self.load_data: Optional[Dict[str, Any]] = None
    
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
        
        # Define custom CSS as a class attribute instead of runtime update
        pass
        
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
        self.simulation.initialize_new_game()
        
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
            system_view.update_system(first_system)
        
        # Update fleet panel
        fleet_panel = self.query_one("#fleet_view", FleetPanel)
        player_empire = self.simulation.get_player_empire()
        if player_empire:
            fleets = [self.simulation.get_fleet(fid) for fid in player_empire.fleets if self.simulation.get_fleet(fid) is not None]
            fleet_panel.update_fleets(fleets)
        
        # Update research panel
        research_panel = self.query_one("#research_view", ResearchPanel)
        if player_empire:
            research_panel.update_empire(player_empire)
        
        # Update empire stats
        empire_stats = self.query_one("#empire_stats", EmpireStatsWidget)
        if player_empire:
            empire_stats.update_empire(player_empire)
        
        # Update time controls
        time_controls = self.query_one("#time_controls", TimeControlWidget)
        time_controls.update_status(
            self.simulation.current_time,
            self.simulation.is_paused
        )
    
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
        """Load a game (simplified - would need file selection in full implementation)."""
        message_log = self.query_one("#message_log", Log)
        message_log.write_line("Load game feature not implemented yet.")
    
    def action_show_systems(self) -> None:
        """Show the star systems view."""
        self._switch_view("systems")
    
    def action_show_fleets(self) -> None:
        """Show the fleets view."""
        self._switch_view("fleets")
    
    def action_show_research(self) -> None:
        """Show the research view."""
        self._switch_view("research")
    
    def _switch_view(self, view_name: str) -> None:
        """Switch between different main views."""
        # Hide all views
        self.query_one("#system_view").add_class("hidden")
        self.query_one("#fleet_view").add_class("hidden") 
        self.query_one("#research_view").add_class("hidden")
        
        # Show selected view
        if view_name == "systems":
            self.query_one("#system_view").remove_class("hidden")
        elif view_name == "fleets":
            self.query_one("#fleet_view").remove_class("hidden")
        elif view_name == "research":
            self.query_one("#research_view").remove_class("hidden")
        
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
        message_log.write_line("  h - Show this help")
    
    async def on_timer(self) -> None:
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
        # Let the binding system handle most keys
        pass
    
    def action_quit(self) -> None:
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

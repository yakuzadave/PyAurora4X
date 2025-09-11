"""
Victory Status Panel for PyAurora 4X

Comprehensive UI for displaying victory progress, leaderboards,
achievements, and game end screens.
"""

from typing import Optional, Dict, List, Any
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, Grid
from textual.widgets import Static, Label, Button, DataTable, ProgressBar, Tabs, TabPane
from textual.reactive import reactive
from textual.message import Message
from textual.binding import Binding

from pyaurora4x.core.models import Empire
from pyaurora4x.core.enums import VictoryCondition
from pyaurora4x.core.victory import GameResult, VictoryAchievement
from pyaurora4x.engine.victory_manager import VictoryManager
from pyaurora4x.core.events import EventManager, EventCategory, EventPriority


class VictoryPanel(Static):
    """
    Comprehensive victory status interface.
    
    Features:
    - Victory progress tracking for all conditions
    - Live leaderboard with empire rankings
    - Achievement system with unlocks
    - Detailed statistics display
    - Game end screens with results
    """
    
    BINDINGS = [
        Binding("v", "toggle_victory", "Victory Status", show=True),
        Binding("l", "show_leaderboard", "Leaderboard", show=True),
        Binding("a", "show_achievements", "Achievements", show=True),
        Binding("s", "show_statistics", "Statistics", show=True),
        Binding("escape", "close", "Close", show=True),
    ]
    
    current_empire = reactive(None)
    game_ended = reactive(False)
    
    def __init__(self, victory_manager: Optional[VictoryManager] = None,
                 event_manager: Optional[EventManager] = None, **kwargs):
        super().__init__(**kwargs)
        self.victory_manager = victory_manager
        self.event_manager = event_manager
        self.current_empire: Optional[Empire] = None
        self.game_result: Optional[GameResult] = None
        self.visible = False
    
    def compose(self) -> ComposeResult:
        """Compose the victory panel layout."""
        with Container(id="victory_container", classes="victory-panel"):
            yield Label("Victory Status & Progress", classes="panel-title")
            
            with Tabs(id="victory_tabs"):
                with TabPane("Progress", id="progress_tab"):
                    with Vertical(id="progress_content"):
                        yield Label("Victory Progress", classes="section-title")
                        
                        # Victory condition progress bars
                        with Container(id="victory_progress_container"):
                            yield Static("", id="victory_progress_display")
                        
                        # Current empire detailed progress
                        yield Label("Detailed Progress", classes="section-title")
                        with Container(id="detailed_progress"):
                            yield Static("", id="detailed_progress_display")
                
                with TabPane("Leaderboard", id="leaderboard_tab"):
                    with Vertical(id="leaderboard_content"):
                        yield Label("Empire Rankings", classes="section-title")
                        with Container(id="leaderboard_container"):
                            yield DataTable(id="leaderboard_table", classes="data-table")
                        
                        # Top empire details
                        yield Label("Leading Empire", classes="section-title")
                        yield Static("", id="leading_empire_details")
                
                with TabPane("Achievements", id="achievements_tab"):
                    with Vertical(id="achievements_content"):
                        yield Label("Achievements", classes="section-title")
                        
                        with Horizontal(id="achievement_filters"):
                            yield Button("All", id="filter_all", variant="primary")
                            yield Button("Military", id="filter_military", variant="outline")
                            yield Button("Economic", id="filter_economic", variant="outline")
                            yield Button("Scientific", id="filter_scientific", variant="outline")
                            yield Button("Diplomatic", id="filter_diplomatic", variant="outline")
                            yield Button("Exploration", id="filter_exploration", variant="outline")
                        
                        with Container(id="achievements_container"):
                            yield DataTable(id="achievements_table", classes="data-table")
                        
                        # Achievement details
                        yield Label("Recent Achievements", classes="section-title")
                        yield Static("", id="recent_achievements")
                
                with TabPane("Statistics", id="statistics_tab"):
                    with Vertical(id="statistics_content"):
                        yield Label("Empire Statistics", classes="section-title")
                        
                        with Grid(id="stats_grid"):
                            # Territory stats
                            with Container(classes="stats-section"):
                                yield Label("Territory & Exploration", classes="stats-category")
                                yield Static("", id="territory_stats")
                            
                            # Military stats  
                            with Container(classes="stats-section"):
                                yield Label("Military Performance", classes="stats-category")
                                yield Static("", id="military_stats")
                            
                            # Economic stats
                            with Container(classes="stats-section"):
                                yield Label("Economic Development", classes="stats-category")
                                yield Static("", id="economic_stats")
                            
                            # Technology stats
                            with Container(classes="stats-section"):
                                yield Label("Scientific Progress", classes="stats-category")
                                yield Static("", id="technology_stats")
                            
                            # Diplomatic stats
                            with Container(classes="stats-section"):
                                yield Label("Diplomatic Relations", classes="stats-category")
                                yield Static("", id="diplomatic_stats")
                            
                            # Overall scores
                            with Container(classes="stats-section"):
                                yield Label("Overall Performance", classes="stats-category")
                                yield Static("", id="overall_stats")
            
            # Game end overlay (hidden by default)
            with Container(id="game_end_overlay", classes="overlay hidden"):
                yield Label("Game Complete!", classes="game-end-title")
                with Container(id="game_end_content"):
                    yield Static("", id="game_end_results")
                    yield Static("", id="final_rankings")
                    
                    with Horizontal(id="game_end_actions"):
                        yield Button("View Detailed Results", id="view_details", variant="primary")
                        yield Button("Save Game Summary", id="save_summary", variant="outline")
                        yield Button("New Game", id="new_game", variant="success")
                        yield Button("Exit", id="exit_game", variant="error")
    
    def on_mount(self) -> None:
        """Initialize the victory panel."""
        self._setup_tables()
        self._update_all_displays()
        
        # Set up grid layout for statistics
        stats_grid = self.query_one("#stats_grid", Grid)
        stats_grid.styles.grid_size_columns = 2
        stats_grid.styles.grid_size_rows = 3
    
    def _setup_tables(self) -> None:
        """Setup data table columns."""
        # Leaderboard table
        leaderboard_table = self.query_one("#leaderboard_table", DataTable)
        leaderboard_table.add_columns(
            "Rank", "Empire", "Score", "Best Victory", "Progress", "Achievements"
        )
        leaderboard_table.cursor_type = "row"
        
        # Achievements table
        achievements_table = self.query_one("#achievements_table", DataTable)
        achievements_table.add_columns(
            "Icon", "Name", "Description", "Category", "Points", "Rarity", "Status"
        )
        achievements_table.cursor_type = "row"
    
    def update_empire(self, empire: Empire) -> None:
        """Update the current empire and refresh displays."""
        self.current_empire = empire
        self.current_empire = empire
        self._update_all_displays()
    
    def update_game_result(self, game_result: GameResult) -> None:
        """Update display when game ends."""
        self.game_result = game_result
        self.game_ended = True
        self._show_game_end_screen()
    
    def toggle_visibility(self) -> None:
        """Toggle panel visibility."""
        self.visible = not self.visible
        if self.visible:
            self.add_class("visible")
            self.remove_class("hidden")
            self._update_all_displays()
        else:
            self.add_class("hidden")
            self.remove_class("visible")
    
    def _update_all_displays(self) -> None:
        """Update all display sections."""
        if not self.victory_manager or not self.current_empire:
            return
        
        self._update_victory_progress()
        self._update_leaderboard()
        self._update_achievements()
        self._update_statistics()
    
    def _update_victory_progress(self) -> None:
        """Update victory progress displays."""
        if not self.victory_manager or not self.current_empire:
            return
        
        victory_status = self.victory_manager.get_victory_status(self.current_empire.id)
        if "error" in victory_status:
            return
        
        # Update main progress display
        progress_lines = []
        progress_lines.append("🏆 Victory Progress Overview\\n")
        
        for victory_type, progress_data in victory_status.get("progress", {}).items():
            progress = progress_data.get("progress", 0.0)
            is_achievable = progress_data.get("is_achievable", True)
            
            # Format victory type name
            victory_name = victory_type.replace('_', ' ').title()
            
            # Create progress bar representation
            bar_length = 20
            filled = int(progress * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            # Status indicator
            status = "🎯" if is_achievable else "❌"
            if progress >= 1.0:
                status = "🏆"
            elif progress >= 0.75:
                status = "🔥"
            elif progress >= 0.5:
                status = "⚡"
            
            progress_lines.append(f"{status} {victory_name}: [{bar}] {progress*100:.1f}%")
        
        progress_lines.append("")
        progress_lines.append(f"Current Rank: #{victory_status.get('current_rank', 'N/A')}")
        progress_lines.append(f"Total Score: {victory_status.get('total_score', 0):,.0f}")
        progress_lines.append(f"Achievements: {len(victory_status.get('achievements', []))}")
        
        try:
            display = self.query_one("#victory_progress_display", Static)
            display.update("\\n".join(progress_lines))
        except Exception:
            pass
        
        # Update detailed progress for current best victory path
        self._update_detailed_progress(victory_status)
    
    def _update_detailed_progress(self, victory_status: Dict[str, Any]) -> None:
        """Update detailed progress for the best victory path."""
        progress_data = victory_status.get("progress", {})
        
        # Find best progress
        best_progress = 0.0
        best_victory_type = None
        
        for victory_type, data in progress_data.items():
            if data.get("progress", 0.0) > best_progress:
                best_progress = data.get("progress", 0.0)
                best_victory_type = victory_type
        
        if not best_victory_type:
            return
        
        best_data = progress_data[best_victory_type]
        details = best_data.get("details", {})
        
        detail_lines = []
        detail_lines.append(f"🎯 Best Victory Path: {best_victory_type.replace('_', ' ').title()}")
        detail_lines.append("")
        
        if best_victory_type == "conquest":
            systems_controlled = details.get("systems_controlled", 0)
            target_systems = details.get("target_systems", 0)
            control_percentage = details.get("control_percentage", 0)
            
            detail_lines.append(f"Systems Controlled: {systems_controlled}/{target_systems}")
            detail_lines.append(f"Galaxy Control: {control_percentage:.1f}%")
            detail_lines.append(f"Progress: {best_progress*100:.1f}%")
            
        elif best_victory_type == "research":
            trees_completed = details.get("tech_trees_completed", 0)
            target_trees = details.get("target_trees", 0)
            total_techs = details.get("total_technologies", 0)
            
            detail_lines.append(f"Tech Trees Completed: {trees_completed}/{target_trees}")
            detail_lines.append(f"Total Technologies: {total_techs}")
            detail_lines.append(f"Progress: {best_progress*100:.1f}%")
            
        elif best_victory_type == "economic":
            empire_gdp = details.get("empire_gdp", 0)
            gdp_ratio = details.get("gdp_ratio", 0)
            target_ratio = details.get("target_ratio", 0)
            
            detail_lines.append(f"Empire GDP: {empire_gdp:,.0f}")
            detail_lines.append(f"GDP Ratio: {gdp_ratio:.2f}x (Target: {target_ratio:.2f}x)")
            detail_lines.append(f"Progress: {best_progress*100:.1f}%")
            
        elif best_victory_type == "exploration":
            systems_explored = details.get("systems_explored", 0)
            target_systems = details.get("target_systems", 0)
            exploration_percentage = details.get("exploration_percentage", 0)
            
            detail_lines.append(f"Systems Explored: {systems_explored}/{target_systems}")
            detail_lines.append(f"Galaxy Explored: {exploration_percentage:.1f}%")
            detail_lines.append(f"Progress: {best_progress*100:.1f}%")
        
        # Add milestones info
        milestones_reached = best_data.get("milestones_reached", 0)
        total_milestones = best_data.get("total_milestones", 0)
        
        detail_lines.append("")
        detail_lines.append(f"Milestones: {milestones_reached}/{total_milestones}")
        
        if best_data.get("estimated_completion"):
            detail_lines.append(f"ETA: {best_data['estimated_completion']:.1f} years")
        
        try:
            display = self.query_one("#detailed_progress_display", Static)
            display.update("\\n".join(detail_lines))
        except Exception:
            pass
    
    def _update_leaderboard(self) -> None:
        """Update the leaderboard display."""
        if not self.victory_manager:
            return
        
        leaderboard = self.victory_manager.get_leaderboard()
        
        # Update table
        table = self.query_one("#leaderboard_table", DataTable)
        table.clear()
        
        for entry in leaderboard:
            rank = entry["rank"]
            empire_name = entry["empire_name"]
            total_score = f"{entry['total_score']:,.0f}"
            best_victory_type = entry.get("best_victory_type", "None")
            best_progress = f"{entry.get('best_victory_progress', 0)*100:.1f}%"
            achievements_count = entry["achievements_count"]
            
            # Add rank indicators
            rank_display = str(rank)
            if rank == 1:
                rank_display = "🥇"
            elif rank == 2:
                rank_display = "🥈"
            elif rank == 3:
                rank_display = "🥉"
            
            table.add_row(
                rank_display,
                empire_name,
                total_score,
                best_victory_type.replace('_', ' ').title() if best_victory_type != "None" else "None",
                best_progress,
                str(achievements_count),
                key=entry["empire_id"]
            )
        
        # Update leading empire details
        if leaderboard:
            leading_empire = leaderboard[0]
            
            detail_lines = []
            detail_lines.append(f"🏆 Leading Empire: {leading_empire['empire_name']}")
            detail_lines.append(f"Total Score: {leading_empire['total_score']:,.0f}")
            detail_lines.append(f"Best Victory Path: {leading_empire.get('best_victory_type', 'None').replace('_', ' ').title()}")
            detail_lines.append(f"Victory Progress: {leading_empire.get('best_victory_progress', 0)*100:.1f}%")
            detail_lines.append(f"Achievements: {leading_empire['achievements_count']}")
            
            try:
                display = self.query_one("#leading_empire_details", Static)
                display.update("\\n".join(detail_lines))
            except Exception:
                pass
    
    def _update_achievements(self) -> None:
        """Update achievements display."""
        if not self.victory_manager:
            return
        
        table = self.query_one("#achievements_table", DataTable)
        table.clear()
        
        # Get achievements (filter by current empire if available)
        all_achievements = self.victory_manager.achievements
        current_filter = "all"  # Would be set by filter buttons
        
        for achievement in all_achievements:
            if current_filter != "all" and achievement.category != current_filter:
                continue
            
            icon = achievement.icon
            name = achievement.name
            description = achievement.description
            category = achievement.category.title()
            points = f"{achievement.points_value:.0f}"
            rarity = achievement.rarity.title()
            
            # Status
            if achievement.is_unlocked:
                if achievement.unlocked_by_empire == (self.current_empire.id if self.current_empire else None):
                    status = "🏆 Unlocked"
                else:
                    status = f"✅ {self.victory_manager.empire_statistics.get(achievement.unlocked_by_empire, type('obj', (object,), {'empire_name': 'Unknown'})).empire_name}"
            else:
                status = "🔒 Locked"
            
            table.add_row(icon, name, description, category, points, rarity, status, key=achievement.achievement_id)
        
        # Update recent achievements
        if self.current_empire:
            empire_achievements = [a for a in all_achievements if a.unlocked_by_empire == self.current_empire.id]
            recent_achievements = sorted(empire_achievements, key=lambda x: x.unlocked_at_time or 0, reverse=True)[:5]
            
            recent_lines = []
            if recent_achievements:
                recent_lines.append("🎉 Recent Achievements:")
                for achievement in recent_achievements:
                    recent_lines.append(f"{achievement.icon} {achievement.name} - {achievement.points_value:.0f} pts")
            else:
                recent_lines.append("No achievements unlocked yet.")
            
            try:
                display = self.query_one("#recent_achievements", Static)
                display.update("\\n".join(recent_lines))
            except Exception:
                pass
    
    def _update_statistics(self) -> None:
        """Update detailed statistics display."""
        if not self.victory_manager or not self.current_empire:
            return
        
        stats = self.victory_manager.empire_statistics.get(self.current_empire.id)
        if not stats:
            return
        
        # Territory stats
        territory_lines = [
            f"Systems Controlled: {stats.systems_controlled}",
            f"Systems Explored: {stats.systems_explored}",
            f"Total Systems: {stats.total_systems}",
            f"Planets Colonized: {stats.planets_colonized}",
            f"Territory Score: {stats.total_territory_score:,.0f}"
        ]
        
        # Military stats
        military_lines = [
            f"Ships Built: {stats.total_ships_built}",
            f"Ships Lost: {stats.total_ships_lost}",
            f"Battles Won: {stats.battles_won}",
            f"Battles Lost: {stats.battles_lost}",
            f"Enemy Ships Destroyed: {stats.enemy_ships_destroyed}",
            f"Military Score: {stats.military_score:,.0f}"
        ]
        
        # Economic stats
        economic_lines = [
            f"Minerals Mined: {stats.total_minerals_mined:,.0f}",
            f"Energy Generated: {stats.total_energy_generated:,.0f}",
            f"Peak Population: {stats.peak_population:,}",
            f"Economic Score: {stats.economic_score:,.0f}"
        ]
        
        # Technology stats
        technology_lines = [
            f"Technologies Researched: {stats.technologies_researched}",
            f"Research Points: {stats.total_research_points:,.0f}",
            f"Tech Trees: {stats.total_tech_trees}",
            f"Tech Score: {stats.tech_score:,.0f}"
        ]
        
        # Diplomatic stats
        diplomatic_lines = [
            f"Treaties Signed: {stats.treaties_signed}",
            f"Alliances Formed: {stats.alliances_formed}",
            f"Wars Declared: {stats.wars_declared}",
            f"Diplomatic Score: {stats.diplomatic_score:,.0f}"
        ]
        
        # Overall stats
        overall_lines = [
            f"Total Score: {stats.total_score:,.0f}",
            f"Victory Points: {stats.victory_points:,.0f}",
            f"Current Rank: #{stats.final_rank or self.victory_manager._get_empire_rank(self.current_empire.id)}",
            f"Game Time: {stats.total_game_time:.1f} years"
        ]
        
        # Update displays
        displays = [
            ("#territory_stats", territory_lines),
            ("#military_stats", military_lines),
            ("#economic_stats", economic_lines),
            ("#technology_stats", technology_lines),
            ("#diplomatic_stats", diplomatic_lines),
            ("#overall_stats", overall_lines)
        ]
        
        for display_id, lines in displays:
            try:
                display = self.query_one(display_id, Static)
                display.update("\\n".join(lines))
            except Exception:
                pass
    
    def _show_game_end_screen(self) -> None:
        """Show the game end overlay with results."""
        if not self.game_result:
            return
        
        # Show overlay
        overlay = self.query_one("#game_end_overlay")
        overlay.remove_class("hidden")
        overlay.add_class("visible")
        
        # Update game end results
        result_lines = []
        result_lines.append(f"🎊 {self.game_result.game_end_reason}")
        result_lines.append("")
        
        if self.game_result.winner_empire_ids:
            winner_stats = self.game_result.empire_statistics.get(self.game_result.winner_empire_ids[0])
            if winner_stats:
                result_lines.append(f"🏆 Winner: {winner_stats.empire_name}")
                result_lines.append(f"Victory Type: {self.game_result.victory_condition.value.title()}")
        
        result_lines.append(f"Game Duration: {self.game_result.total_duration:.1f} years")
        result_lines.append(f"Total Empires: {len(self.game_result.empire_statistics)}")
        
        try:
            results_display = self.query_one("#game_end_results", Static)
            results_display.update("\\n".join(result_lines))
        except Exception:
            pass
        
        # Update final rankings
        ranking_lines = []
        ranking_lines.append("🏅 Final Rankings:")
        ranking_lines.append("")
        
        for empire_id, rank, score in self.game_result.empire_rankings[:5]:  # Show top 5
            stats = self.game_result.empire_statistics.get(empire_id)
            if stats:
                rank_icon = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][rank-1] if rank <= 5 else f"{rank}."
                ranking_lines.append(f"{rank_icon} {stats.empire_name}: {score:,.0f} points")
        
        try:
            rankings_display = self.query_one("#final_rankings", Static)
            rankings_display.update("\\n".join(ranking_lines))
        except Exception:
            pass
    
    # Event handlers
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "view_details":
            # Switch to statistics tab for detailed view
            tabs = self.query_one("#victory_tabs", Tabs)
            tabs.active = "statistics_tab"
        
        elif button_id == "save_summary":
            # Save game summary (would implement file saving)
            if self.event_manager:
                self.event_manager.emit_event(
                    EventCategory.UI,
                    EventPriority.NORMAL,
                    "Game Summary Saved",
                    {"game_result": self.game_result.dict() if self.game_result else {}}
                )
        
        elif button_id == "new_game":
            # Start new game (would trigger game restart)
            if self.event_manager:
                self.event_manager.emit_event(
                    EventCategory.GAME,
                    EventPriority.HIGH,
                    "New Game Requested",
                    {}
                )
        
        elif button_id == "exit_game":
            # Exit application
            if self.event_manager:
                self.event_manager.emit_event(
                    EventCategory.GAME,
                    EventPriority.HIGH,
                    "Exit Game Requested",
                    {}
                )
        
        elif button_id.startswith("filter_"):
            # Handle achievement filter buttons
            filter_type = button_id.replace("filter_", "")
            self._apply_achievement_filter(filter_type)
    
    def _apply_achievement_filter(self, filter_type: str) -> None:
        """Apply filter to achievements display."""
        # Update button styles
        for button in self.query("Button"):
            if button.id and button.id.startswith("filter_"):
                if button.id == f"filter_{filter_type}":
                    button.variant = "primary"
                else:
                    button.variant = "outline"
        
        # Update achievements table with filter
        # This would be implemented with the filter logic
        self._update_achievements()
    
    # Action methods for keybindings
    
    def action_toggle_victory(self) -> None:
        """Toggle victory panel visibility."""
        self.toggle_visibility()
    
    def action_show_leaderboard(self) -> None:
        """Switch to leaderboard tab."""
        if self.visible:
            tabs = self.query_one("#victory_tabs", Tabs)
            tabs.active = "leaderboard_tab"
    
    def action_show_achievements(self) -> None:
        """Switch to achievements tab."""
        if self.visible:
            tabs = self.query_one("#victory_tabs", Tabs)
            tabs.active = "achievements_tab"
    
    def action_show_statistics(self) -> None:
        """Switch to statistics tab."""
        if self.visible:
            tabs = self.query_one("#victory_tabs", Tabs)
            tabs.active = "statistics_tab"
    
    def action_close(self) -> None:
        """Close the victory panel."""
        if self.visible:
            self.toggle_visibility()

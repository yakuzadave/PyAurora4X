"""
Empire Statistics Widget for PyAurora 4X

Displays empire statistics, resources, and overall status.
"""

from typing import Optional
from textual.widgets import Static, Label
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.reactive import reactive

from pyaurora4x.core.models import Empire
from pyaurora4x.core.utils import format_time


class EmpireStatsWidget(Static):
    """
    Widget for displaying empire statistics and status.
    
    Shows resources, research progress, fleet summary,
    and other empire-level information.
    """
    
    empire = reactive(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_empire: Optional[Empire] = None
    
    def compose(self) -> ComposeResult:
        """Compose the empire stats layout."""
        with Container(id="empire_stats_container"):
            yield Label("Empire Status", classes="panel-title")
            
            with Vertical(id="empire_info"):
                yield Static("", id="empire_basic_info", classes="info-section")
                yield Static("", id="empire_resources", classes="info-section")
                yield Static("", id="empire_research", classes="info-section")
                yield Static("", id="empire_military", classes="info-section")
                yield Static("", id="empire_colonies", classes="info-section")
    
    def update_empire(self, empire: Empire) -> None:
        """
        Update the displayed empire.
        
        Args:
            empire: Empire to display statistics for
        """
        self.current_empire = empire
        self._update_all_sections()
    
    def _update_all_sections(self) -> None:
        """Update all information sections."""
        if not self.current_empire:
            self._show_no_empire()
            return
        
        self._update_basic_info()
        self._update_resources()
        self._update_research()
        self._update_military()
        self._update_colonies()
    
    def _show_no_empire(self) -> None:
        """Show message when no empire is loaded."""
        try:
            basic_info = self.query_one("#empire_basic_info", Static)
            basic_info.update("No empire data available")
            
            # Clear other sections
            for section_id in ["empire_resources", "empire_research", "empire_military", "empire_colonies"]:
                section = self.query_one(f"#{section_id}", Static)
                section.update("")
        except Exception:
            pass  # Widgets might not be ready yet
    
    def _update_basic_info(self) -> None:
        """Update basic empire information."""
        empire = self.current_empire
        if not empire:
            return
        
        lines = []
        lines.append(f"Empire: {empire.name}")
        lines.append(f"Government: {empire.government_type}")
        lines.append(f"Culture: {empire.culture}")
        
        if empire.established_date > 0:
            age = format_time(empire.established_date)
            lines.append(f"Age: {age}")
        
        lines.append(f"Home System: {empire.home_system_id}")
        lines.append(f"Controlled Systems: {len(empire.controlled_systems)}")
        
        text = '\n'.join(lines)
        
        try:
            basic_info = self.query_one("#empire_basic_info", Static)
            basic_info.update(text)
        except Exception:
            pass
    
    def _update_resources(self) -> None:
        """Update resource information."""
        empire = self.current_empire
        if not empire:
            return
        
        lines = []
        lines.append("=== Resources ===")
        
        if empire.resources:
            for resource, amount in empire.resources.items():
                resource_name = resource.replace('_', ' ').title()
                lines.append(f"{resource_name}: {amount:.0f}")
        else:
            # Default resources for new empires
            lines.append("Minerals: 1000")
            lines.append("Energy: 500")
            lines.append("Research: 100")
            lines.append("Food: 800")
        
        if empire.income:
            lines.append("")
            lines.append("Income:")
            for resource, income in empire.income.items():
                resource_name = resource.replace('_', ' ').title()
                sign = "+" if income >= 0 else ""
                lines.append(f"  {resource_name}: {sign}{income:.1f}/turn")
        
        text = '\n'.join(lines)
        
        try:
            resources = self.query_one("#empire_resources", Static)
            resources.update(text)
        except Exception:
            pass
    
    def _update_research(self) -> None:
        """Update research information."""
        empire = self.current_empire
        if not empire:
            return
        
        lines = []
        lines.append("=== Research ===")
        
        # Research points
        lines.append(f"Research Points: {empire.research_points:.0f}")
        
        # Current research
        if empire.current_research:
            current_tech = empire.technologies.get(empire.current_research)
            if current_tech:
                progress = min(empire.research_points / current_tech.research_cost * 100, 100)
                lines.append(f"Current: {current_tech.name}")
                lines.append(f"Progress: {progress:.1f}%")
            else:
                lines.append("Current: Unknown technology")
        else:
            lines.append("Current: No active research")
        
        # Research allocation
        if empire.research_allocation:
            lines.append("")
            lines.append("Research Focus:")
            for tech_type, allocation in empire.research_allocation.items():
                type_name = tech_type.value if hasattr(tech_type, 'value') else str(tech_type)
                lines.append(f"  {type_name.title()}: {allocation:.1f}%")
        
        # Completed technologies
        completed_count = sum(1 for tech in empire.technologies.values() if tech.is_researched)
        total_count = len(empire.technologies)
        lines.append("")
        lines.append(f"Completed: {completed_count}/{total_count} technologies")
        
        text = '\n'.join(lines)
        
        try:
            research = self.query_one("#empire_research", Static)
            research.update(text)
        except Exception:
            pass
    
    def _update_military(self) -> None:
        """Update military information."""
        empire = self.current_empire
        if not empire:
            return
        
        lines = []
        lines.append("=== Military ===")
        
        # Fleet summary
        fleet_count = len(empire.fleets)
        lines.append(f"Fleets: {fleet_count}")
        
        # Ship designs
        design_count = len(empire.ship_designs)
        lines.append(f"Ship Designs: {design_count}")
        
        # Placeholder for additional military stats
        lines.append("Total Ships: 0")  # Would calculate from actual fleets
        lines.append("Military Strength: Unknown")
        
        # Recent military events (placeholder)
        lines.append("")
        lines.append("Recent Activity:")
        lines.append("  No recent military activity")
        
        text = '\n'.join(lines)
        
        try:
            military = self.query_one("#empire_military", Static)
            military.update(text)
        except Exception:
            pass
    
    def _update_colonies(self) -> None:
        """Update colony information."""
        empire = self.current_empire
        if not empire:
            return
        
        lines = []
        lines.append("=== Colonies ===")
        
        # Colony count
        colony_count = len(empire.colonies)
        lines.append(f"Colonies: {colony_count}")
        
        if colony_count == 0:
            lines.append("No colonies established")
        else:
            # Placeholder for colony statistics
            lines.append("Total Population: Unknown")
            lines.append("Production Capacity: Unknown")
            lines.append("")
            lines.append("Colony Status:")
            for colony_id in empire.colonies[:3]:  # Show first 3 colonies
                lines.append(f"  Colony {colony_id}: Operational")
            
            if len(empire.colonies) > 3:
                lines.append(f"  ... and {len(empire.colonies) - 3} more")
        
        text = '\n'.join(lines)
        
        try:
            colonies = self.query_one("#empire_colonies", Static)
            colonies.update(text)
        except Exception:
            pass
    
    def on_mount(self) -> None:
        """Initialize the widget when mounted."""
        self._update_all_sections()
    
    def watch_empire(self, empire: Empire) -> None:
        """React to empire changes."""
        if empire:
            self.current_empire = empire
            self._update_all_sections()


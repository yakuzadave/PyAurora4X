"""
Research Panel Widget for PyAurora 4X

Displays technology tree, research progress, and allows research management.
"""

from typing import List, Optional
from textual.widgets import Static, DataTable, Button, Label, ProgressBar
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive

from pyaurora4x.core.models import Empire, Technology


class ResearchPanel(Static):
    """
    Widget for displaying and managing research.
    
    Shows available technologies, research progress,
    and allows starting new research projects.
    """
    
    empire = reactive(None)
    selected_tech = reactive(None)
    
    def __init__(self, tech_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.current_empire: Optional[Empire] = None
        self.current_tech: Optional[Technology] = None
        self.available_techs: List[Technology] = []
        self.tech_manager = tech_manager
    
    def compose(self) -> ComposeResult:
        """Compose the research panel layout."""
        with Container(id="research_container"):
            with Horizontal():
                # Left side - available technologies
                with Vertical(id="tech_list_panel", classes="panel-section"):
                    yield Label("Available Technologies", classes="panel-title")
                    yield DataTable(id="tech_table", cursor_type="row")
                
                # Right side - technology details and research status
                with Vertical(id="tech_details_panel", classes="panel-section"):
                    yield Label("Technology Details", classes="panel-title")
                    yield Static("", id="tech_info", classes="info-display")
                    
                    # Research controls
                    with Vertical(id="research_controls"):
                        yield Label("Research Progress", classes="section-label")
                        yield Static("", id="current_research", classes="research-status")
                        yield ProgressBar(id="research_progress")
                        yield Button("Start Research", id="start_research", variant="primary")
                        yield Button("Cancel Research", id="cancel_research", variant="error")
    
    def on_mount(self) -> None:
        """Initialize the research panel."""
        self._setup_tech_table()
        self._update_display()
    
    def _setup_tech_table(self) -> None:
        """Set up the technology data table."""
        table = self.query_one("#tech_table", DataTable)
        table.add_columns("Technology", "Type", "Cost", "Status")
        table.cursor_type = "row"
    
    def update_empire(self, empire: Empire) -> None:
        """
        Update the empire and refresh research data.
        
        Args:
            empire: Empire to display research for
        """
        self.current_empire = empire
        # Ensure empire has technologies loaded
        if not self.current_empire.technologies and self.tech_manager:
            self.current_empire.technologies = {
                tid: Technology(**t.model_dump())
                for tid, t in self.tech_manager.get_all_technologies().items()
            }

        self._load_available_technologies()
        self._refresh_tech_table()
        self._update_research_status()
        
        # Select first available tech if none selected
        if self.available_techs and not self.current_tech:
            self.current_tech = self.available_techs[0]
            self._update_tech_details()
    
    def _load_available_technologies(self) -> None:
        """Load available technologies from game data."""
        if not self.current_empire:
            self.available_techs = []
            return
        
        self.available_techs = list(self.current_empire.technologies.values())
    
    
    def _refresh_tech_table(self) -> None:
        """Refresh the technology table with current data."""
        table = self.query_one("#tech_table", DataTable)
        table.clear()
        
        for tech in self.available_techs:
            name = tech.name
            tech_type = tech.tech_type.value if hasattr(tech.tech_type, 'value') else str(tech.tech_type)
            cost = str(tech.research_cost)
            status = "✓ Researched" if tech.is_researched else "Available"
            
            # Check if prerequisites are met
            if not tech.is_researched and not self._are_prerequisites_met(tech):
                status = "🔒 Locked"
            
            table.add_row(name, tech_type.title(), cost, status, key=tech.id)
    
    def _are_prerequisites_met(self, tech: Technology) -> bool:
        """Check if technology prerequisites are met."""
        if not self.current_empire:
            return False
        
        for prereq_id in tech.prerequisites:
            prereq_tech = self.current_empire.technologies.get(prereq_id)
            if not prereq_tech or not prereq_tech.is_researched:
                return False
        
        return True
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle technology selection in the table."""
        if event.data_table.id == "tech_table":
            tech_id = event.row_key
            self.current_tech = next((t for t in self.available_techs if t.id == tech_id), None)
            self._update_tech_details()
    
    def _update_tech_details(self) -> None:
        """Update the technology details display."""
        if not self.current_tech:
            self._show_no_tech_selected()
            return
        
        tech = self.current_tech
        details = self._generate_tech_details(tech)
        
        info_widget = self.query_one("#tech_info", Static)
        info_widget.update(details)
        
        # Update research button state
        self._update_research_controls()
    
    def _generate_tech_details(self, tech: Technology) -> str:
        """Generate detailed technology information text."""
        lines = []
        
        # Basic tech info
        lines.append(f"Technology: {tech.name}")
        tech_type = tech.tech_type.value if hasattr(tech.tech_type, 'value') else str(tech.tech_type)
        lines.append(f"Type: {tech_type.title()}")
        lines.append(f"Research Cost: {tech.research_cost} RP")
        lines.append("")
        
        # Description
        lines.append("Description:")
        lines.append(tech.description)
        lines.append("")
        
        # Status
        if tech.is_researched:
            lines.append("Status: ✓ Researched")
        else:
            prerequisites_met = self._are_prerequisites_met(tech)
            if prerequisites_met:
                lines.append("Status: Available for research")
            else:
                lines.append("Status: 🔒 Prerequisites not met")
        
        # Prerequisites
        if tech.prerequisites:
            lines.append("")
            lines.append("Prerequisites:")
            for prereq_id in tech.prerequisites:
                prereq_name = prereq_id.replace('_', ' ').title()
                if self.current_empire:
                    prereq_tech = self.current_empire.technologies.get(prereq_id)
                    if prereq_tech and prereq_tech.is_researched:
                        lines.append(f"  ✓ {prereq_name}")
                    else:
                        lines.append(f"  ✗ {prereq_name}")
                else:
                    lines.append(f"  ? {prereq_name}")
        
        # Unlocks
        if tech.unlocks:
            lines.append("")
            lines.append("Unlocks:")
            for unlock in tech.unlocks:
                unlock_name = unlock.replace('_', ' ').title()
                lines.append(f"  → {unlock_name}")
        
        return '\n'.join(lines)
    
    def _show_no_tech_selected(self) -> None:
        """Show message when no technology is selected."""
        info_widget = self.query_one("#tech_info", Static)
        info_widget.update("Select a technology from the list to view details.")
    
    def _update_research_status(self) -> None:
        """Update the current research status display."""
        if not self.current_empire:
            return
        
        current_research_widget = self.query_one("#current_research", Static)
        progress_bar = self.query_one("#research_progress", ProgressBar)
        
        if self.current_empire.current_research:
            # Find the technology being researched
            research_tech = self.current_empire.technologies.get(
                self.current_empire.current_research
            )
            
            if research_tech:
                # Calculate progress (simplified)
                progress_percentage = min(
                    (self.current_empire.research_points / research_tech.research_cost) * 100,
                    100
                )
                
                current_research_widget.update(
                    f"Researching: {research_tech.name}\n"
                    f"Progress: {self.current_empire.research_points:.0f} / {research_tech.research_cost} RP"
                )
                progress_bar.update(progress=progress_percentage)
            else:
                current_research_widget.update("No active research")
                progress_bar.update(progress=0)
        else:
            current_research_widget.update("No active research")
            progress_bar.update(progress=0)
    
    def _update_research_controls(self) -> None:
        """Update the state of research control buttons."""
        if not self.current_tech or not self.current_empire:
            return
        
        try:
            start_btn = self.query_one("#start_research", Button)
            cancel_btn = self.query_one("#cancel_research", Button)
            
            # Start button logic
            can_start = (
                not self.current_tech.is_researched and
                self._are_prerequisites_met(self.current_tech) and
                self.current_empire.current_research != self.current_tech.id
            )
            start_btn.disabled = not can_start
            
            # Cancel button logic
            can_cancel = self.current_empire.current_research is not None
            cancel_btn.disabled = not can_cancel
            
        except Exception:
            pass  # Buttons might not be ready yet
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle research control button presses."""
        if not self.current_empire:
            return
        
        button_id = event.button.id
        
        if button_id == "start_research":
            self._handle_start_research()
        elif button_id == "cancel_research":
            self._handle_cancel_research()
    
    def _handle_start_research(self) -> None:
        """Handle start research command."""
        if not self.current_tech or not self.current_empire:
            return
        
        if self.current_tech.is_researched:
            return
        
        if not self._are_prerequisites_met(self.current_tech):
            return
        
        # Start researching the selected technology
        self.current_empire.current_research = self.current_tech.id
        self.current_empire.research_points = 0  # Reset progress
        
        # Add technology to empire if not already present
        if self.current_tech.id not in self.current_empire.technologies:
            self.current_empire.technologies[self.current_tech.id] = self.current_tech
        
        self._update_research_status()
        self._update_research_controls()
        self.post_message_no_wait(ResearchCommandEvent("start", self.current_tech.id))
    
    def _handle_cancel_research(self) -> None:
        """Handle cancel research command."""
        if not self.current_empire:
            return
        
        self.current_empire.current_research = None
        self.current_empire.research_points = 0
        
        self._update_research_status()
        self._update_research_controls()
        self.post_message_no_wait(ResearchCommandEvent("cancel", None))
    
    def _update_display(self) -> None:
        """Update the entire display."""
        if not self.current_empire:
            info_widget = self.query_one("#tech_info", Static)
            info_widget.update("No empire data available.")
        else:
            self._refresh_tech_table()
            self._update_research_status()
            if self.current_tech:
                self._update_tech_details()

    def refresh(self) -> None:
        """Refresh research information."""
        self._update_display()


class ResearchCommandEvent:
    """Event for research commands."""
    
    def __init__(self, command: str, tech_id: Optional[str]):
        self.command = command
        self.tech_id = tech_id


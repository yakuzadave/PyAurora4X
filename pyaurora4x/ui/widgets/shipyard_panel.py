"""
Shipyard Management Panel for PyAurora 4X

Displays shipyards, slipways, build queues, and allows order management.
"""

from typing import Dict, List, Optional, Any
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Button, DataTable, Label, Input, Select
from textual.reactive import reactive
from textual.css.query import NoMatches
import logging

from pyaurora4x.core.shipyards import Shipyard, BuildOrder, RefitOrder, YardType

logger = logging.getLogger(__name__)


class ShipyardPanel(Static):
    """UI panel for managing shipyards and construction orders."""

    current_empire_id: reactive[str] = reactive("")
    current_yard_id: reactive[str] = reactive("")

    def __init__(self, simulation=None, **kwargs):
        super().__init__(**kwargs)
        self.simulation = simulation
        self.yards: Dict[str, Shipyard] = {}

    def compose(self) -> ComposeResult:
        """Compose the shipyard panel layout."""
        with Vertical():
            yield Label("Shipyard Management", classes="panel-title")
            
            with Horizontal():
                # Left panel: Shipyard list
                with Vertical(classes="shipyard-list"):
                    yield Label("Shipyards")
                    yield DataTable(id="shipyards-table")
                    
                    with Horizontal():
                        yield Button("New Yard", id="new-yard", variant="primary")
                        yield Button("Upgrade Yard", id="upgrade-yard")
                
                # Right panel: Selected yard details
                with Vertical(classes="yard-details"):
                    yield Label("Yard Details", id="yard-title")
                    yield Static("", id="yard-info")
                    
                    # Slipways status
                    yield Label("Slipways")
                    yield DataTable(id="slipways-table")
                    
                    # Build queue
                    yield Label("Build Queue")
                    yield DataTable(id="queue-table")
                    
                    with Horizontal():
                        yield Button("Add Order", id="add-order", variant="success")
                        yield Button("Cancel Order", id="cancel-order", variant="error")
                        yield Button("Pause/Resume", id="toggle-order")

    def on_mount(self) -> None:
        """Initialize tables and load data."""
        self._setup_tables()
        self.refresh_display()

    def _setup_tables(self) -> None:
        """Setup table columns."""
        # Shipyards table
        shipyards_table = self.query_one("#shipyards-table", DataTable)
        shipyards_table.add_columns("Name", "Type", "BP/Day", "Queue", "Status")
        
        # Slipways table  
        slipways_table = self.query_one("#slipways-table", DataTable)
        slipways_table.add_columns("ID", "Max Tonnage", "Status", "ETA")
        
        # Queue table
        queue_table = self.query_one("#queue-table", DataTable)
        queue_table.add_columns("Order", "Design", "Progress", "Priority", "Status")

    def watch_current_empire_id(self, empire_id: str) -> None:
        """React to empire selection changes."""
        self.refresh_display()

    def watch_current_yard_id(self, yard_id: str) -> None:
        """React to yard selection changes."""
        self.refresh_yard_details()

    def refresh_display(self) -> None:
        """Refresh the entire display with current data."""
        if not self.simulation:
            return
            
        # Get yards for current empire
        self.yards = {
            yard_id: yard for yard_id, yard in self.simulation.shipyard_manager.yards.items()
            if yard.empire_id == self.current_empire_id
        }

        if not self._ui_ready():
            return

        self._update_shipyards_table()
        self.refresh_yard_details()

    def _update_shipyards_table(self) -> None:
        """Update the shipyards table."""
        table = self.query_one("#shipyards-table", DataTable)
        table.clear()
        
        for yard_id, yard in self.yards.items():
            queue_count = len(yard.build_queue) + len(yard.refit_queue)
            active_slips = sum(1 for slip in yard.slipways if slip.active_order_id)
            total_slips = len(yard.slipways)
            
            status = f"{active_slips}/{total_slips} active"
            
            table.add_row(
                yard.name,
                yard.yard_type.value.title(),
                f"{yard.effective_bp_per_day():.1f}",
                str(queue_count),
                status,
                key=yard_id
            )

    def refresh_yard_details(self) -> None:
        """Update the yard details panel."""
        if not self.current_yard_id or self.current_yard_id not in self.yards:
            self._clear_yard_details()
            return

        if not self._ui_ready():
            return
            
        yard = self.yards[self.current_yard_id]
        
        # Update yard info
        info = self.query_one("#yard-info", Static)
        info.update(
            f"Type: {yard.yard_type.value.title()}\n"
            f"Base BP/Day: {yard.bp_per_day:.1f}\n"
            f"Tooling Bonus: {yard.tooling_bonus:.1f}x\n"
            f"Effective BP/Day: {yard.effective_bp_per_day():.1f}"
        )
        
        # Update title
        title = self.query_one("#yard-title", Label)
        title.update(f"Yard Details: {yard.name}")
        
        self._update_slipways_table(yard)
        self._update_queue_table(yard)

    def _clear_yard_details(self) -> None:
        """Clear yard details when no yard selected."""
        if not self._ui_ready():
            return

        self.query_one("#yard-info", Static).update("No yard selected")
        self.query_one("#yard-title", Label).update("Yard Details")
        
        self.query_one("#slipways-table", DataTable).clear()
        self.query_one("#queue-table", DataTable).clear()

    def _update_slipways_table(self, yard: Shipyard) -> None:
        """Update the slipways table for a yard."""
        table = self.query_one("#slipways-table", DataTable)
        table.clear()
        
        for slip in yard.slipways:
            status = "Occupied" if slip.active_order_id else "Free"
            eta = ""
            
            if slip.active_order_id:
                # Find the order for ETA calculation
                for order in yard.build_queue + yard.refit_queue:
                    if order.assigned_slipway_id == slip.id:
                        remaining_bp = order.total_bp - order.progress_bp
                        if yard.effective_bp_per_day() > 0:
                            days_remaining = remaining_bp / yard.effective_bp_per_day()
                            eta = f"{days_remaining:.1f} days"
                        break
            
            table.add_row(
                slip.id,
                f"{slip.max_hull_tonnage:,} tons",
                status,
                eta
            )

    def _update_queue_table(self, yard: Shipyard) -> None:
        """Update the build queue table for a yard."""
        table = self.query_one("#queue-table", DataTable)
        table.clear()
        
        # Add build orders
        for order in yard.build_queue:
            progress_pct = (order.progress_bp / order.total_bp * 100) if order.total_bp > 0 else 0
            status = "Assigned" if order.assigned_slipway_id else "Queued"
            if order.paused:
                status = "Paused"
                
            table.add_row(
                f"Build {order.id[:8]}",
                order.design_id,
                f"{progress_pct:.1f}%",
                str(order.priority if hasattr(order, 'priority') else 5),
                status,
                key=f"build_{order.id}"
            )
        
        # Add refit orders
        for order in yard.refit_queue:
            progress_pct = (order.progress_bp / order.total_bp * 100) if order.total_bp > 0 else 0
            status = "Assigned" if order.assigned_slipway_id else "Queued"
            if order.paused:
                status = "Paused"
                
            table.add_row(
                f"Refit {order.id[:8]}",
                f"{order.from_design_id} → {order.to_design_id}",
                f"{progress_pct:.1f}%",
                str(order.priority if hasattr(order, 'priority') else 5),
                status,
                key=f"refit_{order.id}"
            )

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle table row selection."""
        if event.data_table.id == "shipyards-table":
            # Yard selected
            self.current_yard_id = str(event.row_key)
            
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "new-yard":
            await self._show_new_yard_dialog()
        elif button_id == "upgrade-yard":
            await self._show_upgrade_yard_dialog()
        elif button_id == "add-order":
            await self._show_add_order_dialog()
        elif button_id == "cancel-order":
            await self._cancel_selected_order()
        elif button_id == "toggle-order":
            await self._toggle_selected_order()

    async def _show_new_yard_dialog(self) -> None:
        """Show dialog for creating a new yard."""
        # This would open a modal dialog for new yard creation
        # For now, just log the action
        logger.info("New yard dialog requested")

    async def _show_upgrade_yard_dialog(self) -> None:
        """Show dialog for upgrading a yard."""
        if not self.current_yard_id:
            return
        logger.info("Upgrade yard dialog requested for %s", self.current_yard_id)

    async def _show_add_order_dialog(self) -> None:
        """Show dialog for adding a build/refit order."""
        if not self.current_yard_id:
            return
        logger.info("Add order dialog requested for %s", self.current_yard_id)

    async def _cancel_selected_order(self) -> None:
        """Cancel the selected order."""
        # Get selected row from queue table
        queue_table = self.query_one("#queue-table", DataTable)
        if queue_table.cursor_row is None:
            return
            
        row_key = queue_table.get_row_at(queue_table.cursor_row)[0]
        logger.info("Cancel order requested: %s", row_key)

    async def _toggle_selected_order(self) -> None:
        """Toggle pause/resume for selected order."""
        queue_table = self.query_one("#queue-table", DataTable)
        if queue_table.cursor_row is None:
            return
            
        row_key = queue_table.get_row_at(queue_table.cursor_row)[0]  
        logger.info("Toggle order requested: %s", row_key)

    def set_empire(self, empire_id: str) -> None:
        """Set the current empire for display."""
        self.current_empire_id = empire_id

    def get_yard_summary(self, empire_id: str) -> Dict[str, Any]:
        """Get summary of yards for an empire."""
        if not self.simulation:
            return {}
            
        empire_yards = [
            yard for yard in self.simulation.shipyard_manager.yards.values()
            if yard.empire_id == empire_id
        ]
        
        total_slips = sum(len(yard.slipways) for yard in empire_yards)
        active_slips = sum(
            sum(1 for slip in yard.slipways if slip.active_order_id)
            for yard in empire_yards
        )
        total_queue = sum(len(yard.build_queue) + len(yard.refit_queue) for yard in empire_yards)
        
        return {
            "yards_count": len(empire_yards),
            "total_slipways": total_slips,
            "active_slipways": active_slips,
            "total_orders": total_queue,
            "total_bp_per_day": sum(yard.effective_bp_per_day() for yard in empire_yards)
        }

    def _ui_ready(self) -> bool:
        """Check whether the panel's widgets are available."""
        try:
            self.query_one("#shipyards-table", DataTable)
            self.query_one("#slipways-table", DataTable)
            self.query_one("#queue-table", DataTable)
            return True
        except NoMatches:
            return False

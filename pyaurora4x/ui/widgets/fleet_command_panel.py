"""
Enhanced Fleet Command Panel for PyAurora 4X

Provides comprehensive tactical fleet management including order management,
formation controls, combat displays, and real-time operational status.
"""

from typing import Optional, Dict, List, Any, Tuple
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, Grid
from textual.widgets import Static, Label, Button, DataTable, ProgressBar, Select, Input
from textual.reactive import reactive
from textual.message import Message
from textual.binding import Binding

from pyaurora4x.core.models import Fleet, Empire, Vector3D
from pyaurora4x.core.enums import (
    OrderType, OrderPriority, OrderStatus, FleetStatus, FleetFormation,
    CombatRole, WeaponType, DefenseType
)
from pyaurora4x.core.fleet_command import (
    FleetOrder, FormationTemplate, FleetCommandState, CombatEngagement
)
from pyaurora4x.engine.fleet_command_manager import FleetCommandManager
from pyaurora4x.core.events import EventManager, EventCategory, EventPriority


class FleetCommandPanel(Static):
    """
    Comprehensive fleet command interface for tactical operations.
    
    Features:
    - Fleet selection and status overview
    - Order management with priority queues
    - Formation control and tactical displays
    - Combat engagement monitoring
    - Logistics and supply status
    - Real-time tactical information
    """
    
    BINDINGS = [
        Binding("f", "formations", "Formations", show=True),
        Binding("o", "orders", "Orders", show=True),
        Binding("c", "combat", "Combat", show=True),
        Binding("l", "logistics", "Logistics", show=True),
        Binding("a", "attack", "Attack", show=True),
        Binding("m", "move", "Move", show=True),
        Binding("p", "patrol", "Patrol", show=True),
        Binding("escape", "cancel_order", "Cancel", show=True),
    ]
    
    selected_fleet = reactive(None)
    selected_empire = reactive(None)
    
    def __init__(self, fleet_command_manager: Optional[FleetCommandManager] = None,
                 event_manager: Optional[EventManager] = None, **kwargs):
        super().__init__(**kwargs)
        self.fleet_command_manager = fleet_command_manager
        self.event_manager = event_manager
        self.current_fleet: Optional[Fleet] = None
        self.current_empire: Optional[Empire] = None
        self.all_fleets: List[Fleet] = []
        
        # UI state
        self.selected_fleet_row: Optional[int] = None
        self.selected_order_row: Optional[int] = None
        self.tactical_view_mode: str = "overview"  # overview, formation, combat, logistics
    
    def compose(self) -> ComposeResult:
        """Compose the fleet command layout."""
        with Container(id="fleet_command_container"):
            yield Label("Fleet Command Center", classes="panel-title")
            
            with Horizontal(id="fleet_command_main_layout"):
                # Left panel - Fleet selection and overview
                with Vertical(id="fleet_selection_panel", classes="panel"):
                    yield Label("Fleet Selection", classes="section-title")
                    with Container(id="fleet_list_container"):
                        yield DataTable(id="fleet_list_table", classes="data-table")
                    
                    yield Label("Fleet Status", classes="section-title")
                    yield Static("", id="fleet_status", classes="info-section")
                    
                    yield Label("Quick Actions", classes="section-title")
                    with Horizontal(id="quick_actions"):
                        yield Button("Move", id="quick_move", variant="success")
                        yield Button("Attack", id="quick_attack", variant="error")
                        yield Button("Patrol", id="quick_patrol", variant="outline")
                        yield Button("Defend", id="quick_defend", variant="outline")
                
                # Center panel - Tactical display
                with Vertical(id="tactical_display_panel", classes="panel"):
                    yield Label("Tactical Display", classes="section-title")
                    
                    with Horizontal(id="tactical_view_controls"):
                        yield Button("Overview", id="view_overview", variant="primary")
                        yield Button("Formation", id="view_formation", variant="outline")
                        yield Button("Combat", id="view_combat", variant="outline")
                        yield Button("Logistics", id="view_logistics", variant="outline")
                    
                    with Container(id="tactical_display"):
                        yield Static("", id="tactical_overview", classes="tactical-display")
                        yield Static("", id="tactical_formation", classes="tactical-display hidden")
                        yield Static("", id="tactical_combat", classes="tactical-display hidden")
                        yield Static("", id="tactical_logistics", classes="tactical-display hidden")
                
                # Right panel - Orders and formations
                with Vertical(id="orders_panel", classes="panel"):
                    yield Label("Active Orders", classes="section-title")
                    with Container(id="orders_container"):
                        yield DataTable(id="orders_table", classes="data-table")
                    
                    with Horizontal(id="order_controls"):
                        yield Select(id="order_type_select", prompt="Select Order Type...")
                        yield Select(id="order_priority_select", prompt="Priority...")
                        yield Button("Issue", id="issue_order", variant="success")
                        yield Button("Cancel", id="cancel_order", variant="error")
                    
                    yield Label("Formation Control", classes="section-title")
                    with Container(id="formation_container"):
                        yield Select(id="formation_select", prompt="Select Formation...")
                        yield Button("Form Up", id="form_up", variant="primary")
                        yield Button("Break Formation", id="break_formation", variant="outline")
                        
                        # Formation status
                        yield Static("", id="formation_status", classes="info-section")
    
    def on_mount(self) -> None:
        """Initialize the fleet command panel."""
        self._setup_tables()
        self._setup_selects()
        self._update_display()
    
    def _setup_tables(self) -> None:
        """Setup data table columns."""
        # Fleet list table
        fleet_table = self.query_one("#fleet_list_table", DataTable)
        fleet_table.add_columns("Fleet", "Status", "Ships", "Formation", "Orders")
        fleet_table.cursor_type = "row"
        
        # Orders table
        orders_table = self.query_one("#orders_table", DataTable)
        orders_table.add_columns("Order", "Priority", "Status", "Progress", "ETA")
        orders_table.cursor_type = "row"
    
    def _setup_selects(self) -> None:
        """Setup select widgets with options."""
        # Order type select
        order_select = self.query_one("#order_type_select", Select)
        order_options = [
            (order_type.value.replace('_', ' ').title(), order_type.value)
            for order_type in OrderType
        ]
        order_select.set_options(order_options)
        
        # Priority select
        priority_select = self.query_one("#order_priority_select", Select)
        priority_options = [
            (priority.value.title(), priority.value)
            for priority in OrderPriority
        ]
        priority_select.set_options(priority_options)
        
        # Formation select
        formation_select = self.query_one("#formation_select", Select)
        if self.fleet_command_manager:
            formation_options = [
                (template.name, template.id)
                for template in self.fleet_command_manager.formation_templates.values()
            ]
            formation_select.set_options(formation_options)
    
    def update_fleets(self, fleets: List[Fleet], empire: Empire) -> None:
        """Update the displayed fleets and empire."""
        self.all_fleets = [f for f in fleets if f is not None]
        self.current_empire = empire
        self.selected_empire = empire
        
        # Initialize fleet command states if needed
        if self.fleet_command_manager:
            for fleet in self.all_fleets:
                if fleet.id not in self.fleet_command_manager.fleet_command_states:
                    self.fleet_command_manager.initialize_fleet_command(fleet, empire)
        
        self._refresh_fleet_table()
        
        # Select first fleet if none selected
        if self.all_fleets and not self.current_fleet:
            self.current_fleet = self.all_fleets[0]
            self.selected_fleet = self.current_fleet
            self._update_fleet_details()
    
    def _refresh_fleet_table(self) -> None:
        """Refresh the fleet list table."""
        fleet_table = self.query_one("#fleet_list_table", DataTable)
        fleet_table.clear()
        
        for fleet in self.all_fleets:
            # Get fleet command state
            command_state = None
            if self.fleet_command_manager:
                command_state = self.fleet_command_manager.fleet_command_states.get(fleet.id)
            
            # Format fleet data
            name = fleet.name
            status = self._format_fleet_status(fleet.status)
            ship_count = str(len(fleet.ships))
            
            # Formation status
            formation = "None"
            if command_state and command_state.formation_state:
                formation_state = command_state.formation_state
                if formation_state.is_formed:
                    template = self.fleet_command_manager.formation_templates.get(
                        formation_state.formation_template_id
                    )
                    formation = template.name if template else "Custom"
                else:
                    formation = "Forming..."
            
            # Active orders count
            orders_count = "0"
            if command_state:
                orders_count = str(len(command_state.current_orders))
            
            fleet_table.add_row(name, status, ship_count, formation, orders_count, key=fleet.id)
    
    def _format_fleet_status(self, status: FleetStatus) -> str:
        """Format fleet status with appropriate symbols."""
        status_symbols = {
            'idle': '⏸️ Idle',
            'moving': '🚀 Moving',
            'in_transit': '🌌 Transit',
            'in_formation': '📐 Formation',
            'forming_up': '⚡ Forming',
            'in_combat': '⚔️ Combat',
            'patrolling': '👁️ Patrol',
            'escorting': '🛡️ Escort',
            'surveying': '🔍 Survey',
            'repairing': '🔧 Repair',
            'refueling': '⛽ Refuel',
            'resupplying': '📦 Supply'
        }
        
        status_str = status.value if hasattr(status, 'value') else str(status)
        return status_symbols.get(status_str, f'❓ {status_str.title()}')
    
    def _update_display(self) -> None:
        """Update all display sections."""
        if not self.current_fleet or not self.current_empire or not self.fleet_command_manager:
            self._show_no_fleet_selected()
            return
        
        self._update_fleet_status()
        self._update_orders_table()
        self._update_tactical_display()
        self._update_formation_status()
    
    def _show_no_fleet_selected(self) -> None:
        """Show message when no fleet is selected."""
        try:
            status = self.query_one("#fleet_status", Static)
            status.update("No fleet selected")
            
            # Clear tables
            orders_table = self.query_one("#orders_table", DataTable)
            orders_table.clear()
            
            # Clear tactical displays
            for display_id in ["tactical_overview", "tactical_formation", "tactical_combat", "tactical_logistics"]:
                display = self.query_one(f"#{display_id}", Static)
                display.update("")
                
            formation_status = self.query_one("#formation_status", Static)
            formation_status.update("")
        except Exception:
            pass
    
    def _update_fleet_status(self) -> None:
        """Update fleet status information."""
        if not self.current_fleet or not self.fleet_command_manager:
            return
        
        fleet = self.current_fleet
        tactical_status = self.fleet_command_manager.get_fleet_tactical_status(fleet.id)
        
        if "error" in tactical_status:
            return
        
        lines = []
        lines.append(f"Fleet: {fleet.name}")
        lines.append(f"Status: {self._format_fleet_status(fleet.status)}")
        lines.append(f"Ships: {len(fleet.ships)}")
        lines.append(f"System: {fleet.system_id}")
        lines.append("")
        
        # Command effectiveness
        lines.append(f"Command Effectiveness: {tactical_status['command_effectiveness']:.1%}")
        lines.append(f"Active Orders: {tactical_status['current_orders']}")
        lines.append(f"Pending Orders: {tactical_status['pending_orders']}")
        lines.append("")
        
        # Formation status
        formation = tactical_status.get('formation', {})
        if formation.get('active'):
            lines.append(f"Formation: {formation.get('template', 'Unknown')}")
            lines.append(f"Integrity: {formation.get('integrity', 0):.1%}")
            lines.append(f"Cohesion: {formation.get('cohesion', 0):.1%}")
        else:
            lines.append("Formation: None")
        lines.append("")
        
        # Combat status
        combat = tactical_status.get('combat', {})
        lines.append(f"Combat Rating: {combat.get('combat_rating', 0):.1f}")
        lines.append(f"Experience: {combat.get('experience', 0):.1f}")
        lines.append(f"Morale: {combat.get('morale', 100):.0f}%")
        
        if combat.get('in_combat'):
            lines.append("⚔️ IN COMBAT")
        lines.append("")
        
        # Logistics status
        logistics = tactical_status.get('logistics', {})
        fuel_status = logistics.get('fuel_status', 1.0)
        lines.append(f"Fuel: {fuel_status:.1%}")
        
        maintenance_due = logistics.get('maintenance_due', 0.0)
        if maintenance_due > 0.7:
            lines.append("🔧 Maintenance Required")
        elif maintenance_due > 0.4:
            lines.append("⚠️ Maintenance Soon")
        else:
            lines.append("✅ Maintenance OK")
        
        text = "\\n".join(lines)
        
        try:
            status = self.query_one("#fleet_status", Static)
            status.update(text)
        except Exception:
            pass
    
    def _update_orders_table(self) -> None:
        """Update the active orders table."""
        orders_table = self.query_one("#orders_table", DataTable)
        orders_table.clear()
        
        if not self.current_fleet or not self.fleet_command_manager:
            return
        
        command_state = self.fleet_command_manager.fleet_command_states.get(self.current_fleet.id)
        if not command_state:
            return
        
        # Add orders to table in priority order
        for order_id in command_state.order_queue:
            order = command_state.current_orders.get(order_id)
            if not order:
                continue
            
            # Format order information
            order_name = order.order_type.value.replace('_', ' ').title()
            priority = order.priority.value.title()
            status = order.status.value.title()
            progress = f"{order.progress * 100:.1f}%"
            
            # ETA calculation (simplified)
            eta = "Unknown"
            if order.estimated_duration and order.progress > 0:
                remaining_time = order.estimated_duration * (1.0 - order.progress)
                if remaining_time < 60:
                    eta = f"{remaining_time:.0f}s"
                elif remaining_time < 3600:
                    eta = f"{remaining_time / 60:.1f}m"
                else:
                    eta = f"{remaining_time / 3600:.1f}h"
            
            orders_table.add_row(order_name, priority, status, progress, eta, key=order_id)
    
    def _update_tactical_display(self) -> None:
        """Update the tactical display based on current view mode."""
        if self.tactical_view_mode == "overview":
            self._update_tactical_overview()
        elif self.tactical_view_mode == "formation":
            self._update_tactical_formation()
        elif self.tactical_view_mode == "combat":
            self._update_tactical_combat()
        elif self.tactical_view_mode == "logistics":
            self._update_tactical_logistics()
    
    def _update_tactical_overview(self) -> None:
        """Update tactical overview display."""
        if not self.current_fleet or not self.fleet_command_manager:
            return
        
        tactical_status = self.fleet_command_manager.get_fleet_tactical_status(self.current_fleet.id)
        
        if "error" in tactical_status:
            return
        
        lines = []
        lines.append("=== FLEET TACTICAL OVERVIEW ===")
        lines.append("")
        
        fleet = self.current_fleet
        lines.append(f"Fleet: {fleet.name}")
        lines.append(f"Position: ({fleet.position.x:.0f}, {fleet.position.y:.0f}, {fleet.position.z:.0f})")
        lines.append(f"Ships: {len(fleet.ships)}")
        lines.append("")
        
        # Mission performance
        performance = tactical_status.get('performance', {})
        success_rate = performance.get('mission_success_rate', 0.0)
        total_missions = performance.get('total_missions', 0)
        lines.append(f"Mission Success Rate: {success_rate:.1%}")
        lines.append(f"Total Missions: {total_missions}")
        lines.append("")
        
        # Current status summary
        lines.append("Status Summary:")
        formation = tactical_status.get('formation', {})
        if formation.get('active'):
            lines.append(f"  Formation: {formation.get('template', 'Unknown')}")
        else:
            lines.append("  Formation: Independent Operation")
            
        combat = tactical_status.get('combat', {})
        if combat.get('in_combat'):
            lines.append("  Combat Status: ENGAGED")
        else:
            lines.append("  Combat Status: Ready")
            
        logistics = tactical_status.get('logistics', {})
        fuel_status = logistics.get('fuel_status', 1.0)
        if fuel_status < 0.3:
            lines.append("  Supply Status: CRITICAL - Refuel Required")
        elif fuel_status < 0.6:
            lines.append("  Supply Status: LOW - Consider Refueling")
        else:
            lines.append("  Supply Status: GOOD")
        
        text = "\\n".join(lines)
        
        try:
            overview = self.query_one("#tactical_overview", Static)
            overview.update(text)
        except Exception:
            pass
    
    def _update_tactical_formation(self) -> None:
        """Update formation tactical display."""
        if not self.current_fleet or not self.fleet_command_manager:
            return
        
        lines = []
        lines.append("=== FORMATION CONTROL ===")
        lines.append("")
        
        command_state = self.fleet_command_manager.fleet_command_states.get(self.current_fleet.id)
        if not command_state or not command_state.formation_state:
            lines.append("No active formation")
            lines.append("")
            lines.append("Available Formations:")
            for template in self.fleet_command_manager.formation_templates.values():
                lines.append(f"  {template.name}: {template.description}")
        else:
            formation_state = command_state.formation_state
            template = self.fleet_command_manager.formation_templates.get(
                formation_state.formation_template_id
            )
            
            if template:
                lines.append(f"Formation: {template.name}")
                lines.append(f"Description: {template.description}")
                lines.append("")
                lines.append(f"Status: {'Formed' if formation_state.is_formed else 'Forming'}")
                lines.append(f"Integrity: {formation_state.formation_integrity:.1%}")
                lines.append(f"Cohesion: {formation_state.formation_cohesion:.1%}")
                lines.append("")
                lines.append("Formation Effects:")
                lines.append(f"  Speed Modifier: {template.movement_speed_modifier:.1%}")
                lines.append(f"  Combat Effectiveness: {template.combat_effectiveness_modifier:.1%}")
                lines.append(f"  Detection Modifier: {template.detection_modifier:.1%}")
                if template.coordination_bonus > 0:
                    lines.append(f"  Coordination Bonus: +{template.coordination_bonus:.1%}")
        
        text = "\\n".join(lines)
        
        try:
            formation = self.query_one("#tactical_formation", Static)
            formation.update(text)
        except Exception:
            pass
    
    def _update_tactical_combat(self) -> None:
        """Update combat tactical display."""
        if not self.current_fleet or not self.fleet_command_manager:
            return
        
        lines = []
        lines.append("=== COMBAT STATUS ===")
        lines.append("")
        
        tactical_status = self.fleet_command_manager.get_fleet_tactical_status(self.current_fleet.id)
        combat = tactical_status.get('combat', {})
        
        lines.append(f"Combat Rating: {combat.get('combat_rating', 0):.1f}")
        lines.append(f"Experience Level: {combat.get('experience', 0):.1f}")
        lines.append(f"Morale: {combat.get('morale', 100):.0f}%")
        lines.append("")
        
        if combat.get('in_combat'):
            lines.append("🚨 FLEET IN COMBAT")
            lines.append("")
            # Would show detailed combat information here
            lines.append("Combat Engagement Active")
            lines.append("Tactical coordination in progress...")
        else:
            lines.append("Fleet ready for combat operations")
            lines.append("")
            lines.append("Available Combat Orders:")
            lines.append("  • Attack - Engage hostile forces")
            lines.append("  • Defend - Protect location or asset")
            lines.append("  • Escort - Provide protection")
            lines.append("  • Patrol - Area security sweep")
            lines.append("  • Blockade - Prevent movement")
        
        text = "\\n".join(lines)
        
        try:
            combat_display = self.query_one("#tactical_combat", Static)
            combat_display.update(text)
        except Exception:
            pass
    
    def _update_tactical_logistics(self) -> None:
        """Update logistics tactical display."""
        if not self.current_fleet or not self.fleet_command_manager:
            return
        
        lines = []
        lines.append("=== LOGISTICS STATUS ===")
        lines.append("")
        
        command_state = self.fleet_command_manager.fleet_command_states.get(self.current_fleet.id)
        if not command_state:
            lines.append("Logistics data unavailable")
        else:
            logistics = command_state.logistics_requirements
            
            # Fuel status
            fuel_percentage = logistics.current_fuel / logistics.fuel_capacity
            lines.append(f"Fuel Status: {fuel_percentage:.1%}")
            lines.append(f"Fuel Capacity: {logistics.fuel_capacity:.0f} units")
            lines.append(f"Consumption Rate: {logistics.fuel_consumption_rate:.1f} units/hour")
            
            # Operational range
            if logistics.fuel_consumption_rate > 0:
                operational_hours = logistics.current_fuel / logistics.fuel_consumption_rate
                lines.append(f"Operational Time: {operational_hours:.1f} hours")
            lines.append("")
            
            # Maintenance status
            maintenance_status = self.fleet_command_manager._calculate_maintenance_status(command_state)
            if maintenance_status > 0.8:
                lines.append("🔧 URGENT: Maintenance Required")
            elif maintenance_status > 0.6:
                lines.append("⚠️ WARNING: Maintenance Due Soon")
            elif maintenance_status > 0.3:
                lines.append("ℹ️ INFO: Maintenance Scheduled")
            else:
                lines.append("✅ GOOD: Maintenance Current")
            lines.append("")
            
            # Supply requirements
            lines.append("Supply Requirements:")
            lines.append(f"  Crew: {logistics.crew_requirements}")
            lines.append(f"  Maintenance Efficiency: {logistics.maintenance_efficiency:.1%}")
            
            # Supply lines
            if command_state.supply_lines:
                lines.append("")
                lines.append("Active Supply Lines:")
                for supply_id in command_state.supply_lines[:3]:
                    lines.append(f"  • Supply Point: {supply_id}")
            else:
                lines.append("")
                lines.append("⚠️ No active supply lines")
        
        text = "\\n".join(lines)
        
        try:
            logistics_display = self.query_one("#tactical_logistics", Static)
            logistics_display.update(text)
        except Exception:
            pass
    
    def _update_formation_status(self) -> None:
        """Update formation status display."""
        if not self.current_fleet or not self.fleet_command_manager:
            return
        
        command_state = self.fleet_command_manager.fleet_command_states.get(self.current_fleet.id)
        
        if not command_state or not command_state.formation_state:
            try:
                formation_status = self.query_one("#formation_status", Static)
                formation_status.update("No active formation")
            except Exception:
                pass
            return
        
        formation_state = command_state.formation_state
        template = self.fleet_command_manager.formation_templates.get(
            formation_state.formation_template_id
        )
        
        lines = []
        if template:
            lines.append(f"Formation: {template.name}")
            lines.append(f"Status: {'Formed' if formation_state.is_formed else 'Forming'}")
            lines.append(f"Integrity: {formation_state.formation_integrity:.1%}")
        else:
            lines.append("Formation: Unknown")
        
        text = "\\n".join(lines)
        
        try:
            formation_status = self.query_one("#formation_status", Static)
            formation_status.update(text)
        except Exception:
            pass
    
    # Event handlers
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle table row selections."""
        if event.data_table.id == "fleet_list_table":
            fleet_id = event.row_key
            self.current_fleet = next((f for f in self.all_fleets if f.id == fleet_id), None)
            if self.current_fleet:
                self.selected_fleet = self.current_fleet
                self._update_fleet_details()
        elif event.data_table.id == "orders_table":
            self.selected_order_row = event.row_index
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        # Quick action buttons
        if button_id == "quick_move":
            self._handle_quick_move()
        elif button_id == "quick_attack":
            self._handle_quick_attack()
        elif button_id == "quick_patrol":
            self._handle_quick_patrol()
        elif button_id == "quick_defend":
            self._handle_quick_defend()
        
        # Tactical view controls
        elif button_id in ["view_overview", "view_formation", "view_combat", "view_logistics"]:
            self._switch_tactical_view(button_id.replace("view_", ""))
        
        # Order management
        elif button_id == "issue_order":
            self._handle_issue_order()
        elif button_id == "cancel_order":
            self._handle_cancel_selected_order()
        
        # Formation controls
        elif button_id == "form_up":
            self._handle_form_up()
        elif button_id == "break_formation":
            self._handle_break_formation()
    
    def _update_fleet_details(self) -> None:
        """Update all fleet details when selection changes."""
        self._update_display()
    
    def _switch_tactical_view(self, view_mode: str) -> None:
        """Switch tactical display view."""
        self.tactical_view_mode = view_mode
        
        # Update button states
        for mode in ["overview", "formation", "combat", "logistics"]:
            button = self.query_one(f"#view_{mode}", Button)
            if mode == view_mode:
                button.variant = "primary"
            else:
                button.variant = "outline"
        
        # Show/hide appropriate displays
        for mode in ["overview", "formation", "combat", "logistics"]:
            display = self.query_one(f"#tactical_{mode}", Static)
            if mode == view_mode:
                display.remove_class("hidden")
            else:
                display.add_class("hidden")
        
        # Update the active display
        self._update_tactical_display()
    
    def _handle_quick_move(self) -> None:
        """Handle quick move action."""
        # Simplified move - for full implementation would show target selection
        if self.current_fleet and self.fleet_command_manager:
            target_pos = Vector3D(x=10000, y=5000, z=0)  # Example position
            success, message = self.fleet_command_manager.issue_order(
                fleet_id=self.current_fleet.id,
                order_type=OrderType.MOVE_TO,
                target_position=target_pos,
                priority=OrderPriority.NORMAL
            )
            self._show_order_result(success, message)
    
    def _handle_quick_attack(self) -> None:
        """Handle quick attack action."""
        if self.current_fleet and self.fleet_command_manager:
            success, message = self.fleet_command_manager.issue_order(
                fleet_id=self.current_fleet.id,
                order_type=OrderType.ATTACK,
                target_fleet_id="enemy_fleet_1",  # Example target
                priority=OrderPriority.HIGH
            )
            self._show_order_result(success, message)
    
    def _handle_quick_patrol(self) -> None:
        """Handle quick patrol action."""
        if self.current_fleet and self.fleet_command_manager:
            success, message = self.fleet_command_manager.issue_order(
                fleet_id=self.current_fleet.id,
                order_type=OrderType.PATROL,
                is_repeating=True,
                priority=OrderPriority.LOW
            )
            self._show_order_result(success, message)
    
    def _handle_quick_defend(self) -> None:
        """Handle quick defend action."""
        if self.current_fleet and self.fleet_command_manager:
            success, message = self.fleet_command_manager.issue_order(
                fleet_id=self.current_fleet.id,
                order_type=OrderType.DEFEND,
                priority=OrderPriority.NORMAL
            )
            self._show_order_result(success, message)
    
    def _handle_issue_order(self) -> None:
        """Handle issuing a custom order."""
        if not self.current_fleet or not self.fleet_command_manager:
            return
        
        # Get selected order type and priority
        order_select = self.query_one("#order_type_select", Select)
        priority_select = self.query_one("#order_priority_select", Select)
        
        if order_select.value is Select.BLANK or priority_select.value is Select.BLANK:
            self._show_order_result(False, "Please select order type and priority")
            return
        
        try:
            order_type = OrderType(order_select.value)
            priority = OrderPriority(priority_select.value)
            
            success, message = self.fleet_command_manager.issue_order(
                fleet_id=self.current_fleet.id,
                order_type=order_type,
                priority=priority
            )
            self._show_order_result(success, message)
        except ValueError as e:
            self._show_order_result(False, f"Invalid order parameters: {e}")
    
    def _handle_cancel_selected_order(self) -> None:
        """Handle cancelling the selected order."""
        if (not self.current_fleet or not self.fleet_command_manager or 
            self.selected_order_row is None):
            return
        
        orders_table = self.query_one("#orders_table", DataTable)
        if self.selected_order_row >= orders_table.row_count:
            return
        
        row_key = orders_table.get_row_at(self.selected_order_row).key
        if not row_key:
            return
        
        order_id = str(row_key)
        success = self.fleet_command_manager.cancel_order(self.current_fleet.id, order_id)
        
        if success:
            self._show_order_result(True, "Order cancelled successfully")
        else:
            self._show_order_result(False, "Failed to cancel order")
    
    def _handle_form_up(self) -> None:
        """Handle formation formation."""
        if not self.current_fleet or not self.fleet_command_manager:
            return
        
        formation_select = self.query_one("#formation_select", Select)
        if formation_select.value is Select.BLANK:
            self._show_order_result(False, "Please select a formation")
            return
        
        formation_id = formation_select.value
        success, message = self.fleet_command_manager.set_fleet_formation(
            self.current_fleet.id, formation_id
        )
        self._show_order_result(success, message)
    
    def _handle_break_formation(self) -> None:
        """Handle breaking formation."""
        if not self.current_fleet or not self.fleet_command_manager:
            return
        
        command_state = self.fleet_command_manager.fleet_command_states.get(self.current_fleet.id)
        if command_state and command_state.formation_state:
            command_state.formation_state.is_formed = False
            command_state.formation_state = None
            del self.fleet_command_manager.formation_states[self.current_fleet.id]
            self._show_order_result(True, "Formation broken")
        else:
            self._show_order_result(False, "No active formation to break")
    
    def _show_order_result(self, success: bool, message: str) -> None:
        """Show order result notification."""
        if self.event_manager and self.current_empire:
            category = EventCategory.FLEET if success else EventCategory.SYSTEM
            priority = EventPriority.NORMAL if success else EventPriority.HIGH
            self.event_manager.create_and_post_event(
                category=category,
                priority=priority,
                title="Fleet Order" if success else "Order Failed",
                description=message,
                timestamp=0.0,  # Would use current game time
                empire_id=self.current_empire.id
            )
        
        # Update displays to show changes
        self._update_display()
    
    # Action handlers for key bindings
    
    def action_formations(self) -> None:
        """Switch to formations view."""
        self._switch_tactical_view("formation")
    
    def action_orders(self) -> None:
        """Switch to orders view."""
        self._switch_tactical_view("overview")
    
    def action_combat(self) -> None:
        """Switch to combat view."""
        self._switch_tactical_view("combat")
    
    def action_logistics(self) -> None:
        """Switch to logistics view."""
        self._switch_tactical_view("logistics")
    
    def action_attack(self) -> None:
        """Issue attack order."""
        self._handle_quick_attack()
    
    def action_move(self) -> None:
        """Issue move order."""
        self._handle_quick_move()
    
    def action_patrol(self) -> None:
        """Issue patrol order."""
        self._handle_quick_patrol()
    
    def action_cancel_order(self) -> None:
        """Cancel selected order."""
        self._handle_cancel_selected_order()
    
    def watch_selected_fleet(self, fleet: Fleet) -> None:
        """React to fleet selection changes."""
        if fleet:
            self.current_fleet = fleet
            self._update_fleet_details()
    
    def watch_selected_empire(self, empire: Empire) -> None:
        """React to empire selection changes."""
        if empire:
            self.current_empire = empire

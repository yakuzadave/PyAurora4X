"""
Unit tests for FleetCommandPanel widget.

Tests fleet command UI functionality including fleet selection, order management,
formation control, and tactical display updates.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from textual.widgets import DataTable, Button, Select, Static

from pyaurora4x.ui.widgets.fleet_command_panel import FleetCommandPanel
from pyaurora4x.engine.fleet_command_manager import FleetCommandManager
from pyaurora4x.core.events import EventManager
from pyaurora4x.core.models import Fleet, Empire, Vector3D
from pyaurora4x.core.enums import (
    OrderType, OrderPriority, OrderStatus, FleetStatus, FleetFormation,
    CombatRole, WeaponType, DefenseType
)
from pyaurora4x.core.events import EventCategory, EventPriority
from pyaurora4x.core.fleet_command import (
    FleetOrder, FormationTemplate, FleetCommandState, FleetFormationState,
    CombatCapabilities, LogisticsRequirements
)


class TestFleetCommandPanel:
    """Test cases for FleetCommandPanel functionality."""
    
    @pytest.fixture
    def mock_fleet_command_manager(self):
        """Create a mock FleetCommandManager."""
        manager = Mock(spec=FleetCommandManager)
        
        # Mock formation templates
        formation_template = FormationTemplate(
            id="line_ahead",
            name="Line Ahead",
            formation_type=FleetFormation.LINE_AHEAD,
            description="Ships in line formation",
            movement_speed_modifier=1.1,
            combat_effectiveness_modifier=1.2,
            detection_modifier=1.0,
            coordination_bonus=0.1
        )
        manager.formation_templates = {"line_ahead": formation_template}
        
        # Mock fleet command states
        combat_capabilities = CombatCapabilities(
            combat_rating=50.0,
            total_firepower=100.0,
            total_defense=80.0,
            morale=95.0
        )
        
        logistics_requirements = LogisticsRequirements(
            fuel_capacity=1000.0,
            current_fuel=800.0,
            fuel_consumption_rate=2.0,
            crew_requirements=50,
            maintenance_efficiency=0.9
        )
        
        command_state = FleetCommandState(
            fleet_id="fleet1",
            flagship_id="ship1",
            command_effectiveness=0.85,
            combat_capabilities=combat_capabilities,
            logistics_requirements=logistics_requirements,
            mission_success_rate=0.75,
            total_missions=10,
            combat_experience=25.0
        )
        
        manager.fleet_command_states = {}
        
        # Mock methods
        manager.initialize_fleet_command.return_value = command_state
        manager.issue_order.return_value = (True, "Order issued successfully")
        manager.cancel_order.return_value = True
        manager.set_fleet_formation.return_value = (True, "Formation set successfully")
        
        # Mock tactical status
        tactical_status = {
            "fleet_id": "fleet1",
            "command_effectiveness": 0.85,
            "current_orders": 2,
            "pending_orders": 1,
            "formation": {
                "active": True,
                "template": "Line Ahead",
                "integrity": 0.9,
                "cohesion": 0.8
            },
            "combat": {
                "in_combat": False,
                "combat_rating": 50.0,
                "experience": 25.0,
                "morale": 95.0
            },
            "logistics": {
                "fuel_status": 0.8,
                "supply_status": {"fuel": 0.8, "ammunition": 0.9},
                "maintenance_due": 0.3
            },
            "performance": {
                "mission_success_rate": 0.75,
                "total_missions": 10
            }
        }
        manager.get_fleet_tactical_status.return_value = tactical_status
        
        return manager
    
    @pytest.fixture
    def mock_event_manager(self):
        """Create a mock EventManager."""
        event_manager = Mock(spec=EventManager)
        event_manager.create_and_post_event.return_value = None
        return event_manager
    
    @pytest.fixture
    def sample_fleet(self):
        """Create a sample fleet for testing."""
        fleet = Mock(spec=Fleet)
        fleet.id = "fleet1"
        fleet.name = "Test Fleet Alpha"
        fleet.ships = ["ship1", "ship2", "ship3"]
        fleet.status = FleetStatus.IDLE
        fleet.system_id = "system1"
        fleet.position = Vector3D(x=1000, y=2000, z=500)
        return fleet
    
    @pytest.fixture
    def sample_empire(self):
        """Create a sample empire for testing."""
        empire = Mock(spec=Empire)
        empire.id = "empire1"
        empire.name = "Test Empire"
        return empire
    
    @pytest.fixture
    def fleet_command_panel(self, mock_fleet_command_manager, mock_event_manager):
        """Create a FleetCommandPanel instance for testing."""
        panel = FleetCommandPanel(
            fleet_command_manager=mock_fleet_command_manager,
            event_manager=mock_event_manager
        )
        return panel
    
    def test_initialization(self, fleet_command_panel, mock_fleet_command_manager, mock_event_manager):
        """Test FleetCommandPanel initialization."""
        assert fleet_command_panel.fleet_command_manager == mock_fleet_command_manager
        assert fleet_command_panel.event_manager == mock_event_manager
        assert fleet_command_panel.current_fleet is None
        assert fleet_command_panel.current_empire is None
        assert fleet_command_panel.all_fleets == []
        assert fleet_command_panel.tactical_view_mode == "overview"
    
    @patch('pyaurora4x.ui.widgets.fleet_command_panel.FleetCommandPanel.query_one')
    def test_setup_tables(self, mock_query_one, fleet_command_panel):
        """Test table setup functionality."""
        # Mock DataTable instances
        mock_fleet_table = Mock(spec=DataTable)
        mock_orders_table = Mock(spec=DataTable)
        
        def side_effect(selector, widget_type):
            if selector == "#fleet_list_table":
                return mock_fleet_table
            elif selector == "#orders_table":
                return mock_orders_table
            return Mock()
        
        mock_query_one.side_effect = side_effect
        
        fleet_command_panel._setup_tables()
        
        # Verify fleet table setup
        mock_fleet_table.add_columns.assert_called_once_with("Fleet", "Status", "Ships", "Formation", "Orders")
        assert mock_fleet_table.cursor_type == "row"
        
        # Verify orders table setup
        mock_orders_table.add_columns.assert_called_once_with("Order", "Priority", "Status", "Progress", "ETA")
        assert mock_orders_table.cursor_type == "row"
    
    @patch('pyaurora4x.ui.widgets.fleet_command_panel.FleetCommandPanel.query_one')
    def test_setup_selects(self, mock_query_one, fleet_command_panel):
        """Test select widgets setup."""
        mock_order_select = Mock(spec=Select)
        mock_priority_select = Mock(spec=Select)
        mock_formation_select = Mock(spec=Select)
        
        def side_effect(selector, widget_type):
            if selector == "#order_type_select":
                return mock_order_select
            elif selector == "#order_priority_select":
                return mock_priority_select
            elif selector == "#formation_select":
                return mock_formation_select
            return Mock()
        
        mock_query_one.side_effect = side_effect
        
        fleet_command_panel._setup_selects()
        
        # Verify that set_options was called on all selects
        mock_order_select.set_options.assert_called_once()
        mock_priority_select.set_options.assert_called_once()
        mock_formation_select.set_options.assert_called_once()
    
    def test_update_fleets(self, fleet_command_panel, sample_fleet, sample_empire, mock_fleet_command_manager):
        """Test fleet data update functionality."""
        # Mock the refresh method
        with patch.object(fleet_command_panel, '_refresh_fleet_table') as mock_refresh, \
             patch.object(fleet_command_panel, '_update_fleet_details') as mock_update_details:
            
            fleet_command_panel.update_fleets([sample_fleet], sample_empire)
            
            assert fleet_command_panel.all_fleets == [sample_fleet]
            assert fleet_command_panel.current_empire == sample_empire
            assert fleet_command_panel.selected_empire == sample_empire
            assert fleet_command_panel.current_fleet == sample_fleet
            assert fleet_command_panel.selected_fleet == sample_fleet
            
            mock_refresh.assert_called_once()
            assert mock_update_details.call_count >= 1  # May be called multiple times during initialization
            mock_fleet_command_manager.initialize_fleet_command.assert_called_once_with(sample_fleet, sample_empire)
    
    def test_format_fleet_status(self, fleet_command_panel):
        """Test fleet status formatting."""
        # Test with enum value
        status_result = fleet_command_panel._format_fleet_status(FleetStatus.IDLE)
        assert "Idle" in status_result
        assert "⏸️" in status_result
        
        status_result = fleet_command_panel._format_fleet_status(FleetStatus.IN_COMBAT)
        assert "Combat" in status_result
        assert "⚔️" in status_result
        
        # Test with string value
        status_result = fleet_command_panel._format_fleet_status("moving")
        assert "Moving" in status_result or "❓" in status_result
    
    @patch('pyaurora4x.ui.widgets.fleet_command_panel.FleetCommandPanel.query_one')
    def test_refresh_fleet_table(self, mock_query_one, fleet_command_panel, sample_fleet, sample_empire, mock_fleet_command_manager):
        """Test fleet table refresh functionality."""
        mock_table = Mock(spec=DataTable)
        mock_query_one.return_value = mock_table
        
        # Setup fleet data
        fleet_command_panel.all_fleets = [sample_fleet]
        fleet_command_panel.fleet_command_manager = mock_fleet_command_manager
        
        fleet_command_panel._refresh_fleet_table()
        
        mock_table.clear.assert_called_once()
        mock_table.add_row.assert_called_once()
        
        # Check that the row was added with correct fleet ID as key
        call_args = mock_table.add_row.call_args
        assert call_args[1]['key'] == sample_fleet.id
    
    def test_switch_tactical_view(self, fleet_command_panel):
        """Test tactical view switching."""
        # Mock button and display queries
        with patch.object(fleet_command_panel, 'query_one') as mock_query_one, \
             patch.object(fleet_command_panel, '_update_tactical_display') as mock_update:
            
            # Mock buttons
            mock_buttons = {}
            mock_displays = {}
            
            for mode in ["overview", "formation", "combat", "logistics"]:
                mock_buttons[mode] = Mock(spec=Button)
                mock_displays[mode] = Mock(spec=Static)
            
            def query_side_effect(selector, widget_type=None):
                if selector.startswith("#view_"):
                    mode = selector.replace("#view_", "")
                    return mock_buttons.get(mode, Mock())
                elif selector.startswith("#tactical_"):
                    mode = selector.replace("#tactical_", "")
                    return mock_displays.get(mode, Mock())
                return Mock()
            
            mock_query_one.side_effect = query_side_effect
            
            fleet_command_panel._switch_tactical_view("combat")
            
            assert fleet_command_panel.tactical_view_mode == "combat"
            
            # Verify button variants were updated
            assert mock_buttons["combat"].variant == "primary"
            assert mock_buttons["overview"].variant == "outline"
            
            # Verify display visibility was updated
            mock_displays["combat"].remove_class.assert_called_with("hidden")
            mock_displays["overview"].add_class.assert_called_with("hidden")
            
            mock_update.assert_called_once()
    
    def test_handle_quick_move(self, fleet_command_panel, sample_fleet, mock_fleet_command_manager):
        """Test quick move command handling."""
        fleet_command_panel.current_fleet = sample_fleet
        fleet_command_panel.fleet_command_manager = mock_fleet_command_manager
        
        with patch.object(fleet_command_panel, '_show_order_result') as mock_show_result:
            fleet_command_panel._handle_quick_move()
            
            mock_fleet_command_manager.issue_order.assert_called_once()
            call_args = mock_fleet_command_manager.issue_order.call_args
            assert call_args[1]['fleet_id'] == sample_fleet.id
            assert call_args[1]['order_type'] == OrderType.MOVE_TO
            assert call_args[1]['priority'] == OrderPriority.NORMAL
            
            mock_show_result.assert_called_once_with(True, "Order issued successfully")
    
    def test_handle_quick_attack(self, fleet_command_panel, sample_fleet, mock_fleet_command_manager):
        """Test quick attack command handling."""
        fleet_command_panel.current_fleet = sample_fleet
        fleet_command_panel.fleet_command_manager = mock_fleet_command_manager
        
        with patch.object(fleet_command_panel, '_show_order_result') as mock_show_result:
            fleet_command_panel._handle_quick_attack()
            
            mock_fleet_command_manager.issue_order.assert_called_once()
            call_args = mock_fleet_command_manager.issue_order.call_args
            assert call_args[1]['fleet_id'] == sample_fleet.id
            assert call_args[1]['order_type'] == OrderType.ATTACK
            assert call_args[1]['priority'] == OrderPriority.HIGH
            
            mock_show_result.assert_called_once_with(True, "Order issued successfully")
    
    def test_handle_issue_order(self, fleet_command_panel, sample_fleet, mock_fleet_command_manager):
        """Test custom order issuance."""
        fleet_command_panel.current_fleet = sample_fleet
        fleet_command_panel.fleet_command_manager = mock_fleet_command_manager
        
        # Mock select widgets
        mock_order_select = Mock(spec=Select)
        mock_order_select.value = OrderType.PATROL.value
        
        mock_priority_select = Mock(spec=Select)
        mock_priority_select.value = OrderPriority.LOW.value
        
        with patch.object(fleet_command_panel, 'query_one') as mock_query_one, \
             patch.object(fleet_command_panel, '_show_order_result') as mock_show_result:
            
            def query_side_effect(selector, widget_type):
                if selector == "#order_type_select":
                    return mock_order_select
                elif selector == "#order_priority_select":
                    return mock_priority_select
                return Mock()
            
            mock_query_one.side_effect = query_side_effect
            
            fleet_command_panel._handle_issue_order()
            
            mock_fleet_command_manager.issue_order.assert_called_once()
            call_args = mock_fleet_command_manager.issue_order.call_args
            assert call_args[1]['fleet_id'] == sample_fleet.id
            assert call_args[1]['order_type'] == OrderType.PATROL
            assert call_args[1]['priority'] == OrderPriority.LOW
            
            mock_show_result.assert_called_once_with(True, "Order issued successfully")
    
    def test_handle_form_up(self, fleet_command_panel, sample_fleet, mock_fleet_command_manager):
        """Test formation setup handling."""
        fleet_command_panel.current_fleet = sample_fleet
        fleet_command_panel.fleet_command_manager = mock_fleet_command_manager
        
        mock_formation_select = Mock(spec=Select)
        mock_formation_select.value = "line_ahead"
        
        with patch.object(fleet_command_panel, 'query_one') as mock_query_one, \
             patch.object(fleet_command_panel, '_show_order_result') as mock_show_result:
            
            mock_query_one.return_value = mock_formation_select
            
            fleet_command_panel._handle_form_up()
            
            mock_fleet_command_manager.set_fleet_formation.assert_called_once_with(
                sample_fleet.id, "line_ahead"
            )
            mock_show_result.assert_called_once_with(True, "Formation set successfully")
    
    def test_handle_cancel_selected_order(self, fleet_command_panel, sample_fleet, mock_fleet_command_manager):
        """Test order cancellation handling."""
        fleet_command_panel.current_fleet = sample_fleet
        fleet_command_panel.fleet_command_manager = mock_fleet_command_manager
        fleet_command_panel.selected_order_row = 0
        
        mock_table = Mock(spec=DataTable)
        mock_table.row_count = 1
        mock_row = Mock()
        mock_row.key = "order123"
        mock_table.get_row_at.return_value = mock_row
        
        with patch.object(fleet_command_panel, 'query_one') as mock_query_one, \
             patch.object(fleet_command_panel, '_show_order_result') as mock_show_result:
            
            mock_query_one.return_value = mock_table
            
            fleet_command_panel._handle_cancel_selected_order()
            
            mock_fleet_command_manager.cancel_order.assert_called_once_with(sample_fleet.id, "order123")
            mock_show_result.assert_called_once_with(True, "Order cancelled successfully")
    
    def test_show_order_result_with_event_manager(self, fleet_command_panel, sample_empire, mock_event_manager):
        """Test order result notification with event manager."""
        fleet_command_panel.current_empire = sample_empire
        fleet_command_panel.event_manager = mock_event_manager
        
        with patch.object(fleet_command_panel, '_update_display') as mock_update:
            fleet_command_panel._show_order_result(True, "Test message")
            
            mock_event_manager.create_and_post_event.assert_called_once()
            call_args = mock_event_manager.create_and_post_event.call_args[1]
            assert call_args['category'] == EventCategory.FLEET
            assert call_args['priority'] == EventPriority.NORMAL
            assert call_args['title'] == "Fleet Order"
            assert call_args['description'] == "Test message"
            assert call_args['empire_id'] == sample_empire.id
            
            mock_update.assert_called_once()
    
    def test_show_order_result_failure(self, fleet_command_panel, sample_empire, mock_event_manager):
        """Test order result notification for failures."""
        fleet_command_panel.current_empire = sample_empire
        fleet_command_panel.event_manager = mock_event_manager
        
        with patch.object(fleet_command_panel, '_update_display') as mock_update:
            fleet_command_panel._show_order_result(False, "Error message")
            
            mock_event_manager.create_and_post_event.assert_called_once()
            call_args = mock_event_manager.create_and_post_event.call_args[1]
            assert call_args['category'] == EventCategory.SYSTEM
            assert call_args['priority'] == EventPriority.HIGH
            assert call_args['title'] == "Order Failed"
            assert call_args['description'] == "Error message"
    
    def test_action_handlers(self, fleet_command_panel):
        """Test keyboard shortcut action handlers."""
        with patch.object(fleet_command_panel, '_switch_tactical_view') as mock_switch, \
             patch.object(fleet_command_panel, '_handle_quick_attack') as mock_attack, \
             patch.object(fleet_command_panel, '_handle_quick_move') as mock_move, \
             patch.object(fleet_command_panel, '_handle_quick_patrol') as mock_patrol, \
             patch.object(fleet_command_panel, '_handle_cancel_selected_order') as mock_cancel:
            
            # Test view switching actions
            fleet_command_panel.action_formations()
            mock_switch.assert_called_with("formation")
            
            fleet_command_panel.action_combat()
            mock_switch.assert_called_with("combat")
            
            fleet_command_panel.action_logistics()
            mock_switch.assert_called_with("logistics")
            
            # Test order actions
            fleet_command_panel.action_attack()
            mock_attack.assert_called_once()
            
            fleet_command_panel.action_move()
            mock_move.assert_called_once()
            
            fleet_command_panel.action_patrol()
            mock_patrol.assert_called_once()
            
            fleet_command_panel.action_cancel_order()
            mock_cancel.assert_called_once()
    
    def test_reactive_property_watchers(self, fleet_command_panel, sample_fleet, sample_empire):
        """Test reactive property watch methods."""
        with patch.object(fleet_command_panel, '_update_fleet_details') as mock_update_details:
            fleet_command_panel.watch_selected_fleet(sample_fleet)
            assert fleet_command_panel.current_fleet == sample_fleet
            mock_update_details.assert_called_once()
        
        fleet_command_panel.watch_selected_empire(sample_empire)
        assert fleet_command_panel.current_empire == sample_empire
    
    @patch('pyaurora4x.ui.widgets.fleet_command_panel.FleetCommandPanel.query_one')
    def test_update_fleet_status_display(self, mock_query_one, fleet_command_panel, sample_fleet, mock_fleet_command_manager):
        """Test fleet status display updates."""
        fleet_command_panel.current_fleet = sample_fleet
        fleet_command_panel.fleet_command_manager = mock_fleet_command_manager
        
        mock_status_widget = Mock(spec=Static)
        mock_query_one.return_value = mock_status_widget
        
        fleet_command_panel._update_fleet_status()
        
        mock_fleet_command_manager.get_fleet_tactical_status.assert_called_once_with(sample_fleet.id)
        mock_status_widget.update.assert_called_once()
        
        # Verify the content includes fleet information
        call_args = mock_status_widget.update.call_args[0][0]
        assert sample_fleet.name in call_args
        assert "Command Effectiveness:" in call_args
        assert "Formation:" in call_args
        assert "Combat Rating:" in call_args
    
    @patch('pyaurora4x.ui.widgets.fleet_command_panel.FleetCommandPanel.query_one')
    def test_update_orders_table(self, mock_query_one, fleet_command_panel, sample_fleet, mock_fleet_command_manager):
        """Test orders table update functionality."""
        fleet_command_panel.current_fleet = sample_fleet
        fleet_command_panel.fleet_command_manager = mock_fleet_command_manager
        
        mock_table = Mock(spec=DataTable)
        mock_query_one.return_value = mock_table
        
        # Create mock orders and command state
        mock_order = Mock(spec=FleetOrder)
        mock_order.id = "order1"
        mock_order.order_type = OrderType.PATROL
        mock_order.priority = OrderPriority.NORMAL
        mock_order.status = OrderStatus.ACTIVE
        mock_order.progress = 0.3
        mock_order.estimated_duration = 300.0
        
        # Create command state for the fleet
        command_state = Mock()
        command_state.current_orders = {"order1": mock_order}
        command_state.order_queue = ["order1"]
        mock_fleet_command_manager.fleet_command_states = {sample_fleet.id: command_state}
        
        fleet_command_panel._update_orders_table()
        
        mock_table.clear.assert_called_once()
        mock_table.add_row.assert_called_once()
        
        # Verify order data formatting
        call_args = mock_table.add_row.call_args
        assert call_args[1]['key'] == "order1"
        row_data = call_args[0]
        assert "Patrol" in row_data[0]  # Order name
        assert "Normal" in row_data[1]  # Priority
        assert "Active" in row_data[2]  # Status
        assert "30.0%" in row_data[3]  # Progress

    def test_no_fleet_selected_handling(self, fleet_command_panel):
        """Test behavior when no fleet is selected."""
        with patch.object(fleet_command_panel, 'query_one') as mock_query_one:
            mock_status = Mock(spec=Static)
            mock_table = Mock(spec=DataTable)
            mock_formation = Mock(spec=Static)
            
            def query_side_effect(selector, widget_type):
                if selector == "#fleet_status":
                    return mock_status
                elif selector == "#orders_table":
                    return mock_table
                elif selector == "#formation_status":
                    return mock_formation
                else:
                    return Mock(spec=Static)
            
            mock_query_one.side_effect = query_side_effect
            
            fleet_command_panel._show_no_fleet_selected()
            
            mock_status.update.assert_called_with("No fleet selected")
            mock_table.clear.assert_called_once()
            mock_formation.update.assert_called_with("")


# Integration test class
class TestFleetCommandPanelIntegration:
    """Integration tests for FleetCommandPanel with real components."""
    
    def test_full_workflow_integration(self):
        """Test complete workflow from fleet selection to order issuance."""
        # This would be a more complex integration test
        # involving real FleetCommandManager and event handling
        # For now, we'll mark it as a placeholder for future implementation
        pass
    
    def test_formation_management_integration(self):
        """Test formation management workflow integration."""
        # Another integration test placeholder
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

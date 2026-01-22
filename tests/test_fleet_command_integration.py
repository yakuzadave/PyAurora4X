"""
Integration tests for Fleet Command Manager.

Tests documented workflows and examples from the Advanced Fleet Command guide,
ensuring that documented usage patterns work correctly.
"""

import pytest
from pyaurora4x.engine.fleet_command_manager import FleetCommandManager
from pyaurora4x.core.models import Fleet, Ship, Empire, Vector3D
from pyaurora4x.core.enums import (
    OrderType, OrderPriority, OrderStatus, FleetStatus, FleetFormation
)


class TestFleetCommandIntegration:
    """Integration tests for fleet command workflows."""
    
    @pytest.fixture
    def manager(self):
        """Create a FleetCommandManager instance."""
        return FleetCommandManager()
    
    @pytest.fixture
    def empire(self):
        """Create a test empire."""
        return Empire(
            id="test_empire",
            name="Test Empire",
            color="blue",
            home_system_id="sol",
            home_planet_id="earth"
        )
    
    @pytest.fixture
    def fleet(self):
        """Create a test fleet with ships."""
        ships = [
            Ship(
                id=f"ship_{i}",
                name=f"Test Ship {i}",
                design_id="test_design",
                empire_id="test_empire",
                position=Vector3D(x=0, y=0, z=0)
            )
            for i in range(5)
        ]
        
        return Fleet(
            id="test_fleet",
            name="Test Fleet",
            empire_id="test_empire",
            system_id="test_system",
            ships=[ship.id for ship in ships],
            position=Vector3D(x=0, y=0, z=0),
            status=FleetStatus.IDLE,
            commander_id=None
        )
    
    def test_basic_initialization(self, manager, fleet, empire):
        """Test fleet command initialization as documented."""
        # From documentation: Basic initialization
        command_state = manager.initialize_fleet_command(fleet, empire)
        
        assert command_state is not None
        assert command_state.fleet_id == fleet.id
        assert fleet.id in manager.fleet_command_states
        assert command_state.combat_capabilities is not None
        assert command_state.logistics_requirements is not None
    
    def test_move_order_workflow(self, manager, fleet, empire):
        """Test basic move order as documented in guide."""
        # Initialize fleet
        manager.initialize_fleet_command(fleet, empire)
        
        # From documentation: Basic Move Order
        target_pos = Vector3D(x=1000, y=0, z=500)
        success, msg = manager.issue_order(
            fleet_id=fleet.id,
            order_type=OrderType.MOVE_TO,
            parameters={"speed": 0.8},
            target_position=target_pos,
            priority=OrderPriority.NORMAL
        )
        
        assert success is True
        assert "successfully" in msg.lower()
        
        # Verify order was added
        command_state = manager.fleet_command_states[fleet.id]
        assert len(command_state.current_orders) == 1
        assert len(command_state.order_queue) == 1
        
        # Get the order
        order = list(command_state.current_orders.values())[0]
        assert order.order_type == OrderType.MOVE_TO
        assert order.priority == OrderPriority.NORMAL
        assert order.target_position == target_pos
        assert order.parameters["speed"] == 0.8
    
    def test_attack_order_workflow(self, manager, fleet, empire):
        """Test attack order as documented in guide."""
        # Initialize fleet
        manager.initialize_fleet_command(fleet, empire)
        
        # From documentation: Attack Order
        success, msg = manager.issue_order(
            fleet_id=fleet.id,
            order_type=OrderType.ATTACK,
            target_fleet_id="enemy_fleet_1",
            priority=OrderPriority.EMERGENCY
        )
        
        assert success is True
        
        # Verify order
        command_state = manager.fleet_command_states[fleet.id]
        order = list(command_state.current_orders.values())[0]
        assert order.order_type == OrderType.ATTACK
        assert order.priority == OrderPriority.EMERGENCY
        assert order.target_fleet_id == "enemy_fleet_1"
    
    def test_formation_setup(self, manager, fleet, empire):
        """Test formation setup as documented."""
        # Initialize fleet
        manager.initialize_fleet_command(fleet, empire)
        
        # From documentation: Setting a Formation
        success, msg = manager.set_fleet_formation(
            fleet_id=fleet.id,
            formation_template_id="line_ahead"
        )
        
        assert success is True
        
        # Verify formation state created
        assert fleet.id in manager.formation_states
        formation_state = manager.formation_states[fleet.id]
        assert formation_state.formation_template_id == "line_ahead"
        
        # Verify formation order was issued
        command_state = manager.fleet_command_states[fleet.id]
        assert len(command_state.current_orders) > 0
    
    def test_get_tactical_status(self, manager, fleet, empire):
        """Test getting fleet tactical status as documented."""
        # Initialize fleet
        manager.initialize_fleet_command(fleet, empire)
        
        # From documentation: Checking Fleet Status
        status = manager.get_fleet_tactical_status(fleet.id)
        
        # Verify status structure matches documentation
        assert "command_effectiveness" in status
        assert "current_orders" in status
        assert "pending_orders" in status
        assert "formation" in status
        assert "combat" in status
        assert "logistics" in status
        assert "performance" in status
        
        # Check formation sub-structure
        formation = status["formation"]
        assert "active" in formation
        assert "template" in formation
        assert "integrity" in formation
        assert "cohesion" in formation
        
        # Check combat sub-structure
        combat = status["combat"]
        assert "in_combat" in combat
        assert "combat_rating" in combat
        assert "experience" in combat
        assert "morale" in combat
        
        # Check logistics sub-structure
        logistics = status["logistics"]
        assert "fuel_status" in logistics
        assert "supply_status" in logistics
        assert "maintenance_due" in logistics
    
    def test_order_priority_sorting(self, manager, fleet, empire):
        """Test that orders are sorted by priority."""
        # Initialize fleet
        manager.initialize_fleet_command(fleet, empire)
        
        # Issue orders with different priorities
        manager.issue_order(
            fleet_id=fleet.id,
            order_type=OrderType.MOVE_TO,
            target_position=Vector3D(x=100, y=0, z=0),
            priority=OrderPriority.LOW
        )
        
        manager.issue_order(
            fleet_id=fleet.id,
            order_type=OrderType.ATTACK,
            target_fleet_id="enemy",
            priority=OrderPriority.EMERGENCY
        )
        
        manager.issue_order(
            fleet_id=fleet.id,
            order_type=OrderType.PATROL,
            parameters={},
            priority=OrderPriority.NORMAL
        )
        
        # Verify order queue is sorted by priority
        command_state = manager.fleet_command_states[fleet.id]
        orders = [command_state.current_orders[oid] for oid in command_state.order_queue]
        
        # Critical should be first
        assert orders[0].priority == OrderPriority.EMERGENCY
        # Low should be last
        assert orders[-1].priority == OrderPriority.LOW
    
    def test_cancel_order(self, manager, fleet, empire):
        """Test canceling orders as documented."""
        # Initialize fleet and issue order
        manager.initialize_fleet_command(fleet, empire)
        
        success, _ = manager.issue_order(
            fleet_id=fleet.id,
            order_type=OrderType.MOVE_TO,
            target_position=Vector3D(x=100, y=0, z=0),
            priority=OrderPriority.NORMAL
        )
        
        # Get order ID
        command_state = manager.fleet_command_states[fleet.id]
        order_id = list(command_state.current_orders.keys())[0]
        
        # Cancel order
        success = manager.cancel_order(fleet_id=fleet.id, order_id=order_id)
        
        assert success is True
        assert len(command_state.current_orders) == 0
        assert len(command_state.order_queue) == 0
    
    def test_patrol_order_with_waypoints(self, manager, fleet, empire):
        """Test patrol order with waypoints as documented."""
        # Initialize fleet
        manager.initialize_fleet_command(fleet, empire)
        
        # From documentation: System Defense Patrol
        patrol_waypoints = [
            Vector3D(x=0, y=0, z=0),
            Vector3D(x=1000, y=0, z=0),
            Vector3D(x=1000, y=0, z=1000),
        ]
        
        success, _ = manager.issue_order(
            fleet_id=fleet.id,
            order_type=OrderType.PATROL,
            parameters={
                "waypoints": patrol_waypoints,
                "patrol_speed": 0.6,
                "is_repeating": True
            },
            priority=OrderPriority.NORMAL
        )
        
        assert success is True
        
        # Verify order parameters
        command_state = manager.fleet_command_states[fleet.id]
        order = list(command_state.current_orders.values())[0]
        assert order.order_type == OrderType.PATROL
        assert order.parameters["waypoints"] == patrol_waypoints
        assert order.parameters["patrol_speed"] == 0.6
        assert order.parameters["is_repeating"] is True
    
    def test_escort_order(self, manager, fleet, empire):
        """Test escort order as documented."""
        # Initialize fleet
        manager.initialize_fleet_command(fleet, empire)
        
        # From documentation: Convoy Escort
        success, _ = manager.issue_order(
            fleet_id=fleet.id,
            order_type=OrderType.ESCORT,
            target_fleet_id="cargo_fleet",
            priority=OrderPriority.HIGH
        )
        
        assert success is True
        
        # Verify order
        command_state = manager.fleet_command_states[fleet.id]
        order = list(command_state.current_orders.values())[0]
        assert order.order_type == OrderType.ESCORT
        assert order.target_fleet_id == "cargo_fleet"
        assert order.priority == OrderPriority.HIGH
    
    def test_multiple_fleets(self, manager, empire):
        """Test managing multiple fleets simultaneously."""
        # Create multiple fleets
        fleets = []
        for i in range(3):
            fleet = Fleet(
                id=f"fleet_{i}",
                name=f"Fleet {i}",
                empire_id=empire.id,
                system_id="test_system",
                ships=[f"ship_{i}_0", f"ship_{i}_1"],
                position=Vector3D(x=i*1000, y=0, z=0),
                status=FleetStatus.IDLE
            )
            fleets.append(fleet)
            manager.initialize_fleet_command(fleet, empire)
        
        # Issue different orders to each fleet
        for i, fleet in enumerate(fleets):
            success, _ = manager.issue_order(
                fleet_id=fleet.id,
                order_type=OrderType.MOVE_TO,
                target_position=Vector3D(x=(i+1)*2000, y=0, z=0),
                priority=OrderPriority.NORMAL
            )
            assert success is True
        
        # Verify each fleet has independent state
        for fleet in fleets:
            command_state = manager.fleet_command_states[fleet.id]
            assert len(command_state.current_orders) == 1
            
            # Get status for each fleet
            status = manager.get_fleet_tactical_status(fleet.id)
            assert status["fleet_id"] == fleet.id
    
    def test_formation_integrity_reporting(self, manager, fleet, empire):
        """Test formation integrity reporting in status."""
        # Initialize and set formation
        manager.initialize_fleet_command(fleet, empire)
        manager.set_fleet_formation(fleet.id, "line_ahead")
        
        # Get status
        status = manager.get_fleet_tactical_status(fleet.id)
        formation = status["formation"]
        
        # Verify integrity and cohesion are reported
        assert isinstance(formation["integrity"], float)
        assert isinstance(formation["cohesion"], float)
        assert 0.0 <= formation["integrity"] <= 1.0
        assert 0.0 <= formation["cohesion"] <= 1.0
    
    def test_combat_engagement_setup(self, manager, fleet, empire):
        """Test setting up combat engagement as documented."""
        # Initialize fleets
        manager.initialize_fleet_command(fleet, empire)
        
        # Create enemy fleet (just for testing structure)
        enemy_fleet = Fleet(
            id="enemy_fleet",
            name="Enemy Fleet",
            empire_id="enemy_empire",
            system_id="test_system",
            ships=["enemy_ship_1"],
            position=Vector3D(x=500, y=0, z=0),
            status=FleetStatus.IDLE
        )
        manager.initialize_fleet_command(enemy_fleet, empire)
        
        # From documentation: Starting Combat
        engagement_id = manager.start_combat_engagement(
            attacking_fleet_ids=[fleet.id],
            defending_fleet_ids=[enemy_fleet.id],
            system_id="test_system"
        )
        
        assert engagement_id is not None
        assert engagement_id in manager.combat_engagements
        
        # Verify fleets are marked as in combat
        command_state = manager.fleet_command_states[fleet.id]
        assert command_state.current_engagement == engagement_id
    
    def test_uninit_fleet_error_handling(self, manager):
        """Test error handling for uninitialized fleet."""
        # Try to issue order to non-existent fleet
        success, msg = manager.issue_order(
            fleet_id="nonexistent_fleet",
            order_type=OrderType.MOVE_TO,
            target_position=Vector3D(x=100, y=0, z=0)
        )
        
        assert success is False
        assert "not initialized" in msg.lower()
        
        # Try to get status of non-existent fleet
        status = manager.get_fleet_tactical_status("nonexistent_fleet")
        assert "error" in status


class TestFleetCommandExamples:
    """Test specific examples from the documentation."""
    
    @pytest.fixture
    def setup(self):
        """Setup manager, empire, and fleet for examples."""
        manager = FleetCommandManager()
        empire = Empire(
            id="player_empire",
            name="Player Empire",
            color="blue",
            home_system_id="sol",
            home_planet_id="earth"
        )
        
        # Attack fleet
        attack_fleet = Fleet(
            id="attack_fleet",
            name="Attack Fleet",
            empire_id=empire.id,
            system_id="test_system",
            ships=["ship_1", "ship_2", "ship_3"],
            position=Vector3D(x=0, y=0, z=0),
            status=FleetStatus.IDLE
        )
        
        manager.initialize_fleet_command(attack_fleet, empire)
        
        return manager, empire, attack_fleet
    
    def test_search_and_destroy_mission(self, setup):
        """Test the Search and Destroy mission example from documentation."""
        manager, empire, fleet = setup
        
        # Example 1: Search and Destroy Mission
        # Step 1: Form up attack formation
        success, _ = manager.issue_order(
            fleet_id=fleet.id,
            order_type=OrderType.FORM_UP,
            parameters={"formation_template_id": "line_ahead"},
            priority=OrderPriority.HIGH
        )
        assert success is True
        
        # Step 2: Move to enemy system
        success, _ = manager.issue_order(
            fleet_id=fleet.id,
            order_type=OrderType.MOVE_TO,
            target_position=Vector3D(x=5000, y=0, z=0),
            parameters={"speed": 0.7},
            priority=OrderPriority.HIGH
        )
        assert success is True
        
        # Step 3: Attack enemy fleet
        success, _ = manager.issue_order(
            fleet_id=fleet.id,
            order_type=OrderType.ATTACK,
            target_fleet_id="enemy_defense_fleet",
            priority=OrderPriority.EMERGENCY
        )
        assert success is True
        
        # Step 4: Return to base
        success, _ = manager.issue_order(
            fleet_id=fleet.id,
            order_type=OrderType.MOVE_TO,
            target_position=Vector3D(x=0, y=0, z=0),
            parameters={"speed": 0.5},
            priority=OrderPriority.NORMAL
        )
        assert success is True
        
        # Verify all orders are in queue
        command_state = manager.fleet_command_states[fleet.id]
        assert len(command_state.current_orders) == 4
        
        # Verify order priorities are correct
        orders = [command_state.current_orders[oid] for oid in command_state.order_queue]
        assert orders[0].priority == OrderPriority.EMERGENCY  # Attack first
        assert orders[1].priority == OrderPriority.HIGH      # Form up second
        assert orders[-1].priority == OrderPriority.NORMAL   # Return last

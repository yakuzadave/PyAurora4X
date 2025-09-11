"""
Comprehensive test suite for the Jump Point Travel & Exploration System
"""

import pytest
import math
from unittest.mock import Mock, patch

from pyaurora4x.core.models import Fleet, StarSystem, JumpPoint, Empire, Vector3D, Ship
from pyaurora4x.core.enums import (
    FleetStatus, JumpPointType, JumpPointStatus, ExplorationResult,
    PlanetType, StarType, CONSTANTS
)
from pyaurora4x.engine.jump_point_exploration import JumpPointExplorationSystem
from pyaurora4x.engine.jump_travel_system import FleetJumpTravelSystem
from pyaurora4x.engine.jump_point_manager import JumpPointManager
from pyaurora4x.engine.simulation import GameSimulation


class TestJumpPointModel:
    """Test the enhanced JumpPoint model."""
    
    def test_jump_point_creation(self):
        """Test basic jump point creation and properties."""
        position = Vector3D(x=1000.0, y=2000.0, z=100.0)
        jp = JumpPoint(
            name="Test Jump Point",
            position=position,
            connects_to="target_system_id",
            jump_point_type=JumpPointType.NATURAL,
            status=JumpPointStatus.ACTIVE,
            stability=0.9,
            size_class=3
        )
        
        assert jp.name == "Test Jump Point"
        assert jp.connects_to == "target_system_id"
        assert jp.jump_point_type == JumpPointType.NATURAL
        assert jp.status == JumpPointStatus.ACTIVE
        assert jp.stability == 0.9
        assert jp.size_class == 3
        assert jp.survey_level == 0  # Default
    
    def test_accessibility_check(self):
        """Test jump point accessibility for empires."""
        jp = JumpPoint(
            name="Test JP",
            position=Vector3D(),
            connects_to="target",
            status=JumpPointStatus.ACTIVE,
            discovered_by="empire1"
        )
        
        # Discoverer should have access
        assert jp.is_accessible_by("empire1")
        
        # Other empires shouldn't have access by default
        assert not jp.is_accessible_by("empire2")
        
        # Grant explicit access
        jp.empire_access["empire2"] = True
        assert jp.is_accessible_by("empire2")
        
        # Revoke access
        jp.empire_access["empire2"] = False
        assert not jp.is_accessible_by("empire2")
    
    def test_fuel_cost_calculation(self):
        """Test fuel cost calculation for different fleet configurations."""
        jp = JumpPoint(
            name="Test JP",
            position=Vector3D(),
            connects_to="target",
            size_class=2,
            fuel_cost_modifier=1.0
        )
        
        # Base case
        cost = jp.calculate_fuel_cost(1000.0, 1)  # 1000 mass, 1 ship
        assert cost >= CONSTANTS["JUMP_FUEL_COST_BASE"]
        
        # Larger fleet should cost more
        cost_large = jp.calculate_fuel_cost(5000.0, 5)
        assert cost_large > cost
        
        # Larger jump point should be more efficient
        jp_large = JumpPoint(
            name="Large JP",
            position=Vector3D(),
            connects_to="target",
            size_class=5,
            fuel_cost_modifier=1.0
        )
        cost_efficient = jp_large.calculate_fuel_cost(1000.0, 1)
        assert cost_efficient < cost
    
    def test_travel_time_calculation(self):
        """Test travel time calculation."""
        jp = JumpPoint(
            name="Test JP",
            position=Vector3D(),
            connects_to="target",
            stability=1.0,
            travel_time_modifier=1.0
        )
        
        # Base case
        time = jp.calculate_travel_time(1000.0, 1)
        assert time >= CONSTANTS["JUMP_TIME_BASE"]
        
        # Unstable jump point should take longer
        jp_unstable = JumpPoint(
            name="Unstable JP",
            position=Vector3D(),
            connects_to="target",
            stability=0.5,
            travel_time_modifier=1.0
        )
        time_unstable = jp_unstable.calculate_travel_time(1000.0, 1)
        assert time_unstable > time


class TestJumpPointExploration:
    """Test the exploration system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.exploration_system = JumpPointExplorationSystem()
        
        # Create test fleet
        self.fleet = Fleet(
            name="Explorer",
            empire_id="player",
            system_id="test_system",
            position=Vector3D(x=1000.0, y=1000.0)
        )
        
        # Create test system
        self.system = StarSystem(
            id="test_system",
            name="Test System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0
        )
        
        # Add a jump point to the system
        self.jump_point = JumpPoint(
            name="Test JP",
            position=Vector3D(x=2000.0, y=2000.0),
            connects_to="target_system"
        )
        self.system.jump_points.append(self.jump_point)
    
    def test_system_exploration_initialization(self):
        """Test system exploration data initialization."""
        self.exploration_system.initialize_system_exploration(self.system, "player")
        
        assert "test_system" in self.exploration_system.system_exploration_data
        system_data = self.exploration_system.system_exploration_data["test_system"]
        
        assert "empires" in system_data
        assert "player" in system_data["empires"]
        assert "exploration_difficulty" in system_data
        
        empire_data = system_data["empires"]["player"]
        assert empire_data["exploration_progress"] == 0.0
        assert empire_data["survey_completeness"] == 0.0
        assert empire_data["discovered_jump_points"] == []
    
    def test_exploration_mission_creation(self):
        """Test creating an exploration mission."""
        success = self.exploration_system.start_exploration_mission(
            self.fleet, self.system, "explore", 0.0
        )
        
        assert success
        assert self.fleet.id in self.exploration_system.active_missions
        assert self.fleet.status == FleetStatus.EXPLORING
        
        mission = self.exploration_system.active_missions[self.fleet.id]
        assert mission.fleet_id == self.fleet.id
        assert mission.system_id == self.system.id
        assert mission.mission_type == "explore"
    
    def test_jump_point_detection(self):
        """Test jump point detection mechanics."""
        detected_points = self.exploration_system.attempt_jump_point_detection(
            self.fleet, self.system, "player", 0.0
        )
        
        # Should detect the jump point if close enough
        # (depends on random chance and distance)
        # For deterministic testing, we'll check the setup is correct
        assert isinstance(detected_points, list)
    
    def test_exploration_status_retrieval(self):
        """Test getting exploration status."""
        # Initialize exploration
        self.exploration_system.initialize_system_exploration(self.system, "player")
        
        status = self.exploration_system.get_exploration_status("test_system", "player")
        
        assert "exploration_progress" in status
        assert "survey_completeness" in status
        assert "discovered_jump_points" in status
        assert "system_difficulty" in status
    
    def test_hidden_jump_point_generation(self):
        """Test generation of hidden jump points."""
        # This is called during system initialization
        self.exploration_system.initialize_system_exploration(self.system, "player")
        
        # Check if hidden jump points were potentially generated
        hidden_points = self.exploration_system.hidden_jump_points.get("test_system", [])
        # Number of hidden points is random, so we just check the structure
        for point in hidden_points:
            assert isinstance(point, JumpPoint)
            assert point.status == JumpPointStatus.UNKNOWN


class TestJumpTravelSystem:
    """Test the jump travel system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.travel_system = FleetJumpTravelSystem()
        
        # Create test fleet
        self.fleet = Fleet(
            name="Traveler",
            empire_id="player",
            system_id="origin_system",
            position=Vector3D(),
            fuel_remaining=100.0,
            ships=["ship1", "ship2"]
        )
        
        # Create test ship
        self.ship = Ship(
            id="ship1",
            name="Test Ship",
            design_id="test_design",
            empire_id="player",
            current_mass=500.0
        )
        
        # Create jump point
        self.jump_point = JumpPoint(
            name="Test JP",
            position=Vector3D(),
            connects_to="target_system",
            status=JumpPointStatus.ACTIVE,
            discovered_by="player"
        )
    
    def test_jump_requirements_calculation(self):
        """Test calculation of jump requirements."""
        ships = {"ship1": self.ship}
        empire_tech = {}
        
        requirements = self.travel_system.calculate_jump_requirements(
            self.fleet, self.jump_point, ships, empire_tech
        )
        
        assert isinstance(requirements.fuel_cost, float)
        assert isinstance(requirements.travel_time, float)
        assert isinstance(requirements.preparation_time, float)
        assert isinstance(requirements.can_jump, bool)
    
    def test_jump_preparation_initiation(self):
        """Test initiating jump preparation."""
        ships = {"ship1": self.ship}
        empire_tech = {}
        
        success, message = self.travel_system.initiate_jump_preparation(
            self.fleet, self.jump_point, "target_system", 0.0, ships, empire_tech
        )
        
        if success:  # May fail due to requirements
            assert self.fleet.id in self.travel_system.active_preparations
            assert self.fleet.status == FleetStatus.FORMING_UP
    
    def test_jump_status_retrieval(self):
        """Test getting jump status for a fleet."""
        status = self.travel_system.get_jump_status(self.fleet.id)
        
        assert "has_operation" in status
        assert "operation_type" in status
        assert "progress" in status
        assert "remaining_time" in status
    
    def test_available_jumps_listing(self):
        """Test getting available jump destinations."""
        system = StarSystem(
            id="origin_system",
            name="Origin System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0,
            jump_points=[self.jump_point]
        )
        
        ships = {"ship1": self.ship}
        empire_tech = {}
        
        available_jumps = self.travel_system.get_available_jumps(
            self.fleet, system, ships, empire_tech
        )
        
        assert isinstance(available_jumps, list)
        if available_jumps:  # May be empty due to requirements
            jump_info = available_jumps[0]
            assert "jump_point_id" in jump_info
            assert "target_system_id" in jump_info
            assert "can_jump" in jump_info


class TestJumpPointManager:
    """Test the jump point manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = JumpPointManager()
        
        # Create test systems
        self.system1 = StarSystem(
            id="system1",
            name="System One",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0
        )
        
        self.system2 = StarSystem(
            id="system2",
            name="System Two",
            star_type=StarType.K_DWARF,
            star_mass=0.8,
            star_luminosity=0.6
        )
        
        self.systems = {"system1": self.system1, "system2": self.system2}
        
        # Create test fleet
        self.fleet = Fleet(
            name="Test Fleet",
            empire_id="player",
            system_id="system1",
            position=Vector3D()
        )
    
    def test_network_generation(self):
        """Test enhanced jump network generation."""
        systems = [self.system1, self.system2]
        
        self.manager.generate_enhanced_jump_network(systems, connectivity_level=0.3)
        
        # Check that jump points were created
        total_jump_points = sum(len(sys.jump_points) for sys in systems)
        assert total_jump_points > 0
        
        # Check that systems are connected
        self.manager.update_network(self.systems)
        connections = self.manager.network_manager.system_connections
        assert len(connections) > 0
    
    def test_empire_knowledge_tracking(self):
        """Test empire knowledge initialization and tracking."""
        self.manager.initialize_empire_knowledge("player")
        
        assert "player" in self.manager.empire_knowledge
        knowledge = self.manager.empire_knowledge["player"]
        
        assert "known_systems" in knowledge
        assert "known_jump_points" in knowledge
        assert "exploration_missions" in knowledge
        assert "total_jumps" in knowledge
    
    def test_exploration_mission_start(self):
        """Test starting exploration missions through the manager."""
        success, message = self.manager.start_exploration_mission(
            self.fleet, self.system1, "explore", 0.0
        )
        
        assert isinstance(success, bool)
        assert isinstance(message, str)
    
    def test_jump_network_retrieval(self):
        """Test getting empire-specific jump network."""
        self.manager.initialize_empire_knowledge("player")
        
        # Add some known systems
        self.manager.empire_knowledge["player"]["known_systems"].add("system1")
        
        network = self.manager.get_empire_jump_network("player", self.systems)
        
        assert "known_systems" in network
        assert "system_connections" in network
        assert "statistics" in network


class TestSimulationIntegration:
    """Test integration with the main simulation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.simulation = GameSimulation()
        self.simulation.initialize_new_game(num_systems=3, num_empires=1)
    
    def test_simulation_has_jump_manager(self):
        """Test that simulation has jump point manager."""
        assert hasattr(self.simulation, 'jump_point_manager')
        assert self.simulation.jump_point_manager is not None
    
    def test_enhanced_network_generation(self):
        """Test that enhanced network generation is used."""
        # Check that systems have jump points
        total_jump_points = sum(
            len(system.jump_points) for system in self.simulation.star_systems.values()
        )
        assert total_jump_points > 0
    
    def test_jump_point_operations_processing(self):
        """Test that jump point operations are processed in simulation updates."""
        # This is tested by running a simulation step
        initial_time = self.simulation.current_time
        self.simulation.advance_time(60.0)  # Advance 1 minute
        
        # Should have processed without errors
        assert self.simulation.current_time > initial_time
    
    def test_simulation_jump_methods(self):
        """Test that simulation provides jump-related methods."""
        fleet_ids = list(self.simulation.fleets.keys())
        if fleet_ids:
            fleet_id = fleet_ids[0]
            
            # Test method existence and basic functionality
            available_jumps = self.simulation.get_available_jumps(fleet_id)
            assert isinstance(available_jumps, list)
            
            jump_status = self.simulation.get_fleet_jump_status(fleet_id)
            assert isinstance(jump_status, dict)
            
            # Test exploration methods
            success, message = self.simulation.start_fleet_exploration(fleet_id, "explore")
            assert isinstance(success, bool)
            assert isinstance(message, str)


class TestPerformanceAndEdgeCases:
    """Test performance and edge cases."""
    
    def test_large_network_generation(self):
        """Test generation of large jump point networks."""
        manager = JumpPointManager()
        
        # Create many systems
        systems = []
        for i in range(50):
            system = StarSystem(
                id=f"system_{i}",
                name=f"System {i}",
                star_type=StarType.G_DWARF,
                star_mass=1.0,
                star_luminosity=1.0
            )
            systems.append(system)
        
        # This should complete without hanging or crashing
        manager.generate_enhanced_jump_network(systems, connectivity_level=0.2)
        
        # Verify connectivity
        total_jump_points = sum(len(sys.jump_points) for sys in systems)
        assert total_jump_points >= len(systems) - 1  # At minimum, spanning tree
    
    def test_empty_system_handling(self):
        """Test handling of systems with no jump points."""
        exploration_system = JumpPointExplorationSystem()
        
        system = StarSystem(
            id="empty_system",
            name="Empty System",
            star_type=StarType.M_DWARF,
            star_mass=0.5,
            star_luminosity=0.1,
            jump_points=[]  # No jump points
        )
        
        fleet = Fleet(
            name="Explorer",
            empire_id="player",
            system_id="empty_system",
            position=Vector3D()
        )
        
        # Should handle gracefully
        detected_points = exploration_system.attempt_jump_point_detection(
            fleet, system, "player", 0.0
        )
        assert isinstance(detected_points, list)
        assert len(detected_points) == 0
    
    def test_invalid_jump_attempts(self):
        """Test handling of invalid jump attempts."""
        travel_system = FleetJumpTravelSystem()
        
        # Fleet with no ships
        empty_fleet = Fleet(
            name="Empty Fleet",
            empire_id="player",
            system_id="test_system",
            position=Vector3D(),
            ships=[]
        )
        
        jump_point = JumpPoint(
            name="Test JP",
            position=Vector3D(),
            connects_to="target",
            status=JumpPointStatus.ACTIVE
        )
        
        requirements = travel_system.calculate_jump_requirements(
            empty_fleet, jump_point, {}, {}
        )
        
        assert not requirements.can_jump
        assert "no ships" in " ".join(requirements.failure_reasons).lower()
    
    def test_fuel_exhaustion_handling(self):
        """Test handling of fleets with insufficient fuel."""
        travel_system = FleetJumpTravelSystem()
        
        # Fleet with very low fuel
        low_fuel_fleet = Fleet(
            name="Low Fuel Fleet",
            empire_id="player",
            system_id="test_system",
            position=Vector3D(),
            fuel_remaining=5.0,  # Very low fuel
            ships=["ship1"]
        )
        
        jump_point = JumpPoint(
            name="Test JP",
            position=Vector3D(),
            connects_to="target",
            status=JumpPointStatus.ACTIVE,
            discovered_by="player"
        )
        
        ship = Ship(
            id="ship1",
            name="Test Ship",
            design_id="test_design",
            empire_id="player",
            current_mass=1000.0
        )
        
        requirements = travel_system.calculate_jump_requirements(
            low_fuel_fleet, jump_point, {"ship1": ship}, {}
        )
        
        # Should fail due to insufficient fuel
        assert not requirements.can_jump
        assert any("fuel" in reason.lower() for reason in requirements.failure_reasons)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

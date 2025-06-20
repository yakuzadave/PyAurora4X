"""
Unit tests for PyAurora 4X simulation engine

Tests the core game simulation logic and state management.
"""

from unittest.mock import Mock, patch


from pyaurora4x.core.enums import FleetStatus, PlanetType, StarType
from pyaurora4x.core.models import Planet, StarSystem, Vector3D
from pyaurora4x.engine.simulation import GameSimulation


class TestGameSimulation:
    """Test the GameSimulation class."""

    def test_simulation_initialization(self):
        """Test simulation initialization."""
        sim = GameSimulation()

        assert sim.current_time == 0.0
        assert sim.time_acceleration == 1.0
        assert len(sim.empires) == 0
        assert len(sim.star_systems) == 0
        assert len(sim.fleets) == 0
        assert not sim.is_running
        assert not sim.is_paused

    def test_new_game_initialization(self):
        """Test new game initialization."""
        sim = GameSimulation()
        sim.initialize_new_game(num_systems=2, num_empires=2)

        assert sim.is_running
        assert len(sim.star_systems) == 2
        assert len(sim.empires) == 2

        # Check that a player empire exists
        player_empire = sim.get_player_empire()
        assert player_empire is not None
        assert player_empire.is_player

        # Check that AI empires exist
        ai_empires = [emp for emp in sim.empires.values() if not emp.is_player]
        assert len(ai_empires) == 1  # num_empires includes player

    def test_time_advancement(self):
        """Test time advancement."""
        sim = GameSimulation()
        sim.initialize_new_game()

        initial_time = sim.current_time
        sim.advance_time(100.0)

        assert sim.current_time == initial_time + 100.0

    def test_pause_resume(self):
        """Test pause and resume functionality."""
        sim = GameSimulation()
        sim.initialize_new_game()

        assert not sim.is_paused

        sim.pause()
        assert sim.is_paused

        # Time advancement should not work when paused
        initial_time = sim.current_time
        sim.advance_time(100.0)
        assert sim.current_time == initial_time

        sim.resume()
        assert not sim.is_paused

        # Time advancement should work again
        sim.advance_time(100.0)
        assert sim.current_time == initial_time + 100.0

    def test_stop_simulation(self):
        """Test stopping the simulation."""
        sim = GameSimulation()
        sim.initialize_new_game()

        assert sim.is_running

        sim.stop()
        assert not sim.is_running
        assert not sim.is_paused

    def test_empire_retrieval(self):
        """Test empire retrieval methods."""
        sim = GameSimulation()
        sim.initialize_new_game()

        # Test get_player_empire
        player_empire = sim.get_player_empire()
        assert player_empire is not None
        assert player_empire.is_player

        # Test get_empire
        empire = sim.get_empire(player_empire.id)
        assert empire is player_empire

        # Test non-existent empire
        assert sim.get_empire("non_existent") is None

    def test_star_system_retrieval(self):
        """Test star system retrieval."""
        sim = GameSimulation()
        sim.initialize_new_game()

        # Get a system
        system_id = list(sim.star_systems.keys())[0]
        system = sim.get_system(system_id)

        assert system is not None
        assert system.id == system_id

        # Test non-existent system
        assert sim.get_system("non_existent") is None

    def test_fleet_retrieval(self):
        """Test fleet retrieval."""
        sim = GameSimulation()
        sim.initialize_new_game()

        # Should have at least one fleet (player's initial fleet)
        assert len(sim.fleets) > 0

        fleet_id = list(sim.fleets.keys())[0]
        fleet = sim.get_fleet(fleet_id)

        assert fleet is not None
        assert fleet.id == fleet_id

        # Test non-existent fleet
        assert sim.get_fleet("non_existent") is None

    def test_game_state_serialization(self):
        """Test game state serialization."""
        sim = GameSimulation()
        sim.initialize_new_game()

        # Advance time to have some state
        sim.advance_time(1000.0)

        game_state = sim.get_game_state()

        assert "current_time" in game_state
        assert "empires" in game_state
        assert "star_systems" in game_state
        assert "fleets" in game_state
        assert game_state["current_time"] == 1000.0

    def test_game_state_loading(self):
        """Test game state loading."""
        # Create initial simulation
        sim1 = GameSimulation()
        sim1.initialize_new_game()
        sim1.advance_time(500.0)

        game_state = sim1.get_game_state()

        # Create new simulation and load state
        sim2 = GameSimulation()
        sim2.load_game_state(game_state)

        assert sim2.current_time == 500.0
        assert len(sim2.empires) == len(sim1.empires)
        assert len(sim2.star_systems) == len(sim1.star_systems)
        assert len(sim2.fleets) == len(sim1.fleets)
        assert sim2.is_running

    @patch("pyaurora4x.engine.simulation.StarSystemGenerator")
    def test_star_system_generation(self, mock_generator):
        """Test star system generation."""
        # Mock the generator
        mock_instance = Mock()
        mock_generator.return_value = mock_instance

        mock_system = StarSystem(
            name="Mock System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0,
            planets=[
                Planet(
                    name="Home",
                    planet_type=PlanetType.TERRESTRIAL,
                    mass=1.0,
                    radius=1.0,
                    surface_temperature=288.0,
                    orbital_distance=1.0,
                    orbital_period=1.0,
                    position=Vector3D(),
                )
            ],
        )
        mock_instance.generate_system.return_value = mock_system

        sim = GameSimulation()
        sim.initialize_new_game(num_systems=1)

        # Verify generator was called
        mock_instance.generate_system.assert_called()
        assert len(sim.star_systems) == 1

    def test_empire_creation(self):
        """Test empire creation during initialization."""
        sim = GameSimulation()
        sim.initialize_new_game(num_systems=3, num_empires=3)

        # Should have 3 empires total
        assert len(sim.empires) == 3

        # One should be player
        player_empires = [emp for emp in sim.empires.values() if emp.is_player]
        assert len(player_empires) == 1

        # Two should be AI
        ai_empires = [emp for emp in sim.empires.values() if not emp.is_player]
        assert len(ai_empires) == 2

        # Each empire should have a home system and planet
        for empire in sim.empires.values():
            assert empire.home_system_id in sim.star_systems
            system = sim.star_systems[empire.home_system_id]
            assert any(planet.id == empire.home_planet_id for planet in system.planets)

    def test_initial_fleet_creation(self):
        """Test that initial fleets are created for empires."""
        sim = GameSimulation()
        sim.initialize_new_game()

        player_empire = sim.get_player_empire()
        assert len(player_empire.fleets) > 0

        # Check that the fleet exists in the simulation
        fleet_id = player_empire.fleets[0]
        fleet = sim.get_fleet(fleet_id)
        assert fleet is not None
        assert fleet.empire_id == player_empire.id

    def test_multiple_star_systems(self):
        """Test initialization with multiple star systems."""
        sim = GameSimulation()
        sim.initialize_new_game(num_systems=5, num_empires=3)

        assert len(sim.star_systems) == 5

        # Each system should have at least one planet
        for system in sim.star_systems.values():
            assert len(system.planets) > 0

            # Each planet should have a position
            for planet in system.planets:
                assert planet.position is not None

    def test_orbital_mechanics_initialization(self):
        """Test that orbital mechanics are initialized."""
        sim = GameSimulation()

        # Mock the orbital mechanics to verify it's called
        with patch.object(sim.orbital_mechanics, "initialize_system") as mock_init:
            sim.initialize_new_game(num_systems=2)

            # Should be called for each system
            assert mock_init.call_count == 2

    def test_scheduler_integration(self):
        """Test scheduler integration."""
        sim = GameSimulation()
        sim.initialize_new_game()

        # Verify that events are scheduled
        assert sim.scheduler.get_pending_events_count() > 0

        # Test that time advancement processes events
        with patch.object(sim.scheduler, "process_events") as mock_process:
            sim.advance_time(100.0)
            mock_process.assert_called_once_with(0.0, 100.0)

    def test_ai_processing(self):
        """AI empires should process without errors and take basic actions."""
        sim = GameSimulation()
        sim.initialize_new_game(num_systems=3, num_empires=3)

        # Run AI update
        sim._update_ai_empires()

        ai_empires = [e for e in sim.empires.values() if not e.is_player]
        assert ai_empires

        for empire in ai_empires:
            # Should have started some research
            active = (
                1 if empire.current_research else 0
            ) + len(empire.research_projects)
            assert active > 0

            for fleet_id in empire.fleets:
                fleet = sim.get_fleet(fleet_id)
                assert fleet.status == FleetStatus.IN_TRANSIT
                assert fleet.estimated_arrival is not None

    def test_custom_system_and_empire_counts(self):
        """Initialize with custom counts and verify."""
        sim = GameSimulation()
        sim.initialize_new_game(num_systems=4, num_empires=4)

        assert len(sim.star_systems) == 4
        assert len(sim.empires) == 4



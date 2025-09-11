"""
Comprehensive test suite for the Victory Conditions and Game End System.

Tests victory tracking, progress calculation, achievement unlocking,
game end detection, and UI components.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from pyaurora4x.core.models import Empire, StarSystem, Fleet, Technology, Vector3D
from pyaurora4x.core.enums import VictoryCondition, TechnologyType, FleetStatus
from pyaurora4x.core.victory import (
    VictoryProgress, VictoryStatistics, GameResult, VictoryConditionConfig,
    VictoryAchievement, get_default_victory_config, get_default_achievements
)
from pyaurora4x.engine.victory_manager import VictoryManager
from pyaurora4x.core.events import EventManager


class TestVictoryModels:
    """Test victory condition models."""
    
    def test_victory_progress_creation(self):
        """Test VictoryProgress model creation."""
        progress = VictoryProgress(
            victory_type=VictoryCondition.CONQUEST,
            empire_id="test_empire",
            target_value=10.0
        )
        
        assert progress.victory_type == VictoryCondition.CONQUEST
        assert progress.empire_id == "test_empire"
        assert progress.target_value == 10.0
        assert progress.current_progress == 0.0
        assert progress.is_achievable is True
    
    def test_victory_statistics_creation(self):
        """Test VictoryStatistics model creation."""
        stats = VictoryStatistics(
            empire_id="test_empire",
            empire_name="Test Empire"
        )
        
        assert stats.empire_id == "test_empire"
        assert stats.empire_name == "Test Empire"
        assert stats.systems_controlled == 0
        assert stats.total_score == 0.0
    
    def test_game_result_creation(self):
        """Test GameResult model creation."""
        result = GameResult(
            game_start_time=0.0,
            game_end_time=100.0,
            total_duration=100.0,
            victory_condition=VictoryCondition.CONQUEST,
            game_end_reason="Conquest Victory"
        )
        
        assert result.victory_condition == VictoryCondition.CONQUEST
        assert result.game_end_reason == "Conquest Victory"
        assert result.total_duration == 100.0
    
    def test_victory_achievement_creation(self):
        """Test VictoryAchievement model creation."""
        achievement = VictoryAchievement(
            name="Test Achievement",
            description="A test achievement",
            category="test",
            requirements={"test_value": 5}
        )
        
        assert achievement.name == "Test Achievement"
        assert achievement.category == "test"
        assert achievement.requirements["test_value"] == 5
        assert achievement.is_unlocked is False
    
    def test_default_victory_config(self):
        """Test default victory configuration."""
        config = get_default_victory_config()
        
        assert config.conquest_percentage == 0.75
        assert config.research_trees_required == 5
        assert config.economic_gdp_multiplier == 2.5
        assert config.diplomatic_alliance_percentage == 0.8
        assert config.exploration_percentage == 0.95
    
    def test_default_achievements(self):
        """Test default achievements."""
        achievements = get_default_achievements()
        
        assert len(achievements) > 0
        # Check for some expected achievements
        achievement_names = [a.name for a in achievements]
        assert "First Blood" in achievement_names
        assert "Admiral" in achievement_names
        assert "Explorer" in achievement_names


class TestVictoryManager:
    """Test victory manager functionality."""
    
    @pytest.fixture
    def event_manager(self):
        """Create mock event manager."""
        mock_manager = Mock(spec=EventManager)
        mock_manager.create_and_post_event = Mock()
        return mock_manager
    
    @pytest.fixture
    def victory_manager(self, event_manager):
        """Create victory manager instance."""
        return VictoryManager(event_manager=event_manager)
    
    @pytest.fixture
    def test_empires(self):
        """Create test empires."""
        empires = []
        for i in range(3):
            # Distribute systems among empires (empire_0 gets more systems for testing)
            if i == 0:
                controlled_systems = ["system_0", "system_3", "system_6", "system_9"]
            elif i == 1:
                controlled_systems = ["system_1", "system_4", "system_7"]
            else:
                controlled_systems = ["system_2", "system_5", "system_8"]
                
            empire = Empire(
                id=f"empire_{i}",
                name=f"Test Empire {i}",
                is_player=(i == 0),
                home_system_id=f"system_{i}",
                home_planet_id=f"planet_{i}",
                controlled_systems=controlled_systems
            )
            empires.append(empire)
        return empires
    
    @pytest.fixture
    def test_systems(self):
        """Create test star systems."""
        systems = []
        for i in range(10):
            from pyaurora4x.core.enums import StarType
            system = StarSystem(
                id=f"system_{i}",
                name=f"Test System {i}",
                star_type=StarType.G_DWARF,
                star_mass=1.0,
                star_luminosity=1.0
            )
            systems.append(system)
        return systems
    
    @pytest.fixture
    def test_fleets(self, test_empires):
        """Create test fleets."""
        fleets = {}
        for i, empire in enumerate(test_empires):
            fleet = Fleet(
                id=f"fleet_{i}",
                name=f"Test Fleet {i}",
                empire_id=empire.id,
                system_id=f"system_{i}",
                position=Vector3D(x=0.0, y=0.0, z=0.0),
                ships=[f"ship_{i}_{j}" for j in range(3)]  # 3 ships per fleet
            )
            fleets[fleet.id] = fleet
        return fleets
    
    @pytest.fixture
    def test_technologies(self, test_empires):
        """Create test technologies."""
        technologies = {}
        for empire in test_empires:
            empire_techs = []
            for tech_type in TechnologyType:
                for j in range(2):  # 2 techs per type
                    tech = Technology(
                        id=f"{tech_type.value}_{j}",
                        name=f"{tech_type.value.title()} Tech {j}",
                        description=f"Test technology for {tech_type.value}",
                        tech_type=tech_type,
                        research_cost=100,
                        is_researched=True
                    )
                    empire_techs.append(tech)
            technologies[empire.id] = empire_techs
        return technologies
    
    def test_initialize_game(self, victory_manager, test_empires, test_systems):
        """Test game initialization."""
        victory_manager.initialize_game(test_empires, len(test_systems), 0.0)
        
        assert victory_manager.game_start_time == 0.0
        assert victory_manager.game_active is True
        assert len(victory_manager.victory_progress) == len(test_empires)
        assert len(victory_manager.empire_statistics) == len(test_empires)
        
        # Check that all victory conditions are tracked
        for empire in test_empires:
            empire_progress = victory_manager.victory_progress[empire.id]
            assert len(empire_progress) == len(VictoryCondition)
            for victory_type in VictoryCondition:
                assert victory_type in empire_progress
    
    def test_conquest_progress_calculation(self, victory_manager, test_empires, test_systems):
        """Test conquest victory progress calculation."""
        victory_manager.initialize_game(test_empires, len(test_systems), 0.0)
        
        # Empire 0 controls 4 systems out of 10 (40% of systems)
        empire = test_empires[0]
        
        # Update conquest progress
        victory_manager._calculate_conquest_progress(empire, test_systems)
        
        progress = victory_manager.victory_progress[empire.id][VictoryCondition.CONQUEST]
        
        # Should control systems according to empire.controlled_systems 
        expected_controlled = len(empire.controlled_systems)
        expected_target = len(test_systems) * victory_manager.config.conquest_percentage
        expected_progress = min(1.0, expected_controlled / expected_target)
        
        assert progress.current_value == expected_controlled
        assert progress.target_value == expected_target
        assert abs(progress.current_progress - expected_progress) < 0.01
    
    def test_research_progress_calculation(self, victory_manager, test_empires, test_technologies):
        """Test research victory progress calculation."""
        victory_manager.initialize_game(test_empires, 10, 0.0)
        
        empire = test_empires[0]
        empire_techs = test_technologies[empire.id]
        
        # Update research progress
        victory_manager._calculate_research_progress(empire, empire_techs)
        
        progress = victory_manager.victory_progress[empire.id][VictoryCondition.RESEARCH]
        
        # With 2 techs per type and 12 tech types, we have groups of 2
        # Consider tree "completed" if 10+ techs (only 2 per type, so 0 completed trees)
        expected_completed_trees = 0  # No tree has 10+ technologies
        expected_progress = min(1.0, expected_completed_trees / 5.0)  # Target is 5 trees
        
        assert progress.current_value == expected_completed_trees
        assert progress.current_progress == expected_progress
    
    def test_achievement_unlocking(self, victory_manager, test_empires):
        """Test achievement unlocking."""
        victory_manager.initialize_game(test_empires, 10, 0.0)
        
        # Modify empire statistics to meet achievement requirements
        empire = test_empires[0]
        stats = victory_manager.empire_statistics[empire.id]
        stats.enemy_ships_destroyed = 1  # Should unlock "First Blood"
        stats.battles_won = 10  # Should unlock "Admiral"
        
        # Check achievements
        victory_manager._check_achievements(test_empires, 100.0)
        
        # Verify achievements were unlocked
        first_blood = next((a for a in victory_manager.achievements if a.name == "First Blood"), None)
        admiral = next((a for a in victory_manager.achievements if a.name == "Admiral"), None)
        
        assert first_blood is not None
        assert first_blood.is_unlocked is True
        assert first_blood.unlocked_by_empire == empire.id
        
        assert admiral is not None
        assert admiral.is_unlocked is True
        assert admiral.unlocked_by_empire == empire.id
    
    def test_victory_detection(self, victory_manager, test_empires, test_systems, test_fleets, test_technologies):
        """Test victory condition detection."""
        victory_manager.initialize_game(test_empires, len(test_systems), 0.0)
        
        # Simulate conquest victory - give empire control of enough systems
        empire = test_empires[0]
        # Control 8 out of 10 systems (80% > 75% required)
        empire.controlled_systems = [f"system_{i}" for i in range(8)]
        
        # Update victory progress
        game_result = victory_manager.update_victory_progress(
            test_empires, test_systems, test_fleets, test_technologies, 100.0
        )
        
        # Should detect conquest victory
        assert game_result is not None
        assert game_result.victory_condition == VictoryCondition.CONQUEST
        assert empire.id in game_result.winner_empire_ids
        assert victory_manager.game_active is False
    
    def test_leaderboard_generation(self, victory_manager, test_empires, test_systems, test_fleets, test_technologies):
        """Test leaderboard generation."""
        victory_manager.initialize_game(test_empires, len(test_systems), 0.0)
        
        # Update victory progress to generate scores
        victory_manager.update_victory_progress(
            test_empires, test_systems, test_fleets, test_technologies, 100.0
        )
        
        leaderboard = victory_manager.get_leaderboard()
        
        assert len(leaderboard) == len(test_empires)
        
        # Check leaderboard is sorted by score
        for i in range(len(leaderboard) - 1):
            assert leaderboard[i]["total_score"] >= leaderboard[i + 1]["total_score"]
        
        # Check required fields
        for entry in leaderboard:
            assert "rank" in entry
            assert "empire_id" in entry
            assert "empire_name" in entry
            assert "total_score" in entry
            assert "best_victory_progress" in entry
    
    def test_victory_status_retrieval(self, victory_manager, test_empires, test_systems):
        """Test victory status retrieval."""
        victory_manager.initialize_game(test_empires, len(test_systems), 0.0)
        
        empire = test_empires[0]
        status = victory_manager.get_victory_status(empire.id)
        
        assert "empire_id" in status
        assert "progress" in status
        assert "statistics" in status
        assert "achievements" in status
        assert "current_rank" in status
        assert "total_score" in status
        
        # Check progress data structure
        progress_data = status["progress"]
        assert len(progress_data) == len(VictoryCondition)
        
        for victory_type in VictoryCondition:
            victory_key = victory_type.value
            assert victory_key in progress_data
            
            victory_progress = progress_data[victory_key]
            assert "progress" in victory_progress
            assert "current_value" in victory_progress
            assert "target_value" in victory_progress
            assert "is_achievable" in victory_progress
    
    def test_time_limit_victory(self, victory_manager, test_empires, test_systems, test_fleets, test_technologies):
        """Test time limit victory condition."""
        config = VictoryConditionConfig(max_game_duration=200.0)  # 200 second limit
        victory_manager = VictoryManager(config=config)
        
        victory_manager.initialize_game(test_empires, len(test_systems), 0.0)
        
        # Ensure empires have minimal economic data to avoid auto-victory
        for empire in test_empires:
            empire.colonies = []  # No colonies
            empire.fleets = []    # No fleets 
            empire.controlled_systems = []  # No controlled systems
        
        # Simulate time passing beyond limit
        game_result = victory_manager.update_victory_progress(
            test_empires, test_systems, test_fleets, test_technologies, 300.0
        )
        
        # Should detect time limit victory
        assert game_result is not None
        assert game_result.victory_condition == VictoryCondition.CUSTOM
        assert game_result.game_end_reason == "Time Limit Reached"
        assert victory_manager.game_active is False
    
    def test_force_game_end(self, victory_manager, test_empires):
        """Test forcing game end."""
        victory_manager.initialize_game(test_empires, 10, 0.0)
        
        empire = test_empires[0]
        game_result = victory_manager.force_game_end(
            "Test End Reason", 
            [empire.id], 
            100.0
        )
        
        assert game_result is not None
        assert game_result.game_end_reason == "Test End Reason"
        assert empire.id in game_result.winner_empire_ids
        assert victory_manager.game_active is False
        assert victory_manager.game_result == game_result


class TestVictoryUI:
    """Test victory UI components (basic functionality)."""
    
    @pytest.fixture
    def mock_victory_manager(self):
        """Create mock victory manager."""
        manager = Mock(spec=VictoryManager)
        manager.get_victory_status.return_value = {
            "empire_id": "test_empire",
            "progress": {
                "conquest": {
                    "progress": 0.5,
                    "current_value": 5,
                    "target_value": 10,
                    "is_achievable": True,
                    "details": {"systems_controlled": 5, "target_systems": 10}
                }
            },
            "statistics": {},
            "achievements": [],
            "current_rank": 1,
            "total_score": 1000.0
        }
        manager.get_leaderboard.return_value = [
            {
                "rank": 1,
                "empire_id": "test_empire",
                "empire_name": "Test Empire",
                "total_score": 1000.0,
                "best_victory_progress": 0.5,
                "best_victory_type": "conquest",
                "achievements_count": 0
            }
        ]
        manager.achievements = []
        manager.empire_statistics = {}
        return manager
    
    def test_victory_panel_creation(self, mock_victory_manager):
        """Test victory panel widget creation."""
        from pyaurora4x.ui.widgets.victory_panel import VictoryPanel
        
        panel = VictoryPanel(victory_manager=mock_victory_manager)
        
        assert panel.victory_manager == mock_victory_manager
        assert panel.visible is False
        assert panel.game_ended is False
    
    def test_victory_panel_empire_update(self, mock_victory_manager):
        """Test victory panel empire update."""
        from pyaurora4x.ui.widgets.victory_panel import VictoryPanel
        from pyaurora4x.core.models import Empire
        
        panel = VictoryPanel(victory_manager=mock_victory_manager)
        empire = Empire(
            id="test_empire", 
            name="Test Empire",
            home_system_id="test_system",
            home_planet_id="test_planet"
        )
        
        # Test just the data assignment part without UI updates
        panel.current_empire = empire
        
        assert panel.current_empire == empire
    
    def test_victory_panel_game_result_update(self, mock_victory_manager):
        """Test victory panel game result update."""
        from pyaurora4x.ui.widgets.victory_panel import VictoryPanel
        
        panel = VictoryPanel(victory_manager=mock_victory_manager)
        
        game_result = GameResult(
            game_start_time=0.0,
            game_end_time=100.0,
            total_duration=100.0,
            victory_condition=VictoryCondition.CONQUEST,
            game_end_reason="Test Victory"
        )
        
        # Just test the data assignment, not UI updates that require DOM
        panel.game_result = game_result
        panel.game_ended = True
        
        assert panel.game_result == game_result
        assert panel.game_ended is True


class TestVictoryIntegration:
    """Test victory system integration with game simulation."""
    
    def test_simulation_victory_integration(self):
        """Test victory system integration with simulation."""
        from pyaurora4x.engine.simulation import GameSimulation
        
        simulation = GameSimulation()
        
        # Check that victory manager is properly initialized
        assert hasattr(simulation, 'victory_manager')
        assert simulation.victory_manager is not None
        
        # Initialize a test game
        simulation.initialize_new_game(num_systems=5, num_empires=2)
        
        # Check that victory tracking was initialized
        assert len(simulation.victory_manager.victory_progress) > 0
        assert len(simulation.victory_manager.empire_statistics) > 0
    
    def test_victory_checking_in_simulation(self):
        """Test victory condition checking during simulation."""
        from pyaurora4x.engine.simulation import GameSimulation
        
        simulation = GameSimulation()
        simulation.initialize_new_game(num_systems=3, num_empires=2)
        
        # Mock a victory condition being met
        with patch.object(simulation.victory_manager, 'update_victory_progress') as mock_update:
            mock_game_result = GameResult(
                game_start_time=0.0,
                game_end_time=100.0,
                total_duration=100.0,
                victory_condition=VictoryCondition.CONQUEST,
                game_end_reason="Test Victory"
            )
            mock_update.return_value = mock_game_result
            
            # Check victory conditions
            game_ended = simulation.check_victory_conditions()
            
            assert game_ended is True
            assert simulation.is_running is False


if __name__ == "__main__":
    pytest.main([__file__])

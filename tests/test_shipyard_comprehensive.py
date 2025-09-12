"""
Comprehensive tests for the shipyard system including seeding, refits, 
tooling, UI interactions, and save migrations.
"""

import pytest
import uuid
from unittest.mock import Mock, patch

from pyaurora4x.core.shipyards import Shipyard, Slipway, BuildOrder, RefitOrder, YardType
from pyaurora4x.engine.shipyard_manager import ShipyardManager
from pyaurora4x.engine.simulation import GameSimulation
from pyaurora4x.core.models import Empire, Colony
from pyaurora4x.data.save_manager import SaveManager


class TestShipyardSeeding:
    """Test automatic shipyard creation during game initialization."""
    
    def test_empire_shipyard_initialization(self):
        """Test that empires get initial shipyards when game starts."""
        sim = GameSimulation()
        sim.initialize_new_game(num_systems=2, num_empires=2)
        
        # Check that shipyards were created for all empires
        assert len(sim.shipyard_manager.yards) > 0
        
        player_yards = [y for y in sim.shipyard_manager.yards.values() if y.empire_id == "player"]
        assert len(player_yards) == 1
        
        player_yard = player_yards[0]
        assert player_yard.yard_type == YardType.COMMERCIAL
        assert len(player_yard.slipways) == 2  # Player gets 2 slipways
        assert player_yard.bp_per_day > 0
        
        # Check AI empires got yards too
        ai_yards = [y for y in sim.shipyard_manager.yards.values() if y.empire_id.startswith("ai_")]
        assert len(ai_yards) >= 1
    
    def test_shipyard_throughput_calculation(self):
        """Test that shipyard throughput is calculated from industry."""
        sim = GameSimulation()
        sim.initialize_new_game(num_systems=1, num_empires=1)
        
        # Get the player empire and yard
        empire = sim.empires["player"]
        yard = next(y for y in sim.shipyard_manager.yards.values() if y.empire_id == "player")
        
        initial_bp = yard.bp_per_day
        assert initial_bp > 0
        
        # Simulate adding industry to a colony
        colony = sim.colonies[empire.colonies[0]]
        colony.infrastructure = {"factory": 3}
        
        # Update throughput
        sim._update_shipyard_throughput()
        
        # Throughput should have increased
        assert yard.bp_per_day > initial_bp


class TestShipyardRefits:
    """Test refit order system and ship design comparisons."""
    
    @pytest.fixture
    def shipyard_manager(self):
        return ShipyardManager()
    
    @pytest.fixture
    def test_yard(self, shipyard_manager):
        yard = Shipyard(
            id="test_yard",
            empire_id="test_empire",
            name="Test Shipyard",
            yard_type=YardType.NAVAL,
            bp_per_day=100.0,
            slipways=[Slipway(id="slip1", max_hull_tonnage=10000)]
        )
        shipyard_manager.add_yard(yard)
        return yard
    
    def test_refit_order_creation(self, shipyard_manager):
        """Test creating refit orders with cost calculation."""
        refit_order = shipyard_manager.create_refit_order(
            ship_id="ship_1",
            from_design_id="design_a",
            to_design_id="design_b",
            hull_tonnage=5000,
            priority=8
        )
        
        assert refit_order.ship_id == "ship_1"
        assert refit_order.from_design_id == "design_a"
        assert refit_order.to_design_id == "design_b"
        assert refit_order.hull_tonnage == 5000
        assert refit_order.total_bp > 0  # Cost was calculated
        assert refit_order.refit_cost_multiplier == 1.5
    
    def test_refit_queue_management(self, shipyard_manager, test_yard):
        """Test adding refit orders to yard queues."""
        refit_order = RefitOrder(
            ship_id="ship_1",
            from_design_id="design_a", 
            to_design_id="design_b",
            hull_tonnage=5000,
            total_bp=750.0
        )
        
        success = shipyard_manager.add_refit_order(test_yard.id, refit_order)
        assert success
        assert len(test_yard.refit_queue) == 1
        assert test_yard.refit_queue[0].ship_id == "ship_1"
    
    def test_ship_design_comparison(self, shipyard_manager):
        """Test ship design comparison functionality."""
        comparison = shipyard_manager.compare_ship_designs("design_a", "design_b")
        
        assert "components_different" in comparison
        assert "cost_difference" in comparison
        assert "time_estimate_days" in comparison
        assert "feasible" in comparison


class TestShipyardTooling:
    """Test yard tooling upgrades and capacity expansion."""
    
    @pytest.fixture
    def test_yard(self):
        return Shipyard(
            id="test_yard",
            empire_id="test_empire", 
            name="Test Yard",
            yard_type=YardType.NAVAL,
            bp_per_day=100.0,
            tooling_bonus=1.0,
            slipways=[Slipway(id="slip1", max_hull_tonnage=10000)]
        )
    
    def test_tooling_upgrade_calculation(self, test_yard):
        """Test tooling upgrade cost and benefit calculation."""
        upgrade_info = test_yard.upgrade_tooling()
        
        assert upgrade_info["feasible"] is True
        assert upgrade_info["current_bonus"] == 1.0
        assert upgrade_info["new_bonus"] == 1.1
        assert upgrade_info["cost_bp"] > 0
        assert upgrade_info["time_days"] > 0
        assert upgrade_info["efficiency_gain"] == 10.0  # 10% improvement
    
    def test_tooling_upgrade_cap(self, test_yard):
        """Test that tooling upgrades are capped at maximum efficiency."""
        test_yard.tooling_bonus = 2.0  # At max
        
        upgrade_info = test_yard.upgrade_tooling()
        assert upgrade_info["feasible"] is False
        assert "maximum tooling" in upgrade_info["reason"]
    
    def test_slipway_addition(self, test_yard):
        """Test adding new slipways to yards."""
        initial_slipways = len(test_yard.slipways)
        
        addition_info = test_yard.add_slipway(max_tonnage=15000)
        
        assert addition_info["feasible"] is True
        assert addition_info["max_tonnage"] == 15000
        assert addition_info["cost_bp"] > 0
        assert addition_info["total_slipways_after"] == initial_slipways + 1
    
    def test_retooling_for_design(self, test_yard):
        """Test yard retooling for specific ship designs."""
        retool_info = test_yard.retool_for_design("design_x")
        
        assert retool_info["feasible"] is True
        assert retool_info["design_id"] == "design_x"
        assert retool_info["cost_bp"] > 0
        assert retool_info["design_bonus"] == 1.25  # 25% bonus
        assert retool_info["general_penalty"] == 0.95  # 5% penalty for others


class TestShipyardUI:
    """Test shipyard UI panel functionality."""
    
    @pytest.fixture
    def mock_simulation(self):
        sim = Mock()
        sim.shipyard_manager = ShipyardManager()
        
        # Add test yard
        yard = Shipyard(
            id="test_yard_ui",
            empire_id="player",
            name="Player Shipyard",
            yard_type=YardType.COMMERCIAL,
            bp_per_day=75.0,
            slipways=[
                Slipway(id="slip1", max_hull_tonnage=5000),
                Slipway(id="slip2", max_hull_tonnage=8000, active_order_id="order1")
            ],
            build_queue=[
                BuildOrder(id="order1", design_id="frigate_mk1", hull_tonnage=3000, 
                          total_bp=300.0, progress_bp=150.0, assigned_slipway_id="slip2")
            ]
        )
        sim.shipyard_manager.add_yard(yard)
        return sim
    
    def test_shipyard_panel_initialization(self, mock_simulation):
        """Test shipyard panel setup and data loading."""
        from pyaurora4x.ui.widgets.shipyard_panel import ShipyardPanel
        
        panel = ShipyardPanel(simulation=mock_simulation)
        panel.set_empire("player")
        panel.refresh_display()
        
        # Check that yards were loaded
        assert len(panel.yards) == 1
        assert "test_yard_ui" in panel.yards
    
    def test_yard_summary_generation(self, mock_simulation):
        """Test empire shipyard summary generation."""
        from pyaurora4x.ui.widgets.shipyard_panel import ShipyardPanel
        
        panel = ShipyardPanel(simulation=mock_simulation)
        summary = panel.get_yard_summary("player")
        
        assert summary["yards_count"] == 1
        assert summary["total_slipways"] == 2
        assert summary["active_slipways"] == 1
        assert summary["total_orders"] == 1
        assert summary["total_bp_per_day"] > 0


class TestSaveMigration:
    """Test save file migration for backward compatibility."""
    
    def test_legacy_save_migration(self):
        """Test migration of save files without shipyards section."""
        save_manager = SaveManager()
        
        # Create legacy save data without shipyards
        legacy_save = {
            "current_time": 86400,
            "empires": {"player": {"id": "player", "name": "Test"}},
            "star_systems": {},
            "fleets": {},
            "colonies": {}
            # No shipyards section
        }
        
        # Apply migration
        migrated_save = save_manager._migrate_save_data(legacy_save)
        
        # Check that shipyards section was added
        assert "shipyards" in migrated_save
        assert migrated_save["shipyards"] == {}
        assert migrated_save["save_format_version"] == "1.1"
    
    def test_modern_save_no_migration(self):
        """Test that modern saves with shipyards are not modified."""
        save_manager = SaveManager()
        
        modern_save = {
            "save_format_version": "1.1",
            "current_time": 86400,
            "empires": {"player": {"id": "player"}},
            "shipyards": {"yard_1": {"id": "yard_1"}}
        }
        
        original_shipyards = modern_save["shipyards"].copy()
        migrated_save = save_manager._migrate_save_data(modern_save)
        
        # Should be unchanged
        assert migrated_save["shipyards"] == original_shipyards
        assert migrated_save["save_format_version"] == "1.1"


class TestShipyardIntegration:
    """Test full integration of shipyard system with simulation."""
    
    def test_full_shipyard_workflow(self):
        """Test complete shipyard workflow from initialization through production."""
        # Initialize simulation with shipyards
        sim = GameSimulation()
        sim.initialize_new_game(num_systems=1, num_empires=1)
        
        # Verify shipyards were created
        player_empire = sim.empires["player"]
        player_yards = [y for y in sim.shipyard_manager.yards.values() 
                       if y.empire_id == player_empire.id]
        assert len(player_yards) == 1
        
        yard = player_yards[0]
        
        # Add a build order
        build_order = BuildOrder(
            id=str(uuid.uuid4()),
            design_id="test_design",
            hull_tonnage=2000,
            total_bp=100.0
        )
        yard.build_queue.append(build_order)
        
        # Advance time to trigger shipyard processing
        sim.advance_time(86400 * 2)  # 2 days
        
        # Order should have made progress
        assert build_order.progress_bp > 0
        
        # Test save/load with shipyards
        save_manager = SaveManager()
        game_state = sim.get_game_state()
        
        # Should include shipyards
        assert "shipyards" in game_state
        assert len(game_state["shipyards"]) > 0
        
        # Save and reload
        save_path = save_manager.save_game(game_state, "test_shipyards")
        loaded_state = save_manager.load_game("test_shipyards")
        
        # Shipyards should be preserved
        assert "shipyards" in loaded_state
        assert len(loaded_state["shipyards"]) > 0
    
    def test_industry_throughput_integration(self):
        """Test that industry changes affect shipyard throughput."""
        sim = GameSimulation()
        sim.initialize_new_game(num_systems=1, num_empires=1)
        
        empire = sim.empires["player"]
        yard = next(y for y in sim.shipyard_manager.yards.values() 
                   if y.empire_id == empire.id)
        
        initial_throughput = yard.bp_per_day
        
        # Add industrial capacity
        colony = sim.colonies[empire.colonies[0]]
        colony.infrastructure = {"factory": 5}  # Add factories
        
        # Update throughput (happens automatically daily, but we can force it)
        sim._update_shipyard_throughput()
        
        # Throughput should increase
        assert yard.bp_per_day > initial_throughput
        
        # Add construction technology
        from pyaurora4x.core.models import Technology
        tech = Technology(
            id="automated_construction",
            name="Automated Construction",
            description="Improves construction efficiency",
            tech_type="construction",
            research_cost=1000,
            is_researched=True
        )
        empire.technologies["automated_construction"] = tech
        
        # Update again
        previous_throughput = yard.bp_per_day
        sim._update_shipyard_throughput()
        
        # Should increase further due to tech bonus
        assert yard.bp_per_day > previous_throughput


# Test fixtures for mock objects
@pytest.fixture
def mock_empire():
    return Empire(
        id="test_empire",
        name="Test Empire",
        is_player=True,
        home_system_id="system_1",
        home_planet_id="planet_1",
        colonies=["colony_1"],
        technologies={}
    )

@pytest.fixture  
def mock_colony():
    return Colony(
        id="colony_1",
        name="Test Colony",
        empire_id="test_empire",
        planet_id="planet_1",
        infrastructure={"factory": 2}
    )

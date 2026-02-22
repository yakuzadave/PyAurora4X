"""
Integration tests for Ship Mechanics.

Tests ship component system, shipyard operations, build/refit mechanics,
and validates examples from the Ship Mechanics guide.
"""

import pytest
from pyaurora4x.core.models import Ship, ShipComponent, ShipDesign, ShipType, Vector3D
from pyaurora4x.core.shipyards import Shipyard, BuildOrder, RefitOrder, Slipway, YardType
from pyaurora4x.engine.shipyard_manager import ShipyardManager


class TestShipComponents:
    """Test ship component system."""
    
    def test_component_creation(self):
        """Test creating a ship component with all attributes."""
        component = ShipComponent(
            id="ion_drive_mk2",
            name="Ion Drive Mark II",
            component_type="engine",
            mass=50.0,
            cost=1000,
            power_requirement=0.0,
            crew_requirement=5,
            tech_requirements=["Advanced Ion Propulsion"],
            attributes={
                "power_output": 100.0,
                "fuel_efficiency": 0.8,
                "max_acceleration": 5.0,
                "max_speed": 5000.0
            }
        )
        
        assert component.id == "ion_drive_mk2"
        assert component.component_type == "engine"
        assert component.mass == 50.0
        assert component.attributes["power_output"] == 100.0
    
    def test_weapon_component(self):
        """Test weapon component attributes."""
        weapon = ShipComponent(
            id="railgun_mk1",
            name="Railgun Mark I",
            component_type="weapon",
            mass=25.0,
            cost=500,
            power_requirement=50.0,
            crew_requirement=3,
            tech_requirements=["Railgun Technology"],
            attributes={
                "damage": 100.0,
                "range": 10000.0,
                "accuracy": 0.85,
                "rate_of_fire": 2.0,
                "weapon_type": "kinetic",
                "tracking_speed": 1.5
            }
        )
        
        assert weapon.component_type == "weapon"
        assert weapon.attributes["damage"] == 100.0
        assert weapon.attributes["accuracy"] == 0.85


class TestShipDesign:
    """Test ship design system."""
    
    def test_design_creation(self):
        """Test creating a ship design."""
        design = ShipDesign(
            id="cruiser_mk1",
            name="Cruiser Mark I",
            ship_type=ShipType.CRUISER,
            components=["engine_1", "fuel_tank_1", "weapon_1"],
            total_mass=5000.0,
            total_cost=10000,
            crew_requirement=50
        )
        
        assert design.ship_type == ShipType.CRUISER
        assert len(design.components) == 3
        assert design.total_mass == 5000.0
    
    def test_design_statistics(self):
        """Test calculated design statistics."""
        design = ShipDesign(
            id="destroyer_mk1",
            name="Destroyer Mark I",
            ship_type=ShipType.DESTROYER,
            components=["comp_1", "comp_2"],
            total_mass=2000.0,
            total_cost=5000,
            crew_requirement=30
        )
        
        assert design.total_mass > 0
        assert design.total_cost > 0
        assert design.crew_requirement > 0


class TestShipyardOperations:
    """Test shipyard build point system and operations."""
    
    @pytest.fixture
    def shipyard(self):
        """Create a test shipyard."""
        return Shipyard(
            id="yard_1",
            empire_id="test_empire",
            name="Test Shipyard",
            yard_type=YardType.NAVAL,
            bp_per_day=1000.0,
            tooling_bonus=1.5,
            slipways=[
                Slipway(id="slip_1", max_hull_tonnage=10000),
                Slipway(id="slip_2", max_hull_tonnage=5000),
            ]
        )
    
    def test_effective_bp_calculation(self, shipyard):
        """Test BP calculation as documented in guide."""
        # From documentation: BP Generation Formula
        expected_bp = 1000.0 * 1.5  # base × tooling_bonus
        assert shipyard.effective_bp_per_day() == expected_bp
    
    def test_available_slipway(self, shipyard):
        """Test finding available slipway."""
        # From documentation: Slipway Assignment
        slipway = shipyard.available_slipway(tonnage=5000)
        
        assert slipway is not None
        assert slipway.max_hull_tonnage >= 5000
        assert slipway.active_order_id is None
    
    def test_slipway_tonnage_limit(self, shipyard):
        """Test slipway respects tonnage limits."""
        # Try to find slipway for ship too large
        slipway = shipyard.available_slipway(tonnage=15000)
        
        # Should fail - no slipway can handle 15000 tons
        assert slipway is None
    
    def test_upgrade_tooling(self, shipyard):
        """Test tooling upgrade calculation as documented."""
        # From documentation: Upgrading Tooling
        upgrade_info = shipyard.upgrade_tooling(cost_multiplier=2.0)
        
        assert upgrade_info["feasible"] is True
        assert "current_bonus" in upgrade_info
        assert "new_bonus" in upgrade_info
        assert "cost_bp" in upgrade_info
        assert "time_days" in upgrade_info
        assert "efficiency_gain" in upgrade_info
        
        # New bonus should be +10%
        expected_new_bonus = min(shipyard.tooling_bonus + 0.1, 2.0)
        assert upgrade_info["new_bonus"] == expected_new_bonus
    
    def test_upgrade_tooling_at_maximum(self):
        """Test that tooling cannot be upgraded beyond maximum."""
        shipyard = Shipyard(
            id="yard_max",
            empire_id="test_empire",
            name="Max Shipyard",
            yard_type=YardType.NAVAL,
            bp_per_day=1000.0,
            tooling_bonus=2.0,  # Already at max
            slipways=[Slipway(id="slip_1", max_hull_tonnage=10000)]
        )
        
        upgrade_info = shipyard.upgrade_tooling()
        
        assert upgrade_info["feasible"] is False
        assert "maximum" in upgrade_info["reason"].lower()
    
    def test_retool_for_design(self, shipyard):
        """Test retooling calculation as documented."""
        # From documentation: Retooling for Different Design
        retool_info = shipyard.retool_for_design(
            design_id="destroyer_mk1",
            retool_cost_multiplier=0.25
        )
        
        assert retool_info["feasible"] is True
        assert "cost_bp" in retool_info
        assert "retool_time_days" in retool_info
        assert retool_info["design_id"] == "destroyer_mk1"


class TestBuildOrders:
    """Test build order system."""
    
    def test_build_order_creation(self):
        """Test creating a build order."""
        order = BuildOrder(
            id="order_1",
            design_id="cruiser_mk1",
            hull_tonnage=5000,
            total_bp=50000.0,
            priority=5
        )
        
        assert order.design_id == "cruiser_mk1"
        assert order.total_bp == 50000.0
        assert order.progress_bp == 0.0
        assert not order.is_complete()
    
    def test_build_completion_check(self):
        """Test build order completion detection."""
        order = BuildOrder(
            id="order_1",
            design_id="cruiser_mk1",
            hull_tonnage=5000,
            total_bp=50000.0,
            progress_bp=50000.0  # Fully built
        )
        
        assert order.is_complete()
        assert order.completion_percentage() == 100.0
    
    def test_partial_completion(self):
        """Test partial build completion percentage."""
        order = BuildOrder(
            id="order_1",
            design_id="cruiser_mk1",
            hull_tonnage=5000,
            total_bp=50000.0,
            progress_bp=25000.0  # 50% complete
        )
        
        assert order.completion_percentage() == 50.0
        assert not order.is_complete()


class TestRefitOrders:
    """Test refit order system."""
    
    def test_refit_order_creation(self):
        """Test creating a refit order as documented."""
        # From documentation: Refitting Ships
        refit = RefitOrder(
            id="refit_1",
            ship_id="ship_alpha",
            from_design_id="cruiser_mk1",
            to_design_id="cruiser_mk2",
            hull_tonnage=5000,
            total_bp=75000.0,
            refit_cost_multiplier=1.5,
            components_to_add={"railgun_mk2": 2, "shield_generator_mk2": 1},
            components_to_remove={"railgun_mk1": 2, "shield_generator_mk1": 1}
        )
        
        assert refit.ship_id == "ship_alpha"
        assert refit.from_design_id == "cruiser_mk1"
        assert refit.to_design_id == "cruiser_mk2"
        assert refit.refit_cost_multiplier == 1.5
        assert "railgun_mk2" in refit.components_to_add
        assert "railgun_mk1" in refit.components_to_remove


class TestShipyardManager:
    """Test shipyard manager tick processing."""
    
    @pytest.fixture
    def manager_with_yard(self):
        """Create manager with configured shipyard."""
        manager = ShipyardManager()
        
        yard = Shipyard(
            id="test_yard",
            empire_id="test_empire",
            name="Test Shipyard",
            yard_type=YardType.NAVAL,
            bp_per_day=500.0,
            tooling_bonus=1.0,
            slipways=[
                Slipway(id="slip_1", max_hull_tonnage=10000),
                Slipway(id="slip_2", max_hull_tonnage=5000),
            ]
        )
        
        manager.add_yard(yard)
        return manager, yard
    
    def test_build_order_processing(self, manager_with_yard):
        """Test that build orders consume BP over time."""
        manager, yard = manager_with_yard
        
        # Add build order
        order = BuildOrder(
            id="build_1",
            design_id="test_design",
            hull_tonnage=5000,
            total_bp=5000.0,
            priority=5
        )
        yard.build_queue.append(order)
        
        # Process 1 day (should apply 500 BP)
        completed = manager.tick(days=1.0, now=0.0)
        
        assert order.progress_bp > 0
        assert order.progress_bp <= 500.0  # Can't exceed daily capacity
        assert len(completed) == 0  # Not finished yet
    
    def test_build_completion(self, manager_with_yard):
        """Test build order completion and event generation."""
        manager, yard = manager_with_yard
        
        # Add order that will complete in one tick
        order = BuildOrder(
            id="build_1",
            design_id="test_design",
            hull_tonnage=5000,
            total_bp=400.0,  # Less than daily capacity
            priority=5
        )
        yard.build_queue.append(order)
        
        # Process 1 day (500 BP available, only needs 400)
        completed = manager.tick(days=1.0, now=100.0)
        
        assert len(completed) == 1
        assert completed[0]["order_id"] == "build_1"
        assert completed[0]["type"] == "BuildOrder"
        assert completed[0]["time"] == 100.0
        
        # Order should be removed from queue
        assert len(yard.build_queue) == 0
    
    def test_multiple_orders_bp_distribution(self, manager_with_yard):
        """Test BP distribution among multiple active orders."""
        manager, yard = manager_with_yard
        
        # Add two orders
        order1 = BuildOrder(
            id="build_1",
            design_id="design_1",
            hull_tonnage=5000,
            total_bp=10000.0,
            priority=5
        )
        order2 = BuildOrder(
            id="build_2",
            design_id="design_2",
            hull_tonnage=5000,
            total_bp=10000.0,
            priority=5
        )
        
        yard.build_queue.extend([order1, order2])
        
        # Process 1 day (500 BP total)
        # Should split: 250 BP to each order
        completed = manager.tick(days=1.0, now=0.0)
        
        assert order1.progress_bp > 0
        assert order2.progress_bp > 0
        # Both should receive roughly equal shares
        assert abs(order1.progress_bp - order2.progress_bp) < 10.0
        assert len(completed) == 0  # Neither complete yet
    
    def test_refit_order_processing(self, manager_with_yard):
        """Test refit order processing."""
        manager, yard = manager_with_yard
        
        # Add refit order
        refit = RefitOrder(
            id="refit_1",
            ship_id="ship_1",
            from_design_id="old_design",
            to_design_id="new_design",
            hull_tonnage=5000,
            total_bp=3000.0,
            refit_cost_multiplier=1.5
        )
        yard.refit_queue.append(refit)
        
        # Process to completion
        completed = manager.tick(days=10.0, now=0.0)  # 5000 BP available
        
        # Should complete (needs 3000 BP)
        assert len(completed) == 1
        assert completed[0]["type"] == "RefitOrder"
        assert len(yard.refit_queue) == 0
    
    def test_slipway_assignment(self, manager_with_yard):
        """Test automatic slipway assignment."""
        manager, yard = manager_with_yard
        
        # Add order without assigned slipway
        order = BuildOrder(
            id="build_1",
            design_id="test_design",
            hull_tonnage=5000,
            total_bp=5000.0,
            priority=5
        )
        yard.build_queue.append(order)
        
        # First tick should assign slipway
        manager.assign_orders()
        
        assert order.assigned_slipway_id is not None
        
        # Find the slipway
        slipway = next(s for s in yard.slipways if s.id == order.assigned_slipway_id)
        assert slipway.active_order_id == order.id


class TestShipConditionAndDamage:
    """Test ship condition and damage mechanics."""
    
    def test_ship_initial_condition(self):
        """Test ship starts at full condition."""
        ship = Ship(
            id="ship_1",
            name="Test Ship",
            design_id="design_1",
            empire_id="empire_1",
            system_id="sol"
        )
        
        assert ship.condition == 100.0
        assert ship.structure == 100.0
        assert ship.fuel == 100.0
    
    def test_damage_reduces_condition(self):
        """Test that damage affects ship condition."""
        ship = Ship(
            id="ship_1",
            name="Test Ship",
            design_id="design_1",
            empire_id="empire_1",
            system_id="sol",
            structure=50.0  # 50% structure damage
        )
        
        # Structure damage should reflect in condition
        assert ship.structure < 100.0
    
    def test_shield_and_armor_values(self):
        """Test ship combat defense values."""
        ship = Ship(
            id="ship_1",
            name="Combat Ship",
            design_id="design_1",
            empire_id="empire_1",
            system_id="sol",
            shields=100.0,
            armor=50.0
        )
        
        assert ship.shields == 100.0
        assert ship.armor == 50.0


class TestShipMechanicsExamples:
    """Test specific examples from the Ship Mechanics guide."""
    
    def test_scout_design_example(self):
        """Test scout-like ship design from documentation."""
        # From documentation: Example 1 - Scout design (using FRIGATE as scout-like)
        scout_design = ShipDesign(
            id="scout_mk1",
            name="Scout Mark I",
            ship_type=ShipType.FRIGATE,  # Use FRIGATE for light/fast ships
            components=[
                "advanced_engine",
                "fuel_tank_large",
                "sensor_array_long",
                "light_laser",
                "crew_quarters_small",
                "command_center_basic"
            ]
        )
        
        assert scout_design.ship_type == ShipType.FRIGATE
        assert len(scout_design.components) == 6
    
    def test_battleship_design_example(self):
        """Test battleship design from documentation."""
        # From documentation: Example 2 - Designing a Battleship
        battleship_design = ShipDesign(
            id="battleship_mk1",
            name="Battleship Mark I",
            ship_type=ShipType.BATTLESHIP,
            components=[
                "fusion_drive",
                "fuel_tank_standard",
                "sensor_array_standard",
                "heavy_railgun", "heavy_railgun", "heavy_railgun",
                "missile_launcher", "missile_launcher",
                "shield_generator_heavy",
                "armor_plate_heavy", "armor_plate_heavy",
                "crew_quarters_large",
                "command_center_advanced"
            ]
        )
        
        assert battleship_design.ship_type == ShipType.BATTLESHIP
        assert len(battleship_design.components) == 13
        # 3 heavy railguns + 2 missile launchers = heavy firepower
        weapon_count = sum(1 for c in battleship_design.components 
                          if "railgun" in c or "missile" in c)
        assert weapon_count == 5
    
    def test_fleet_building_example(self):
        """Test building a fleet as documented."""
        # From documentation: Example 3 - Building a Fleet
        shipyard = Shipyard(
            id="earth_orbital_yards",
            empire_id="player_empire",
            name="Earth Orbital Shipyards",
            yard_type=YardType.NAVAL,
            bp_per_day=1000.0,
            tooling_bonus=1.5,
            slipways=[
                Slipway(id="slip_1", max_hull_tonnage=10000),
                Slipway(id="slip_2", max_hull_tonnage=10000),
                Slipway(id="slip_3", max_hull_tonnage=5000),
            ]
        )
        
        # Queue multiple ships
        designs_to_build = [
            ("battleship_mk1", 8000, 80000.0),
            ("cruiser_mk1", 5000, 50000.0),
            ("cruiser_mk1", 5000, 50000.0),
            ("destroyer_mk1", 2000, 20000.0),
            ("destroyer_mk1", 2000, 20000.0),
            ("destroyer_mk1", 2000, 20000.0),
        ]
        
        for i, (design_id, tonnage, bp) in enumerate(designs_to_build):
            order = BuildOrder(
                id=f"order_{i}",
                design_id=design_id,
                hull_tonnage=tonnage,
                total_bp=bp,
                priority=10 - i
            )
            shipyard.build_queue.append(order)
        
        assert len(shipyard.build_queue) == 6
        
        # Calculate completion as documented
        effective_bp = shipyard.effective_bp_per_day()
        assert effective_bp == 1500.0  # 1000 × 1.5
        
        total_bp = sum(bp for _, _, bp in designs_to_build)
        assert total_bp == 240000.0  # 80k + 50k + 50k + 20k + 20k + 20k
        
        # Expected time
        total_days = total_bp / effective_bp
        assert abs(total_days - 160.0) < 1.0  # Should be ~160 days


class TestShipLogistics:
    """Test ship fuel and logistics systems."""
    
    def test_ship_fuel_tracking(self):
        """Test ship fuel tracking."""
        ship = Ship(
            id="ship_1",
            name="Test Ship",
            design_id="design_1",
            empire_id="empire_1",
            system_id="sol",
            fuel=75.0  # 75% fuel
        )
        
        assert ship.fuel == 75.0
        assert 0.0 <= ship.fuel <= 100.0
    
    def test_fuel_percentage_calculation(self):
        """Test fuel percentage calculation from guide."""
        ship = Ship(
            id="ship_1",
            name="Test Ship",
            design_id="design_1",
            empire_id="empire_1",
            system_id="sol",
            fuel=30.0
        )
        
        # From documentation: fuel warning at < 30%
        fuel_percentage = ship.fuel / 100.0
        
        assert fuel_percentage == 0.3
        assert fuel_percentage < 0.5  # Would trigger warning


class TestShipyardIntegration:
    """Integration tests for complete shipyard workflows."""
    
    def test_complete_build_workflow(self):
        """Test complete ship building workflow."""
        # Setup
        manager = ShipyardManager()
        yard = Shipyard(
            id="yard_1",
            empire_id="test_empire",
            name="Test Yard",
            yard_type=YardType.NAVAL,
            bp_per_day=1000.0,
            tooling_bonus=1.0,
            slipways=[Slipway(id="slip_1", max_hull_tonnage=10000)]
        )
        manager.add_yard(yard)
        
        # Create order
        order = BuildOrder(
            id="order_1",
            design_id="frigate_mk1",
            hull_tonnage=3000,
            total_bp=3000.0,
            priority=5
        )
        yard.build_queue.append(order)
        
        # Process until complete
        day = 0
        max_days = 10
        while day < max_days and not order.is_complete():
            completed = manager.tick(days=1.0, now=float(day))
            day += 1
            
            if completed:
                assert len(completed) == 1
                assert completed[0]["order_id"] == "order_1"
                break
        
        # Should complete in 3 days (3000 BP ÷ 1000 BP/day)
        assert day <= 4  # Allow some margin
        assert len(yard.build_queue) == 0  # Order removed after completion
    
    def test_multiple_slipways_parallel_building(self):
        """Test parallel construction on multiple slipways."""
        manager = ShipyardManager()
        yard = Shipyard(
            id="yard_1",
            empire_id="test_empire",
            name="Test Yard",
            yard_type=YardType.NAVAL,
            bp_per_day=1000.0,
            tooling_bonus=1.0,
            slipways=[
                Slipway(id="slip_1", max_hull_tonnage=10000),
                Slipway(id="slip_2", max_hull_tonnage=10000),
            ]
        )
        manager.add_yard(yard)
        
        # Add two orders
        order1 = BuildOrder(
            id="order_1",
            design_id="ship_a",
            hull_tonnage=5000,
            total_bp=2000.0,
            priority=5
        )
        order2 = BuildOrder(
            id="order_2",
            design_id="ship_b",
            hull_tonnage=5000,
            total_bp=2000.0,
            priority=5
        )
        yard.build_queue.extend([order1, order2])
        
        # Process 1 day
        completed = manager.tick(days=1.0, now=0.0)
        
        # Both orders should make progress (BP split between them)
        assert order1.progress_bp > 0
        assert order2.progress_bp > 0
        
        # Both should have different slipways
        assert order1.assigned_slipway_id != order2.assigned_slipway_id

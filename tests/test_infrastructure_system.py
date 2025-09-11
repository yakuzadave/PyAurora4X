"""
Tests for the enhanced colony infrastructure system.

Tests building construction, resource production, construction queues,
and infrastructure management functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock

from pyaurora4x.core.models import Colony, Empire
from pyaurora4x.core.enums import BuildingType, ConstructionStatus, TechnologyType
from pyaurora4x.core.infrastructure import (
    BuildingTemplate, Building, ConstructionProject, 
    ColonyInfrastructureState, get_default_building_templates
)
from pyaurora4x.engine.infrastructure_manager import ColonyInfrastructureManager


@pytest.fixture
def empire():
    """Create a test empire."""
    empire = Empire(
        id="test_empire",
        name="Test Empire",
        home_system_id="system_1",
        home_planet_id="planet_1"
    )
    # Add some basic technologies
    empire.technologies = {
        "engineering": Mock(is_researched=True),
        "physics": Mock(is_researched=True),
        "weapons": Mock(is_researched=True),
    }
    return empire


@pytest.fixture
def colony():
    """Create a test colony."""
    colony = Colony(
        id="test_colony",
        name="Test Colony",
        empire_id="test_empire",
        planet_id="test_planet",
        population=1000,
        max_population=1000
    )
    # Initialize with some basic resources
    colony.stockpiles = {
        "minerals": 1000.0,
        "energy": 500.0,
        "alloys": 100.0
    }
    return colony


@pytest.fixture
def infrastructure_manager():
    """Create an infrastructure manager."""
    return ColonyInfrastructureManager()


class TestBuildingTemplates:
    """Test building template functionality."""
    
    def test_default_building_templates(self):
        """Test that default building templates are properly defined."""
        templates = get_default_building_templates()
        
        assert len(templates) > 0
        assert "basic_mine" in templates
        assert "basic_factory" in templates
        assert "research_lab" in templates
        assert "power_plant" in templates
        assert "habitat" in templates
        assert "defense_station" in templates
        
        # Check basic mine template
        mine_template = templates["basic_mine"]
        assert mine_template.building_type == BuildingType.MINE
        assert mine_template.construction_cost["minerals"] == 100
        assert mine_template.resource_production["minerals"] == 10
        assert mine_template.can_upgrade_to == "automated_mine"
    
    def test_building_template_structure(self):
        """Test building template has all required fields."""
        templates = get_default_building_templates()
        template = templates["basic_mine"]
        
        assert hasattr(template, "id")
        assert hasattr(template, "name")
        assert hasattr(template, "building_type")
        assert hasattr(template, "description")
        assert hasattr(template, "construction_cost")
        assert hasattr(template, "construction_time")
        assert hasattr(template, "resource_production")
        assert hasattr(template, "resource_consumption")
        assert hasattr(template, "upkeep_cost")


class TestInfrastructureManager:
    """Test infrastructure manager functionality."""
    
    def test_manager_initialization(self, infrastructure_manager):
        """Test infrastructure manager initializes properly."""
        assert len(infrastructure_manager.building_templates) > 0
        assert infrastructure_manager.colony_states == {}
        assert infrastructure_manager.buildings == {}
        assert infrastructure_manager.construction_projects == {}
    
    def test_colony_initialization(self, infrastructure_manager, colony):
        """Test colony infrastructure initialization."""
        state = infrastructure_manager.initialize_colony_infrastructure(colony)
        
        assert state.colony_id == colony.id
        assert colony.id in infrastructure_manager.colony_states
        assert infrastructure_manager.get_colony_state(colony.id) == state
    
    def test_legacy_infrastructure_conversion(self, infrastructure_manager, colony):
        """Test conversion of legacy infrastructure to new system."""
        # Set up legacy infrastructure
        colony.infrastructure = {"mine": 2}
        
        state = infrastructure_manager.initialize_colony_infrastructure(colony)
        
        # Should have converted 2 mines to 2 buildings
        assert len(state.buildings) == 2
        for building_id, building in state.buildings.items():
            building_obj = infrastructure_manager.buildings[building_id]
            assert building_obj.template_id == "basic_mine"
    
    def test_available_buildings(self, infrastructure_manager, empire):
        """Test getting available buildings for an empire."""
        available = infrastructure_manager.get_available_buildings(empire)
        
        assert len(available) > 0
        
        # Should include basic buildings that don't require tech
        basic_buildings = [b for b in available if not b.tech_requirements]
        assert len(basic_buildings) > 0
        
        # Should include buildings requiring available tech
        engineering_buildings = [
            b for b in available 
            if TechnologyType.ENGINEERING in b.tech_requirements
        ]
        assert len(engineering_buildings) > 0


class TestBuildingConstruction:
    """Test building construction functionality."""
    
    def test_can_build_basic_building(self, infrastructure_manager, colony, empire):
        """Test checking if a basic building can be constructed."""
        can_build, reason = infrastructure_manager.can_build(colony, empire, "basic_mine")
        assert can_build
        assert reason == "Can build"
    
    def test_cannot_build_without_resources(self, infrastructure_manager, colony, empire):
        """Test building cannot be constructed without sufficient resources."""
        # Remove all resources
        colony.stockpiles = {}
        
        can_build, reason = infrastructure_manager.can_build(colony, empire, "basic_mine")
        assert not can_build
        assert "Insufficient" in reason
    
    def test_cannot_build_without_tech(self, infrastructure_manager, colony, empire):
        """Test building cannot be constructed without required technology."""
        # Remove engineering technology
        empire.technologies = {}
        
        can_build, reason = infrastructure_manager.can_build(colony, empire, "automated_mine")
        assert not can_build
        assert "Missing technology" in reason
    
    def test_cannot_build_without_population(self, infrastructure_manager, colony, empire):
        """Test building cannot be constructed without sufficient population."""
        # Set low population
        colony.population = 5
        
        can_build, reason = infrastructure_manager.can_build(colony, empire, "basic_mine")
        assert not can_build
        assert "Insufficient population" in reason
    
    def test_start_construction(self, infrastructure_manager, colony, empire):
        """Test starting construction of a building."""
        infrastructure_manager.initialize_colony_infrastructure(colony)
        
        success, message = infrastructure_manager.start_construction(
            colony, empire, "basic_mine", priority=5
        )
        
        assert success
        assert "started" in message
        
        state = infrastructure_manager.get_colony_state(colony.id)
        assert len(state.construction_projects) == 1
        assert len(state.construction_queue) == 1
        
        project_id = state.construction_queue[0]
        project = state.construction_projects[project_id]
        assert project.building_template_id == "basic_mine"
        assert project.priority == 5
        assert project.status == ConstructionStatus.PLANNED
    
    def test_construction_queue_priority(self, infrastructure_manager, colony, empire):
        """Test construction queue is ordered by priority."""
        infrastructure_manager.initialize_colony_infrastructure(colony)
        
        # Add buildings with different priorities
        infrastructure_manager.start_construction(colony, empire, "basic_mine", priority=3)
        infrastructure_manager.start_construction(colony, empire, "power_plant", priority=8)
        infrastructure_manager.start_construction(colony, empire, "habitat", priority=1)
        
        state = infrastructure_manager.get_colony_state(colony.id)
        assert len(state.construction_queue) == 3
        
        # Queue should be ordered by priority (highest first)
        priorities = []
        for project_id in state.construction_queue:
            project = state.construction_projects[project_id]
            priorities.append(project.priority)
        
        assert priorities == [8, 3, 1]
    
    def test_cancel_construction(self, infrastructure_manager, colony, empire):
        """Test cancelling construction projects."""
        infrastructure_manager.initialize_colony_infrastructure(colony)
        
        # Start construction
        success, _ = infrastructure_manager.start_construction(colony, empire, "basic_mine")
        assert success
        
        state = infrastructure_manager.get_colony_state(colony.id)
        project_id = state.construction_queue[0]
        
        # Cancel construction
        success = infrastructure_manager.cancel_construction(colony.id, project_id)
        assert success
        
        # Project should be removed
        assert len(state.construction_projects) == 0
        assert len(state.construction_queue) == 0


class TestResourceProduction:
    """Test resource production and consumption."""
    
    def test_building_production_calculation(self, infrastructure_manager, colony, empire):
        """Test that building production is calculated correctly."""
        # Initialize and add a basic mine
        state = infrastructure_manager.initialize_colony_infrastructure(colony)
        building = infrastructure_manager._create_building(colony.id, "basic_mine")
        state.buildings[building.id] = building
        infrastructure_manager.buildings[building.id] = building
        
        # Update production calculations
        infrastructure_manager._update_colony_production(colony, state)
        
        # Should produce 10 minerals per day
        assert state.daily_production["minerals"] == 10.0
        assert state.net_production["minerals"] == 10.0
        assert colony.production["minerals"] == 10.0
    
    def test_building_consumption(self, infrastructure_manager, colony, empire):
        """Test building resource consumption."""
        # Initialize and add a factory (consumes minerals, produces alloys)
        state = infrastructure_manager.initialize_colony_infrastructure(colony)
        building = infrastructure_manager._create_building(colony.id, "basic_factory")
        state.buildings[building.id] = building
        infrastructure_manager.buildings[building.id] = building
        
        # Update production calculations
        infrastructure_manager._update_colony_production(colony, state)
        
        # Should consume 8 minerals and produce 5 alloys per day
        assert state.daily_consumption["minerals"] == 8.0
        assert state.daily_production["alloys"] == 5.0
        assert state.net_production["minerals"] == -8.0
        assert state.net_production["alloys"] == 5.0
    
    def test_power_generation_and_consumption(self, infrastructure_manager, colony, empire):
        """Test power generation and consumption tracking."""
        state = infrastructure_manager.initialize_colony_infrastructure(colony)
        
        # Add power plant (generates energy)
        power_plant = infrastructure_manager._create_building(colony.id, "power_plant")
        state.buildings[power_plant.id] = power_plant
        infrastructure_manager.buildings[power_plant.id] = power_plant
        
        # Add factory (consumes power)
        factory = infrastructure_manager._create_building(colony.id, "basic_factory")
        state.buildings[factory.id] = factory
        infrastructure_manager.buildings[factory.id] = factory
        
        # Update production
        infrastructure_manager._update_colony_production(colony, state)
        
        # Check power balance
        assert state.total_power_generation > 0  # Power plant generates
        assert state.total_power_consumption > 0  # Factory consumes
        assert colony.power_generation > 0
        assert colony.power_consumption > 0
    
    def test_population_capacity(self, infrastructure_manager, colony, empire):
        """Test population capacity calculation."""
        state = infrastructure_manager.initialize_colony_infrastructure(colony)
        
        # Add habitat (increases population capacity)
        habitat = infrastructure_manager._create_building(colony.id, "habitat")
        state.buildings[habitat.id] = habitat
        infrastructure_manager.buildings[habitat.id] = habitat
        
        # Update production
        infrastructure_manager._update_colony_production(colony, state)
        
        # Should increase population capacity
        assert state.total_population_capacity > 1000  # More than base 1000
        assert colony.max_population > 1000


class TestConstructionProcessing:
    """Test construction processing over time."""
    
    def test_construction_progression(self, infrastructure_manager, colony, empire):
        """Test construction progresses over time."""
        infrastructure_manager.initialize_colony_infrastructure(colony)
        
        # Start construction
        infrastructure_manager.start_construction(colony, empire, "basic_mine")
        state = infrastructure_manager.get_colony_state(colony.id)
        project_id = state.construction_queue[0]
        project = state.construction_projects[project_id]
        
        # Initially should be planned
        assert project.status == ConstructionStatus.PLANNED
        assert project.progress == 0.0
        
        # Process construction for half the build time
        template = infrastructure_manager.building_templates["basic_mine"]
        half_build_time = template.construction_time / 2
        infrastructure_manager.process_construction(colony, empire, half_build_time)
        
        # Should be in progress and about 50% complete
        assert project.status == ConstructionStatus.IN_PROGRESS
        assert 0.4 < project.progress < 0.6  # Approximately 50%
    
    def test_construction_completion(self, infrastructure_manager, colony, empire):
        """Test construction completes and creates building."""
        infrastructure_manager.initialize_colony_infrastructure(colony)
        
        # Start construction
        infrastructure_manager.start_construction(colony, empire, "basic_mine")
        state = infrastructure_manager.get_colony_state(colony.id)
        initial_building_count = len(state.buildings)
        
        # Process construction for full build time
        template = infrastructure_manager.building_templates["basic_mine"]
        infrastructure_manager.process_construction(colony, empire, template.construction_time)
        
        # Should have completed and created building
        assert len(state.buildings) == initial_building_count + 1
        assert len(state.construction_projects) == 0
        assert len(state.construction_queue) == 0
        
        # Colony should have the building in its buildings dict
        assert len(colony.buildings) == 1


class TestBuildingOperations:
    """Test building operations like upgrade and demolish."""
    
    def test_building_upgrade(self, infrastructure_manager, colony, empire):
        """Test upgrading a building."""
        state = infrastructure_manager.initialize_colony_infrastructure(colony)
        
        # Create a basic mine
        building = infrastructure_manager._create_building(colony.id, "basic_mine")
        state.buildings[building.id] = building
        infrastructure_manager.buildings[building.id] = building
        colony.buildings[building.id] = "basic_mine"
        
        # Upgrade the building
        success, message = infrastructure_manager.upgrade_building(
            colony, empire, building.id
        )
        
        assert success
        assert "started" in message.lower()
        
        # Should have started construction of automated mine
        assert len(state.construction_projects) == 1
        project = list(state.construction_projects.values())[0]
        assert project.building_template_id == "automated_mine"
        assert project.priority == 8  # High priority for upgrades
    
    def test_building_demolish(self, infrastructure_manager, colony, empire):
        """Test demolishing a building."""
        state = infrastructure_manager.initialize_colony_infrastructure(colony)
        
        # Create a basic mine
        building = infrastructure_manager._create_building(colony.id, "basic_mine")
        state.buildings[building.id] = building
        infrastructure_manager.buildings[building.id] = building
        colony.buildings[building.id] = "basic_mine"
        
        initial_minerals = colony.stockpiles.get("minerals", 0)
        
        # Demolish the building
        success = infrastructure_manager.demolish_building(colony, building.id)
        assert success
        
        # Building should be removed
        assert building.id not in state.buildings
        assert building.id not in infrastructure_manager.buildings
        assert building.id not in colony.buildings
        
        # Should get resource refund (25% of construction cost)
        template = infrastructure_manager.building_templates["basic_mine"]
        expected_refund = template.construction_cost["minerals"] * 0.25
        assert colony.stockpiles["minerals"] == initial_minerals + expected_refund
    
    def test_get_building_info(self, infrastructure_manager):
        """Test getting building information."""
        # Create a building
        building = infrastructure_manager._create_building("test_colony", "basic_mine")
        infrastructure_manager.buildings[building.id] = building
        
        info = infrastructure_manager.get_building_info(building.id)
        
        assert info is not None
        assert "building" in info
        assert "template" in info
        assert "daily_production" in info
        assert "daily_consumption" in info
        assert "upkeep" in info
        assert "efficiency" in info
        
        assert info["building"] == building
        assert info["template"].id == "basic_mine"


class TestIntegrationScenarios:
    """Test integrated scenarios combining multiple features."""
    
    def test_complete_colony_development(self, infrastructure_manager, colony, empire):
        """Test a complete colony development scenario."""
        # Initialize colony
        infrastructure_manager.initialize_colony_infrastructure(colony)
        
        # Build initial infrastructure
        infrastructure_manager.start_construction(colony, empire, "power_plant", priority=10)
        infrastructure_manager.start_construction(colony, empire, "basic_mine", priority=8)
        infrastructure_manager.start_construction(colony, empire, "habitat", priority=6)
        
        state = infrastructure_manager.get_colony_state(colony.id)
        assert len(state.construction_queue) == 3
        
        # Process construction over time to complete all buildings
        total_construction_time = sum(
            infrastructure_manager.building_templates[project.building_template_id].construction_time
            for project in state.construction_projects.values()
        )
        
        # Process in chunks to simulate realistic progression
        for _ in range(10):
            infrastructure_manager.process_construction(
                colony, empire, total_construction_time / 10
            )
        
        # All construction should be completed
        assert len(state.construction_projects) == 0
        assert len(state.buildings) == 3
        
        # Colony should have improved capabilities
        infrastructure_manager._update_colony_production(colony, state)
        assert state.total_power_generation > 0
        assert state.total_population_capacity > 1000
        assert state.daily_production.get("minerals", 0) > 0
    
    def test_resource_shortage_handling(self, infrastructure_manager, colony, empire):
        """Test handling of resource shortages during construction."""
        infrastructure_manager.initialize_colony_infrastructure(colony)
        
        # Start construction with sufficient resources
        infrastructure_manager.start_construction(colony, empire, "basic_mine")
        
        # Reduce resources to simulate shortage
        colony.stockpiles = {"minerals": 1.0, "energy": 1.0}  # Very low
        
        # Process construction - should not progress much due to resource shortage
        template = infrastructure_manager.building_templates["basic_mine"]
        infrastructure_manager.process_construction(colony, empire, template.construction_time)
        
        state = infrastructure_manager.get_colony_state(colony.id)
        project = list(state.construction_projects.values())[0]
        
        # Construction should still be in progress but with minimal progress
        assert project.status == ConstructionStatus.IN_PROGRESS
        assert project.progress < 0.1  # Very little progress due to resource shortage


if __name__ == "__main__":
    pytest.main([__file__])

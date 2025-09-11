"""
Infrastructure and Building System for PyAurora 4X

Defines buildings, construction projects, and resource production chains
for enhanced colony management.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from pyaurora4x.core.enums import BuildingType, ConstructionStatus, TechnologyType, ResourceType


class BuildingTemplate(BaseModel):
    """Template defining a building type and its properties."""
    
    id: str
    name: str
    building_type: BuildingType
    description: str
    
    # Construction requirements
    construction_cost: Dict[str, float] = Field(default_factory=dict)  # Resource type -> amount
    construction_time: float = 86400.0  # seconds (default 1 day)
    power_requirement: float = 0.0
    population_requirement: int = 0
    
    # Technology prerequisites
    tech_requirements: List[TechnologyType] = Field(default_factory=list)
    
    # Production capabilities
    resource_production: Dict[str, float] = Field(default_factory=dict)  # per day
    resource_consumption: Dict[str, float] = Field(default_factory=dict)  # per day
    
    # Special effects and bonuses
    population_capacity: int = 0
    research_bonus: Dict[TechnologyType, float] = Field(default_factory=dict)
    defense_value: float = 0.0
    happiness_modifier: float = 0.0
    
    # Maintenance costs
    upkeep_cost: Dict[str, float] = Field(default_factory=dict)  # per day
    
    # Upgrade information
    can_upgrade_to: Optional[str] = None  # Building template ID
    upgrade_cost_multiplier: float = 1.5


class Building(BaseModel):
    """An actual building instance in a colony."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    template_id: str
    colony_id: str
    
    # Status
    status: str = "operational"  # operational, damaged, under_maintenance
    efficiency: float = 1.0  # 0.0 to 1.0 multiplier for production
    built_date: float = 0.0
    last_maintained: float = 0.0
    
    # Customization
    name: Optional[str] = None  # Custom name for this building instance


class ConstructionProject(BaseModel):
    """A building under construction or planned for construction."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    colony_id: str
    building_template_id: str
    
    # Construction progress
    status: ConstructionStatus = ConstructionStatus.PLANNED
    progress: float = 0.0  # 0.0 to 1.0 (percentage complete)
    estimated_completion: Optional[float] = None
    
    # Resource allocation
    resources_invested: Dict[str, float] = Field(default_factory=dict)
    daily_resource_allocation: Dict[str, float] = Field(default_factory=dict)
    
    # Priority and management
    priority: int = 1  # 1-10, higher numbers = higher priority
    started_date: Optional[float] = None
    paused: bool = False
    
    # Construction details
    total_cost: Dict[str, float] = Field(default_factory=dict)
    construction_time: float = 86400.0


class ResourceProductionChain(BaseModel):
    """Defines complex resource production relationships."""
    
    id: str
    name: str
    description: str
    
    # Input requirements
    inputs: Dict[str, float] = Field(default_factory=dict)  # resource -> amount per day
    
    # Output production
    outputs: Dict[str, float] = Field(default_factory=dict)  # resource -> amount per day
    
    # Requirements
    required_buildings: List[BuildingType] = Field(default_factory=list)
    required_population: int = 0
    power_consumption: float = 0.0
    
    # Efficiency factors
    base_efficiency: float = 1.0
    technology_modifiers: Dict[TechnologyType, float] = Field(default_factory=dict)


class ColonyInfrastructureState(BaseModel):
    """Current infrastructure state of a colony."""
    
    colony_id: str
    
    # Buildings
    buildings: Dict[str, Building] = Field(default_factory=dict)  # building_id -> building
    construction_queue: List[str] = Field(default_factory=list)  # construction_project_ids in order
    construction_projects: Dict[str, ConstructionProject] = Field(default_factory=dict)
    
    # Resource production summary (calculated)
    daily_production: Dict[str, float] = Field(default_factory=dict)
    daily_consumption: Dict[str, float] = Field(default_factory=dict)
    net_production: Dict[str, float] = Field(default_factory=dict)
    
    # Infrastructure totals (calculated)
    total_power_generation: float = 0.0
    total_power_consumption: float = 0.0
    total_population_capacity: int = 1000  # Default capacity
    total_defense_value: float = 0.0
    
    # Efficiency factors
    overall_efficiency: float = 1.0
    happiness_modifier: float = 0.0
    
    # Last update timestamp
    last_updated: float = 0.0


# Default building templates for the game
def get_default_building_templates() -> Dict[str, BuildingTemplate]:
    """Returns the default set of building templates."""
    
    templates = {}
    
    # Basic Mine
    templates["basic_mine"] = BuildingTemplate(
        id="basic_mine",
        name="Mine",
        building_type=BuildingType.MINE,
        description="Basic mineral extraction facility",
        construction_cost={"minerals": 100, "energy": 50},
        construction_time=86400,  # 1 day
        population_requirement=10,
        resource_production={"minerals": 10},
        upkeep_cost={"energy": 2},
        can_upgrade_to="automated_mine"
    )
    
    # Automated Mine
    templates["automated_mine"] = BuildingTemplate(
        id="automated_mine",
        name="Automated Mine",
        building_type=BuildingType.AUTOMATED_MINE,
        description="Automated mineral extraction with higher output",
        construction_cost={"minerals": 200, "energy": 100, "alloys": 50},
        construction_time=172800,  # 2 days
        tech_requirements=[TechnologyType.ENGINEERING],
        population_requirement=5,
        resource_production={"minerals": 25},
        upkeep_cost={"energy": 5},
        can_upgrade_to="deep_core_mine"
    )
    
    # Basic Factory
    templates["basic_factory"] = BuildingTemplate(
        id="basic_factory",
        name="Factory",
        building_type=BuildingType.FACTORY,
        description="Basic manufacturing facility",
        construction_cost={"minerals": 150, "energy": 100},
        construction_time=129600,  # 1.5 days
        population_requirement=20,
        power_requirement=10,
        resource_consumption={"minerals": 8},
        resource_production={"alloys": 5},
        upkeep_cost={"energy": 3},
        can_upgrade_to="automated_factory"
    )
    
    # Research Lab
    templates["research_lab"] = BuildingTemplate(
        id="research_lab",
        name="Research Laboratory",
        building_type=BuildingType.RESEARCH_LAB,
        description="Basic research facility",
        construction_cost={"minerals": 200, "energy": 150, "alloys": 50},
        construction_time=172800,  # 2 days
        population_requirement=15,
        power_requirement=15,
        resource_consumption={"energy": 10},
        resource_production={"research": 8},
        research_bonus={TechnologyType.PHYSICS: 0.1, TechnologyType.ENGINEERING: 0.1},
        upkeep_cost={"energy": 5},
        can_upgrade_to="advanced_lab"
    )
    
    # Power Plant
    templates["power_plant"] = BuildingTemplate(
        id="power_plant",
        name="Power Plant",
        building_type=BuildingType.POWER_PLANT,
        description="Generates energy for colony operations",
        construction_cost={"minerals": 120, "alloys": 30},
        construction_time=86400,
        population_requirement=8,
        resource_consumption={"minerals": 3},
        resource_production={"energy": 20},
        upkeep_cost={"minerals": 1},
        can_upgrade_to="fusion_plant"
    )
    
    # Habitat
    templates["habitat"] = BuildingTemplate(
        id="habitat",
        name="Habitat Module",
        building_type=BuildingType.HABITAT,
        description="Provides housing for colonists",
        construction_cost={"minerals": 80, "energy": 40},
        construction_time=64800,  # 18 hours
        population_capacity=500,
        happiness_modifier=0.1,
        upkeep_cost={"energy": 2}
    )
    
    # Defense Station
    templates["defense_station"] = BuildingTemplate(
        id="defense_station",
        name="Defense Station",
        building_type=BuildingType.DEFENSE_STATION,
        description="Provides basic planetary defense",
        construction_cost={"minerals": 200, "alloys": 100, "energy": 80},
        construction_time=259200,  # 3 days
        tech_requirements=[TechnologyType.WEAPONS],
        population_requirement=25,
        power_requirement=20,
        defense_value=50.0,
        upkeep_cost={"energy": 8, "alloys": 2}
    )
    
    return templates

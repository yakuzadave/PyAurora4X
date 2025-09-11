"""
Colony Infrastructure Manager for PyAurora 4X

Manages building construction, resource production, and infrastructure effects
for all colonies in the game.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import uuid

from pyaurora4x.core.models import Colony, Empire
from pyaurora4x.core.enums import BuildingType, ConstructionStatus, TechnologyType
from pyaurora4x.core.infrastructure import (
    BuildingTemplate, 
    Building, 
    ConstructionProject, 
    ColonyInfrastructureState,
    get_default_building_templates
)

logger = logging.getLogger(__name__)


class ColonyInfrastructureManager:
    """Manages colony infrastructure, buildings, and construction."""
    
    def __init__(self):
        self.building_templates: Dict[str, BuildingTemplate] = get_default_building_templates()
        self.colony_states: Dict[str, ColonyInfrastructureState] = {}  # colony_id -> state
        self.buildings: Dict[str, Building] = {}  # building_id -> building
        self.construction_projects: Dict[str, ConstructionProject] = {}  # project_id -> project
    
    def initialize_colony_infrastructure(self, colony: Colony) -> ColonyInfrastructureState:
        """Initialize infrastructure state for a new colony."""
        if colony.id in self.colony_states:
            return self.colony_states[colony.id]
        
        state = ColonyInfrastructureState(colony_id=colony.id)
        
        # Add starter buildings based on colony infrastructure
        if colony.infrastructure:
            for infra_type, count in colony.infrastructure.items():
                if infra_type == "mine" and count > 0:
                    # Convert legacy mines to new building system
                    for _ in range(count):
                        building = self._create_building(colony.id, "basic_mine")
                        state.buildings[building.id] = building
                        self.buildings[building.id] = building
        
        # Calculate initial production
        self._update_colony_production(colony, state)
        
        self.colony_states[colony.id] = state
        logger.info("Initialized infrastructure for colony %s", colony.name)
        return state
    
    def get_colony_state(self, colony_id: str) -> Optional[ColonyInfrastructureState]:
        """Get infrastructure state for a colony."""
        return self.colony_states.get(colony_id)
    
    def get_available_buildings(self, empire: Empire) -> List[BuildingTemplate]:
        """Get buildings available for construction by an empire."""
        available = []
        
        for template in self.building_templates.values():
            # Check technology requirements
            can_build = True
            for tech_req in template.tech_requirements:
                if tech_req not in empire.technologies or not empire.technologies[tech_req].is_researched:
                    can_build = False
                    break
            
            if can_build:
                available.append(template)
        
        return available
    
    def can_build(self, colony: Colony, empire: Empire, template_id: str) -> Tuple[bool, str]:
        """Check if a building can be constructed in a colony."""
        template = self.building_templates.get(template_id)
        if not template:
            return False, f"Unknown building template: {template_id}"
        
        # Check technology requirements
        for tech_req in template.tech_requirements:
            if tech_req not in empire.technologies or not empire.technologies[tech_req].is_researched:
                return False, f"Missing technology: {tech_req.value}"
        
        # Check resource requirements
        for resource, cost in template.construction_cost.items():
            if colony.stockpiles.get(resource, 0) < cost:
                return False, f"Insufficient {resource}: need {cost}, have {colony.stockpiles.get(resource, 0)}"
        
        # Check population requirements
        if template.population_requirement > 0:
            available_pop = colony.population
            # Subtract population already assigned to buildings
            state = self.get_colony_state(colony.id)
            if state:
                for building_id, building in state.buildings.items():
                    building_template = self.building_templates.get(self.buildings[building_id].template_id)
                    if building_template:
                        available_pop -= building_template.population_requirement
            
            if available_pop < template.population_requirement:
                return False, f"Insufficient population: need {template.population_requirement}, have {available_pop} available"
        
        return True, "Can build"
    
    def start_construction(self, colony: Colony, empire: Empire, template_id: str, priority: int = 5) -> Tuple[bool, str]:
        """Start construction of a building."""
        can_build, reason = self.can_build(colony, empire, template_id)
        if not can_build:
            return False, reason
        
        template = self.building_templates[template_id]
        
        # Create construction project
        project = ConstructionProject(
            colony_id=colony.id,
            building_template_id=template_id,
            status=ConstructionStatus.PLANNED,
            priority=priority,
            total_cost=template.construction_cost.copy(),
            construction_time=template.construction_time
        )
        
        # Add to colony state
        state = self.get_colony_state(colony.id)
        if not state:
            state = self.initialize_colony_infrastructure(colony)
        
        state.construction_projects[project.id] = project
        state.construction_queue.append(project.id)
        self.construction_projects[project.id] = project
        
        # Sort queue by priority
        state.construction_queue.sort(
            key=lambda pid: state.construction_projects[pid].priority, 
            reverse=True
        )
        
        logger.info("Started construction of %s in colony %s", template.name, colony.name)
        return True, f"Construction of {template.name} started"
    
    def cancel_construction(self, colony_id: str, project_id: str) -> bool:
        """Cancel a construction project and refund resources."""
        state = self.get_colony_state(colony_id)
        if not state or project_id not in state.construction_projects:
            return False
        
        project = state.construction_projects[project_id]
        
        # Refund invested resources (partial refund based on progress)
        refund_rate = 0.5 if project.status == ConstructionStatus.IN_PROGRESS else 1.0
        
        # Remove from queue and projects
        if project_id in state.construction_queue:
            state.construction_queue.remove(project_id)
        del state.construction_projects[project_id]
        del self.construction_projects[project_id]
        
        logger.info("Cancelled construction project %s", project_id)
        return True
    
    def process_construction(self, colony: Colony, empire: Empire, delta_seconds: float) -> None:
        """Process construction progress for a colony."""
        state = self.get_colony_state(colony.id)
        if not state or not state.construction_queue:
            return
        
        # Process the highest priority project
        project_id = state.construction_queue[0]
        project = state.construction_projects.get(project_id)
        if not project:
            return
        
        template = self.building_templates.get(project.building_template_id)
        if not template:
            return
        
        # Start construction if planned
        if project.status == ConstructionStatus.PLANNED:
            # Check if we have resources to start
            can_start = all(
                colony.stockpiles.get(resource, 0) >= cost * 0.1  # Need 10% up front
                for resource, cost in template.construction_cost.items()
            )
            
            if can_start:
                project.status = ConstructionStatus.IN_PROGRESS
                project.started_date = 0.0  # Would use current game time
        
        # Process ongoing construction
        if project.status == ConstructionStatus.IN_PROGRESS:
            # Calculate daily progress (assuming construction time is in seconds)
            daily_progress = delta_seconds / template.construction_time
            
            # Check resource availability for continued construction
            daily_resource_needed = {
                resource: cost * daily_progress
                for resource, cost in template.construction_cost.items()
            }
            
            can_continue = all(
                colony.stockpiles.get(resource, 0) >= needed
                for resource, needed in daily_resource_needed.items()
            )
            
            if can_continue:
                # Consume resources
                for resource, needed in daily_resource_needed.items():
                    colony.stockpiles[resource] = colony.stockpiles.get(resource, 0) - needed
                    project.resources_invested[resource] = project.resources_invested.get(resource, 0) + needed
                
                # Update progress
                project.progress = min(1.0, project.progress + daily_progress)
                
                # Complete construction
                if project.progress >= 1.0:
                    self._complete_construction(colony, project)
    
    def _complete_construction(self, colony: Colony, project: ConstructionProject) -> None:
        """Complete a construction project."""
        template = self.building_templates.get(project.building_template_id)
        if not template:
            return
        
        # Create the building
        building = self._create_building(colony.id, project.building_template_id)
        
        # Add to colony state
        state = self.get_colony_state(colony.id)
        if state:
            state.buildings[building.id] = building
            
            # Remove project from queue
            if project.id in state.construction_queue:
                state.construction_queue.remove(project.id)
            if project.id in state.construction_projects:
                del state.construction_projects[project.id]
        
        # Add to global buildings registry
        self.buildings[building.id] = building
        
        # Update colony buildings dict (for compatibility)
        colony.buildings[building.id] = template.id
        
        # Remove project from global registry
        if project.id in self.construction_projects:
            del self.construction_projects[project.id]
        
        # Update production
        self._update_colony_production(colony, state)
        
        logger.info("Completed construction of %s in colony %s", template.name, colony.name)
    
    def _create_building(self, colony_id: str, template_id: str) -> Building:
        """Create a new building instance."""
        return Building(
            template_id=template_id,
            colony_id=colony_id,
            status="operational",
            efficiency=1.0,
            built_date=0.0  # Would use current game time
        )
    
    def _update_colony_production(self, colony: Colony, state: ColonyInfrastructureState) -> None:
        """Update resource production for a colony."""
        # Reset production/consumption
        state.daily_production.clear()
        state.daily_consumption.clear()
        state.net_production.clear()
        
        state.total_power_generation = 0.0
        state.total_power_consumption = 0.0
        state.total_population_capacity = 1000  # Base capacity
        state.total_defense_value = 0.0
        
        # Process each building
        for building_id, building in state.buildings.items():
            template = self.building_templates.get(building.template_id)
            if not template:
                continue
            
            efficiency = building.efficiency * state.overall_efficiency
            
            # Production
            for resource, amount in template.resource_production.items():
                daily_amount = amount * efficiency
                state.daily_production[resource] = state.daily_production.get(resource, 0) + daily_amount
                colony.production[resource] = colony.production.get(resource, 0) + daily_amount
            
            # Consumption
            for resource, amount in template.resource_consumption.items():
                daily_amount = amount * efficiency
                state.daily_consumption[resource] = state.daily_consumption.get(resource, 0) + daily_amount
                colony.consumption[resource] = colony.consumption.get(resource, 0) + daily_amount
            
            # Infrastructure effects
            if template.power_requirement > 0:
                state.total_power_consumption += template.power_requirement
                colony.power_consumption += template.power_requirement
            
            for resource, amount in template.resource_production.items():
                if resource == "energy":
                    state.total_power_generation += amount * efficiency
                    colony.power_generation += amount * efficiency
            
            # Population capacity
            state.total_population_capacity += template.population_capacity
            colony.max_population = state.total_population_capacity
            
            # Defense value
            state.total_defense_value += template.defense_value
            colony.defense_rating += template.defense_value
        
        # Calculate net production
        for resource in set(list(state.daily_production.keys()) + list(state.daily_consumption.keys())):
            production = state.daily_production.get(resource, 0)
            consumption = state.daily_consumption.get(resource, 0)
            state.net_production[resource] = production - consumption
        
        state.last_updated = 0.0  # Would use current game time
    
    def get_building_info(self, building_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a building."""
        building = self.buildings.get(building_id)
        if not building:
            return None
        
        template = self.building_templates.get(building.template_id)
        if not template:
            return None
        
        return {
            "building": building,
            "template": template,
            "daily_production": template.resource_production,
            "daily_consumption": template.resource_consumption,
            "upkeep": template.upkeep_cost,
            "efficiency": building.efficiency
        }
    
    def upgrade_building(self, colony: Colony, empire: Empire, building_id: str) -> Tuple[bool, str]:
        """Upgrade a building to its next tier."""
        building = self.buildings.get(building_id)
        if not building:
            return False, "Building not found"
        
        template = self.building_templates.get(building.template_id)
        if not template or not template.can_upgrade_to:
            return False, "Building cannot be upgraded"
        
        upgrade_template = self.building_templates.get(template.can_upgrade_to)
        if not upgrade_template:
            return False, "Upgrade template not found"
        
        # Check if we can build the upgrade
        can_build, reason = self.can_build(colony, empire, upgrade_template.id)
        if not can_build:
            return False, f"Cannot upgrade: {reason}"
        
        # Calculate upgrade cost (base cost * multiplier - refund from old building)
        upgrade_cost = {}
        for resource, cost in upgrade_template.construction_cost.items():
            adjusted_cost = cost * template.upgrade_cost_multiplier
            # Partial refund from old building
            refund = template.construction_cost.get(resource, 0) * 0.25
            upgrade_cost[resource] = max(0, adjusted_cost - refund)
        
        # Check resources
        for resource, cost in upgrade_cost.items():
            if colony.stockpiles.get(resource, 0) < cost:
                return False, f"Insufficient {resource} for upgrade"
        
        # Start upgrade as construction project
        return self.start_construction(colony, empire, upgrade_template.id, priority=8)
    
    def demolish_building(self, colony: Colony, building_id: str) -> bool:
        """Demolish a building and get partial resource refund."""
        building = self.buildings.get(building_id)
        if not building or building.colony_id != colony.id:
            return False
        
        template = self.building_templates.get(building.template_id)
        if not template:
            return False
        
        # Remove from colony state
        state = self.get_colony_state(colony.id)
        if state and building_id in state.buildings:
            del state.buildings[building_id]
        
        # Remove from colony buildings dict
        if building_id in colony.buildings:
            del colony.buildings[building_id]
        
        # Remove from global registry
        if building_id in self.buildings:
            del self.buildings[building_id]
        
        # Refund 25% of construction costs
        refund_rate = 0.25
        for resource, cost in template.construction_cost.items():
            refund = cost * refund_rate
            colony.stockpiles[resource] = colony.stockpiles.get(resource, 0) + refund
        
        # Update production
        if state:
            self._update_colony_production(colony, state)
        
        logger.info("Demolished %s in colony %s", template.name, colony.name)
        return True

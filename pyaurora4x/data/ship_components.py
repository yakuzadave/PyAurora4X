"""
Ship Components Manager for PyAurora 4X

Manages ship components, designs, and construction systems.
"""

import json
from typing import Dict, List, Optional
from pathlib import Path
import logging

from pyaurora4x.core.models import ShipComponent, ShipDesign
from pyaurora4x.core.enums import ShipType

logger = logging.getLogger(__name__)


class ShipComponentManager:
    """
    Manages ship components and designs.
    
    Loads component definitions from JSON files and provides
    ship design validation and construction logic.
    """
    
    def __init__(self, data_directory: str = "data"):
        """
        Initialize the ship component manager.
        
        Args:
            data_directory: Directory containing component data files
        """
        self.data_directory = Path(data_directory)
        self.components: Dict[str, ShipComponent] = {}
        self.designs: Dict[str, ShipDesign] = {}
        self.components_loaded = False
        
        # Try to load component data
        self.load_components()
    
    def load_components(self) -> bool:
        """
        Load ship components from data files.
        
        Returns:
            True if loading was successful
        """
        components_file = self.data_directory / "ship_components.json"
        
        if not components_file.exists():
            logger.warning(f"Components file not found: {components_file}")
            self._create_default_components()
            return False
        
        try:
            with open(components_file, 'r') as f:
                component_data = json.load(f)
            
            self._load_components_from_data(component_data)
            
            self.components_loaded = True
            logger.info(f"Loaded {len(self.components)} ship components")
            return True
            
        except Exception as e:
            logger.error(f"Error loading components: {e}")
            self._create_default_components()
            return False
    
    def _load_components_from_data(self, component_data: Dict) -> None:
        """Load components from parsed JSON data."""
        self.components.clear()
        
        for component_id, component_info in component_data.get("components", {}).items():
            try:
                # Create component object
                component = ShipComponent(
                    id=component_id,
                    name=component_info.get("name", component_id.replace("_", " ").title()),
                    component_type=component_info.get("type", "misc"),
                    mass=component_info.get("mass", 1.0),
                    cost=component_info.get("cost", 10),
                    power_requirement=component_info.get("power_requirement", 0.0),
                    crew_requirement=component_info.get("crew_requirement", 0),
                    tech_requirements=component_info.get("tech_requirements", []),
                    attributes=component_info.get("attributes", {})
                )
                
                self.components[component_id] = component
                
            except Exception as e:
                logger.error(f"Error loading component {component_id}: {e}")
    
    def _create_default_components(self) -> None:
        """Create default ship components."""
        logger.info("Creating default ship components")
        
        default_components = [
            # Engines
            {
                "id": "chemical_engine",
                "name": "Chemical Engine",
                "type": "engine",
                "mass": 50.0,
                "cost": 100,
                "power_requirement": 0.0,
                "crew_requirement": 2,
                "tech_requirements": ["basic_propulsion"],
                "attributes": {
                    "thrust": 1000.0,
                    "fuel_efficiency": 0.8,
                    "max_burn_time": 3600
                }
            },
            {
                "id": "ion_engine",
                "name": "Ion Engine",
                "type": "engine",
                "mass": 30.0,
                "cost": 200,
                "power_requirement": 100.0,
                "crew_requirement": 1,
                "tech_requirements": ["advanced_propulsion"],
                "attributes": {
                    "thrust": 100.0,
                    "fuel_efficiency": 5.0,
                    "max_burn_time": 36000
                }
            },
            
            # Power Plants
            {
                "id": "solar_panels",
                "name": "Solar Panels",
                "type": "power_plant",
                "mass": 20.0,
                "cost": 50,
                "power_requirement": 0.0,
                "crew_requirement": 0,
                "tech_requirements": ["basic_energy"],
                "attributes": {
                    "power_output": 50.0,
                    "efficiency": 0.15,
                    "degradation_rate": 0.01
                }
            },
            {
                "id": "nuclear_reactor",
                "name": "Nuclear Reactor",
                "type": "power_plant",
                "mass": 100.0,
                "cost": 500,
                "power_requirement": 0.0,
                "crew_requirement": 5,
                "tech_requirements": ["nuclear_power"],
                "attributes": {
                    "power_output": 1000.0,
                    "fuel_consumption": 1.0,
                    "heat_generation": 500.0
                }
            },
            
            # Fuel Tanks
            {
                "id": "basic_fuel_tank",
                "name": "Basic Fuel Tank",
                "type": "fuel_tank",
                "mass": 10.0,
                "cost": 20,
                "power_requirement": 0.0,
                "crew_requirement": 0,
                "tech_requirements": [],
                "attributes": {
                    "fuel_capacity": 1000.0,
                    "fuel_type": "chemical"
                }
            },
            {
                "id": "advanced_fuel_tank",
                "name": "Advanced Fuel Tank",
                "type": "fuel_tank",
                "mass": 15.0,
                "cost": 40,
                "power_requirement": 0.0,
                "crew_requirement": 0,
                "tech_requirements": ["fuel_efficiency"],
                "attributes": {
                    "fuel_capacity": 2000.0,
                    "fuel_type": "any",
                    "self_sealing": True
                }
            },
            
            # Crew Quarters
            {
                "id": "basic_crew_quarters",
                "name": "Basic Crew Quarters",
                "type": "crew_quarters",
                "mass": 40.0,
                "cost": 80,
                "power_requirement": 10.0,
                "crew_requirement": 0,
                "tech_requirements": [],
                "attributes": {
                    "crew_capacity": 10,
                    "comfort_level": 1.0
                }
            },
            {
                "id": "luxury_crew_quarters",
                "name": "Luxury Crew Quarters",
                "type": "crew_quarters",
                "mass": 60.0,
                "cost": 200,
                "power_requirement": 20.0,
                "crew_requirement": 0,
                "tech_requirements": ["advanced_life_support"],
                "attributes": {
                    "crew_capacity": 10,
                    "comfort_level": 2.0,
                    "morale_bonus": 0.2
                }
            },
            
            # Sensors
            {
                "id": "basic_sensors",
                "name": "Basic Sensor Array",
                "type": "sensor",
                "mass": 25.0,
                "cost": 150,
                "power_requirement": 50.0,
                "crew_requirement": 1,
                "tech_requirements": ["basic_sensors"],
                "attributes": {
                    "detection_range": 1000000.0,
                    "resolution": 1.0,
                    "scan_time": 60.0
                }
            },
            {
                "id": "advanced_sensors",
                "name": "Advanced Sensor Array",
                "type": "sensor",
                "mass": 35.0,
                "cost": 400,
                "power_requirement": 120.0,
                "crew_requirement": 2,
                "tech_requirements": ["advanced_sensors"],
                "attributes": {
                    "detection_range": 5000000.0,
                    "resolution": 0.1,
                    "scan_time": 30.0,
                    "stealth_detection": True
                }
            },
            
            # Weapons
            {
                "id": "laser_cannon",
                "name": "Laser Cannon",
                "type": "weapon",
                "mass": 45.0,
                "cost": 300,
                "power_requirement": 200.0,
                "crew_requirement": 2,
                "tech_requirements": ["basic_weapons"],
                "attributes": {
                    "damage": 100.0,
                    "range": 500000.0,
                    "firing_rate": 2.0,
                    "accuracy": 0.8
                }
            },
            {
                "id": "missile_launcher",
                "name": "Missile Launcher",
                "type": "weapon",
                "mass": 80.0,
                "cost": 250,
                "power_requirement": 50.0,
                "crew_requirement": 3,
                "tech_requirements": ["missile_systems"],
                "attributes": {
                    "damage": 300.0,
                    "range": 2000000.0,
                    "firing_rate": 0.5,
                    "accuracy": 0.9,
                    "ammunition_capacity": 20
                }
            },
            
            # Shields
            {
                "id": "basic_shields",
                "name": "Basic Shield Generator",
                "type": "shield",
                "mass": 70.0,
                "cost": 400,
                "power_requirement": 300.0,
                "crew_requirement": 2,
                "tech_requirements": ["basic_shields"],
                "attributes": {
                    "shield_strength": 500.0,
                    "recharge_rate": 10.0,
                    "power_efficiency": 0.6
                }
            },
            
            # Armor
            {
                "id": "titanium_armor",
                "name": "Titanium Armor Plating",
                "type": "armor",
                "mass": 30.0,
                "cost": 100,
                "power_requirement": 0.0,
                "crew_requirement": 0,
                "tech_requirements": ["advanced_materials"],
                "attributes": {
                    "armor_value": 200.0,
                    "damage_reduction": 0.3
                }
            },
            
            # Bridge
            {
                "id": "standard_bridge",
                "name": "Standard Bridge",
                "type": "bridge",
                "mass": 80.0,
                "cost": 300,
                "power_requirement": 100.0,
                "crew_requirement": 5,
                "tech_requirements": ["basic_computing"],
                "attributes": {
                    "command_efficiency": 1.0,
                    "sensor_bonus": 0.1
                }
            },
            
            # Cargo Bay
            {
                "id": "cargo_bay",
                "name": "Cargo Bay",
                "type": "cargo_bay",
                "mass": 5.0,
                "cost": 50,
                "power_requirement": 5.0,
                "crew_requirement": 0,
                "tech_requirements": [],
                "attributes": {
                    "cargo_capacity": 500.0
                }
            }
        ]
        
        # Convert to ShipComponent objects
        for comp_data in default_components:
            component = ShipComponent(
                id=comp_data["id"],
                name=comp_data["name"],
                component_type=comp_data["type"],
                mass=comp_data["mass"],
                cost=comp_data["cost"],
                power_requirement=comp_data["power_requirement"],
                crew_requirement=comp_data["crew_requirement"],
                tech_requirements=comp_data["tech_requirements"],
                attributes=comp_data["attributes"]
            )
            self.components[comp_data["id"]] = component
    
    def get_component(self, component_id: str) -> Optional[ShipComponent]:
        """Get a component by ID."""
        return self.components.get(component_id)
    
    def get_all_components(self) -> Dict[str, ShipComponent]:
        """Get all components."""
        return self.components.copy()
    
    def get_components_by_type(self, component_type: str) -> List[ShipComponent]:
        """Get all components of a specific type."""
        return [comp for comp in self.components.values() if comp.component_type == component_type]
    
    def get_available_components(self, researched_techs: List[str]) -> List[ShipComponent]:
        """
        Get components that can be built with current technology.
        
        Args:
            researched_techs: List of researched technology IDs
            
        Returns:
            List of available components
        """
        available = []
        researched_set = set(researched_techs)
        
        for component in self.components.values():
            # Check if all tech requirements are met
            if all(tech in researched_set for tech in component.tech_requirements):
                available.append(component)
        
        return available
    
    def create_ship_design(
        self, 
        design_id: str,
        name: str,
        ship_type: ShipType,
        component_ids: List[str]
    ) -> Optional[ShipDesign]:
        """
        Create a new ship design.
        
        Args:
            design_id: Unique design identifier
            name: Design name
            ship_type: Type of ship
            component_ids: List of component IDs to include
            
        Returns:
            Created ship design or None if invalid
        """
        # Validate components exist
        components = []
        for comp_id in component_ids:
            component = self.get_component(comp_id)
            if not component:
                logger.error(f"Unknown component: {comp_id}")
                return None
            components.append(component)
        
        # Calculate totals
        total_mass = sum(comp.mass for comp in components)
        total_cost = sum(comp.cost for comp in components)
        total_crew = sum(comp.crew_requirement for comp in components)
        
        # Validate design
        validation_result = self._validate_ship_design(components, ship_type)
        if not validation_result["valid"]:
            logger.error(f"Invalid ship design: {validation_result['errors']}")
            return None
        
        # Create design
        design = ShipDesign(
            id=design_id,
            name=name,
            ship_type=ship_type,
            components=component_ids,
            total_mass=total_mass,
            total_cost=total_cost,
            crew_requirement=total_crew,
            is_obsolete=False
        )
        
        self.designs[design_id] = design
        logger.info(f"Created ship design: {name}")
        return design
    
    def _validate_ship_design(self, components: List[ShipComponent], ship_type: ShipType) -> Dict:
        """Validate a ship design for completeness and consistency."""
        errors = []
        warnings = []
        
        # Check for required components
        component_types = [comp.component_type for comp in components]
        
        # Every ship needs power
        if "power_plant" not in component_types:
            errors.append("Ship must have at least one power plant")
        
        # Most ships need propulsion
        if ship_type not in [ShipType.MINING_SHIP] and "engine" not in component_types:
            warnings.append("Ship has no propulsion system")
        
        # Ships with crew need life support
        total_crew = sum(comp.crew_requirement for comp in components)
        crew_capacity = sum(
            comp.attributes.get("crew_capacity", 0) 
            for comp in components 
            if comp.component_type == "crew_quarters"
        )
        
        if total_crew > 0 and crew_capacity < total_crew:
            errors.append(f"Insufficient crew quarters: need {total_crew}, have {crew_capacity}")
        
        # Check power balance
        power_generation = sum(
            comp.attributes.get("power_output", 0) 
            for comp in components 
            if comp.component_type == "power_plant"
        )
        power_consumption = sum(comp.power_requirement for comp in components)
        
        if power_consumption > power_generation:
            errors.append(f"Power deficit: need {power_consumption}, generate {power_generation}")
        
        # Check fuel requirements
        has_fuel_consuming_engine = any(
            comp.component_type == "engine" and comp.attributes.get("fuel_consumption", 0) > 0
            for comp in components
        )
        has_fuel_tank = any(comp.component_type == "fuel_tank" for comp in components)
        
        if has_fuel_consuming_engine and not has_fuel_tank:
            warnings.append("Ship has fuel-consuming engines but no fuel tanks")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def get_ship_design(self, design_id: str) -> Optional[ShipDesign]:
        """Get a ship design by ID."""
        return self.designs.get(design_id)
    
    def get_all_designs(self) -> Dict[str, ShipDesign]:
        """Get all ship designs."""
        return self.designs.copy()
    
    def get_designs_by_type(self, ship_type: ShipType) -> List[ShipDesign]:
        """Get all designs of a specific ship type."""
        return [design for design in self.designs.values() if design.ship_type == ship_type]
    
    def calculate_construction_time(self, design: ShipDesign, construction_rate: float = 1.0) -> float:
        """
        Calculate time required to construct a ship.
        
        Args:
            design: Ship design to construct
            construction_rate: Construction rate multiplier
            
        Returns:
            Construction time in game seconds
        """
        base_time = design.total_mass * 100  # 100 seconds per ton base
        complexity_modifier = 1.0 + (len(design.components) * 0.1)  # More components = more complex
        
        return (base_time * complexity_modifier) / construction_rate
    
    def save_components(self, file_path: Optional[str] = None) -> str:
        """
        Save components to a file.
        
        Args:
            file_path: Optional custom file path
            
        Returns:
            Path to saved file
        """
        if file_path is None:
            file_path = self.data_directory / "ship_components.json"
        else:
            file_path = Path(file_path)
        
        # Create data structure
        component_data = {
            "version": "1.0",
            "created_date": "auto-generated",
            "components": {}
        }
        
        for comp_id, component in self.components.items():
            component_data["components"][comp_id] = {
                "name": component.name,
                "type": component.component_type,
                "mass": component.mass,
                "cost": component.cost,
                "power_requirement": component.power_requirement,
                "crew_requirement": component.crew_requirement,
                "tech_requirements": component.tech_requirements,
                "attributes": component.attributes
            }
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save file
        with open(file_path, 'w') as f:
            json.dump(component_data, f, indent=2)
        
        logger.info(f"Ship components saved to: {file_path}")
        return str(file_path)


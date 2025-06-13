"""
Technology Tree Manager for PyAurora 4X

Manages the technology system, prerequisites, and research progression.
"""

import json
import os
from typing import Dict, List, Optional, Set
from pathlib import Path
import logging

from pyaurora4x.core.models import Technology
from pyaurora4x.core.enums import TechnologyType

logger = logging.getLogger(__name__)


class TechTreeManager:
    """
    Manages the technology tree system.
    
    Loads technology definitions from JSON files, validates prerequisites,
    and provides research progression logic.
    """
    
    def __init__(self, data_directory: str = "data"):
        """
        Initialize the technology tree manager.
        
        Args:
            data_directory: Directory containing tech data files
        """
        self.data_directory = Path(data_directory)
        self.technologies: Dict[str, Technology] = {}
        self.tech_tree_loaded = False
        
        # Try to load tech tree data
        self.load_tech_tree()
    
    def load_tech_tree(self) -> bool:
        """
        Load the technology tree from data files.
        
        Returns:
            True if loading was successful
        """
        tech_file = self.data_directory / "techs.json"
        
        if not tech_file.exists():
            logger.warning(f"Tech file not found: {tech_file}")
            self._create_default_tech_tree()
            return False
        
        try:
            with open(tech_file, 'r') as f:
                tech_data = json.load(f)
            
            self._load_technologies_from_data(tech_data)
            self._validate_tech_tree()
            
            self.tech_tree_loaded = True
            logger.info(f"Loaded {len(self.technologies)} technologies")
            return True
            
        except Exception as e:
            logger.error(f"Error loading tech tree: {e}")
            self._create_default_tech_tree()
            return False
    
    def _load_technologies_from_data(self, tech_data: Dict) -> None:
        """Load technologies from parsed JSON data."""
        self.technologies.clear()
        
        for tech_id, tech_info in tech_data.get("technologies", {}).items():
            try:
                # Parse technology type
                tech_type_str = tech_info.get("type", "engineering")
                tech_type = self._parse_tech_type(tech_type_str)
                
                # Create technology object
                technology = Technology(
                    id=tech_id,
                    name=tech_info.get("name", tech_id.replace("_", " ").title()),
                    description=tech_info.get("description", ""),
                    tech_type=tech_type,
                    research_cost=tech_info.get("research_cost", 100),
                    prerequisites=tech_info.get("prerequisites", []),
                    unlocks=tech_info.get("unlocks", []),
                    is_researched=False
                )
                
                self.technologies[tech_id] = technology
                
            except Exception as e:
                logger.error(f"Error loading technology {tech_id}: {e}")
    
    def _parse_tech_type(self, type_str: str) -> TechnologyType:
        """Parse technology type from string."""
        type_mapping = {
            "propulsion": TechnologyType.PROPULSION,
            "energy": TechnologyType.ENERGY,
            "weapons": TechnologyType.WEAPONS,
            "shields": TechnologyType.SHIELDS,
            "sensors": TechnologyType.SENSORS,
            "construction": TechnologyType.CONSTRUCTION,
            "biology": TechnologyType.BIOLOGY,
            "physics": TechnologyType.PHYSICS,
            "engineering": TechnologyType.ENGINEERING,
            "logistics": TechnologyType.LOGISTICS,
            "computing": TechnologyType.COMPUTING,
            "materials": TechnologyType.MATERIALS,
        }
        
        return type_mapping.get(type_str.lower(), TechnologyType.ENGINEERING)
    
    def _validate_tech_tree(self) -> None:
        """Validate the technology tree for consistency."""
        errors = []
        
        # Check for circular dependencies
        for tech_id in self.technologies:
            if self._has_circular_dependency(tech_id):
                errors.append(f"Circular dependency detected for {tech_id}")
        
        # Check for invalid prerequisites
        for tech_id, tech in self.technologies.items():
            for prereq in tech.prerequisites:
                if prereq not in self.technologies:
                    errors.append(f"Invalid prerequisite {prereq} for {tech_id}")
        
        # Check for invalid unlocks
        for tech_id, tech in self.technologies.items():
            for unlock in tech.unlocks:
                if unlock not in self.technologies:
                    logger.warning(f"Technology {tech_id} unlocks unknown tech: {unlock}")
        
        if errors:
            logger.error("Tech tree validation errors:")
            for error in errors:
                logger.error(f"  {error}")
        else:
            logger.info("Tech tree validation passed")
    
    def _has_circular_dependency(self, tech_id: str, visited: Optional[Set[str]] = None) -> bool:
        """Check if a technology has circular dependencies."""
        if visited is None:
            visited = set()
        
        if tech_id in visited:
            return True
        
        tech = self.technologies.get(tech_id)
        if not tech:
            return False
        
        visited.add(tech_id)
        
        for prereq in tech.prerequisites:
            if self._has_circular_dependency(prereq, visited.copy()):
                return True
        
        return False
    
    def _create_default_tech_tree(self) -> None:
        """Create a default technology tree."""
        logger.info("Creating default technology tree")
        
        default_techs = [
            {
                "id": "basic_propulsion",
                "name": "Basic Propulsion",
                "description": "Chemical rockets and basic thrust systems for interplanetary travel.",
                "type": "propulsion",
                "research_cost": 100,
                "prerequisites": [],
                "unlocks": ["advanced_propulsion", "fuel_efficiency"]
            },
            {
                "id": "advanced_propulsion",
                "name": "Advanced Propulsion",
                "description": "Ion drives and nuclear thermal propulsion systems.",
                "type": "propulsion",
                "research_cost": 250,
                "prerequisites": ["basic_propulsion", "basic_energy"],
                "unlocks": ["fusion_drive"]
            },
            {
                "id": "fusion_drive",
                "name": "Fusion Drive",
                "description": "Fusion-powered spacecraft propulsion systems.",
                "type": "propulsion",
                "research_cost": 500,
                "prerequisites": ["advanced_propulsion", "fusion_power"],
                "unlocks": ["antimatter_drive"]
            },
            {
                "id": "basic_energy",
                "name": "Basic Energy Systems",
                "description": "Solar panels and chemical batteries for power generation.",
                "type": "energy",
                "research_cost": 80,
                "prerequisites": [],
                "unlocks": ["nuclear_power", "energy_storage"]
            },
            {
                "id": "nuclear_power",
                "name": "Nuclear Power",
                "description": "Fission reactors for high-output power generation.",
                "type": "energy",
                "research_cost": 200,
                "prerequisites": ["basic_energy"],
                "unlocks": ["fusion_power"]
            },
            {
                "id": "fusion_power",
                "name": "Fusion Power",
                "description": "Fusion reactors for clean, high-efficiency power.",
                "type": "energy",
                "research_cost": 400,
                "prerequisites": ["nuclear_power", "magnetic_confinement"],
                "unlocks": ["zero_point_energy"]
            },
            {
                "id": "basic_sensors",
                "name": "Basic Sensors",
                "description": "Optical and radio telescopes for basic detection.",
                "type": "sensors",
                "research_cost": 75,
                "prerequisites": [],
                "unlocks": ["advanced_sensors", "deep_space_tracking"]
            },
            {
                "id": "advanced_sensors",
                "name": "Advanced Sensors",
                "description": "Gravitational wave detectors and advanced imaging systems.",
                "type": "sensors",
                "research_cost": 180,
                "prerequisites": ["basic_sensors", "basic_computing"],
                "unlocks": ["quantum_sensors"]
            },
            {
                "id": "basic_computing",
                "name": "Basic Computing",
                "description": "Digital computers and basic AI systems.",
                "type": "computing",
                "research_cost": 90,
                "prerequisites": [],
                "unlocks": ["advanced_computing", "ai_systems"]
            },
            {
                "id": "advanced_computing",
                "name": "Advanced Computing",
                "description": "Quantum computers and neural networks.",
                "type": "computing",
                "research_cost": 220,
                "prerequisites": ["basic_computing"],
                "unlocks": ["quantum_computing"]
            },
            {
                "id": "basic_weapons",
                "name": "Basic Weapons",
                "description": "Kinetic projectiles and basic laser systems.",
                "type": "weapons",
                "research_cost": 120,
                "prerequisites": ["basic_energy"],
                "unlocks": ["missile_systems", "beam_weapons"]
            },
            {
                "id": "missile_systems",
                "name": "Missile Systems",
                "description": "Guided missiles and torpedo systems.",
                "type": "weapons",
                "research_cost": 200,
                "prerequisites": ["basic_weapons", "basic_sensors"],
                "unlocks": ["smart_missiles"]
            },
            {
                "id": "basic_shields",
                "name": "Basic Shields",
                "description": "Electromagnetic field generators for deflection.",
                "type": "shields",
                "research_cost": 150,
                "prerequisites": ["basic_energy", "magnetic_confinement"],
                "unlocks": ["advanced_shields"]
            },
            {
                "id": "magnetic_confinement",
                "name": "Magnetic Confinement",
                "description": "Magnetic field manipulation and control systems.",
                "type": "physics",
                "research_cost": 160,
                "prerequisites": ["basic_energy"],
                "unlocks": ["fusion_power", "basic_shields"]
            },
            {
                "id": "basic_construction",
                "name": "Basic Construction",
                "description": "Space-based manufacturing and assembly systems.",
                "type": "construction",
                "research_cost": 110,
                "prerequisites": [],
                "unlocks": ["automated_construction", "orbital_shipyards"]
            },
            {
                "id": "automated_construction",
                "name": "Automated Construction",
                "description": "Robotic construction systems and 3D printing.",
                "type": "construction",
                "research_cost": 240,
                "prerequisites": ["basic_construction", "basic_computing"],
                "unlocks": ["self_replicating_systems"]
            }
        ]
        
        # Convert to Technology objects
        for tech_data in default_techs:
            tech_type = self._parse_tech_type(tech_data["type"])
            technology = Technology(
                id=tech_data["id"],
                name=tech_data["name"],
                description=tech_data["description"],
                tech_type=tech_type,
                research_cost=tech_data["research_cost"],
                prerequisites=tech_data["prerequisites"],
                unlocks=tech_data["unlocks"],
                is_researched=False
            )
            self.technologies[tech_data["id"]] = technology
        
        # Validate the default tree
        self._validate_tech_tree()
    
    def get_technology(self, tech_id: str) -> Optional[Technology]:
        """Get a technology by ID."""
        return self.technologies.get(tech_id)
    
    def get_all_technologies(self) -> Dict[str, Technology]:
        """Get all technologies."""
        return self.technologies.copy()
    
    def get_technologies_by_type(self, tech_type: TechnologyType) -> List[Technology]:
        """Get all technologies of a specific type."""
        return [tech for tech in self.technologies.values() if tech.tech_type == tech_type]
    
    def get_available_technologies(self, researched_techs: Set[str]) -> List[Technology]:
        """
        Get technologies that can be researched based on current knowledge.
        
        Args:
            researched_techs: Set of already researched technology IDs
            
        Returns:
            List of available technologies
        """
        available = []
        
        for tech in self.technologies.values():
            if tech.id in researched_techs:
                continue  # Already researched
            
            # Check if prerequisites are met
            if self._are_prerequisites_met(tech, researched_techs):
                available.append(tech)
        
        return available
    
    def _are_prerequisites_met(self, technology: Technology, researched_techs: Set[str]) -> bool:
        """Check if technology prerequisites are satisfied."""
        for prereq in technology.prerequisites:
            if prereq not in researched_techs:
                return False
        return True
    
    def get_research_path(self, target_tech_id: str, researched_techs: Set[str]) -> List[str]:
        """
        Get the research path to a target technology.
        
        Args:
            target_tech_id: Technology to research
            researched_techs: Currently researched technologies
            
        Returns:
            List of technology IDs in research order
        """
        if target_tech_id in researched_techs:
            return []  # Already researched
        
        target_tech = self.technologies.get(target_tech_id)
        if not target_tech:
            return []  # Invalid technology
        
        path = []
        to_research = set()
        
        def collect_prerequisites(tech_id: str):
            if tech_id in researched_techs:
                return  # Already have it
            
            tech = self.technologies.get(tech_id)
            if not tech:
                return
            
            # First collect prerequisites
            for prereq in tech.prerequisites:
                collect_prerequisites(prereq)
            
            # Then add this technology
            if tech_id not in to_research:
                to_research.add(tech_id)
                path.append(tech_id)
        
        collect_prerequisites(target_tech_id)
        return path
    
    def get_technology_tree_summary(self) -> Dict[str, any]:
        """Get a summary of the technology tree."""
        summary = {
            "total_technologies": len(self.technologies),
            "by_type": {},
            "research_costs": {
                "total": sum(tech.research_cost for tech in self.technologies.values()),
                "average": 0,
                "min": float('inf'),
                "max": 0
            },
            "complexity": {
                "max_prerequisites": 0,
                "technologies_with_no_prerequisites": 0,
                "technologies_with_no_unlocks": 0
            }
        }
        
        # Count by type
        for tech in self.technologies.values():
            tech_type = tech.tech_type.value if hasattr(tech.tech_type, 'value') else str(tech.tech_type)
            summary["by_type"][tech_type] = summary["by_type"].get(tech_type, 0) + 1
        
        # Calculate research cost statistics
        if self.technologies:
            costs = [tech.research_cost for tech in self.technologies.values()]
            summary["research_costs"]["average"] = sum(costs) / len(costs)
            summary["research_costs"]["min"] = min(costs)
            summary["research_costs"]["max"] = max(costs)
        
        # Calculate complexity statistics
        for tech in self.technologies.values():
            prereq_count = len(tech.prerequisites)
            summary["complexity"]["max_prerequisites"] = max(
                summary["complexity"]["max_prerequisites"], 
                prereq_count
            )
            
            if prereq_count == 0:
                summary["complexity"]["technologies_with_no_prerequisites"] += 1
            
            if not tech.unlocks:
                summary["complexity"]["technologies_with_no_unlocks"] += 1
        
        return summary
    
    def save_tech_tree(self, file_path: Optional[str] = None) -> str:
        """
        Save the current technology tree to a file.
        
        Args:
            file_path: Optional custom file path
            
        Returns:
            Path to saved file
        """
        if file_path is None:
            file_path = self.data_directory / "techs.json"
        else:
            file_path = Path(file_path)
        
        # Create data structure
        tech_data = {
            "version": "1.0",
            "created_date": "auto-generated",
            "technologies": {}
        }
        
        for tech_id, tech in self.technologies.items():
            tech_type = tech.tech_type.value if hasattr(tech.tech_type, 'value') else str(tech.tech_type)
            tech_data["technologies"][tech_id] = {
                "name": tech.name,
                "description": tech.description,
                "type": tech_type,
                "research_cost": tech.research_cost,
                "prerequisites": tech.prerequisites,
                "unlocks": tech.unlocks
            }
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save file
        with open(file_path, 'w') as f:
            json.dump(tech_data, f, indent=2)
        
        logger.info(f"Technology tree saved to: {file_path}")
        return str(file_path)


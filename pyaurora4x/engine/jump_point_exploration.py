"""
Jump Point Exploration System for PyAurora 4X

Handles the discovery, survey, and exploration of jump points within star systems.
This system manages the progressive revelation of jump point networks as fleets
explore and survey systems.
"""

import logging
import math
import random
from typing import Dict, List, Optional, Tuple, Any

from pyaurora4x.core.models import Fleet, StarSystem, JumpPoint, Empire, Vector3D
from pyaurora4x.core.enums import (
    FleetStatus, JumpPointType, JumpPointStatus, ExplorationResult,
    CONSTANTS
)

logger = logging.getLogger(__name__)


class ExplorationMission:
    """Represents an active exploration or survey mission."""
    
    def __init__(
        self,
        fleet_id: str,
        system_id: str,
        mission_type: str,
        start_time: float,
        duration: float,
        target_position: Optional[Vector3D] = None,
        target_jump_point_id: Optional[str] = None
    ):
        self.fleet_id = fleet_id
        self.system_id = system_id
        self.mission_type = mission_type  # "explore", "survey", "deep_scan"
        self.start_time = start_time
        self.duration = duration
        self.target_position = target_position
        self.target_jump_point_id = target_jump_point_id
        self.progress = 0.0
        self.completed = False
        self.results: List[ExplorationResult] = []


class JumpPointExplorationSystem:
    """Manages jump point discovery and exploration mechanics."""
    
    def __init__(self):
        self.active_missions: Dict[str, ExplorationMission] = {}  # fleet_id -> mission
        self.system_exploration_data: Dict[str, Dict[str, Any]] = {}  # system_id -> data
        self.hidden_jump_points: Dict[str, List[JumpPoint]] = {}  # system_id -> hidden points
        
        # Exploration parameters
        self.base_detection_chance = CONSTANTS["EXPLORATION_SUCCESS_BASE"]
        self.survey_skill_bonus = 0.1  # Bonus per survey ship skill level
        self.system_difficulty_modifier = 1.0
        
        logger.info("Jump Point Exploration System initialized")
    
    def initialize_system_exploration(self, system: StarSystem, empire_id: str) -> None:
        """Initialize exploration data for a star system."""
        if system.id not in self.system_exploration_data:
            self.system_exploration_data[system.id] = {
                "empires": {},
                "total_exploration_time": 0.0,
                "last_exploration": None,
                "exploration_difficulty": self._calculate_system_difficulty(system),
                "potential_jump_points": self._generate_hidden_jump_points(system)
            }
        
        # Initialize empire-specific exploration data
        if empire_id not in self.system_exploration_data[system.id]["empires"]:
            self.system_exploration_data[system.id]["empires"][empire_id] = {
                "exploration_progress": 0.0,
                "survey_completeness": 0.0,
                "discovered_jump_points": [],
                "last_exploration": None,
                "exploration_bonuses": {}
            }
    
    def start_exploration_mission(
        self,
        fleet: Fleet,
        system: StarSystem,
        mission_type: str = "explore",
        current_time: float = 0.0,
        target_position: Optional[Vector3D] = None
    ) -> bool:
        """Start an exploration mission for a fleet."""
        if fleet.id in self.active_missions:
            logger.warning("Fleet %s already has an active exploration mission", fleet.name)
            return False
        
        # Calculate mission duration based on type and fleet capabilities
        duration = self._calculate_mission_duration(fleet, mission_type, system)
        
        # Create the mission
        mission = ExplorationMission(
            fleet_id=fleet.id,
            system_id=system.id,
            mission_type=mission_type,
            start_time=current_time,
            duration=duration,
            target_position=target_position or fleet.position.copy()
        )
        
        self.active_missions[fleet.id] = mission
        
        # Update fleet status
        if mission_type == "explore":
            fleet.status = FleetStatus.EXPLORING
        elif mission_type == "survey":
            fleet.status = FleetStatus.SURVEYING
        
        fleet.current_orders.append(f"Conducting {mission_type} mission")
        
        logger.info(
            "Fleet %s started %s mission in system %s (duration: %.1f seconds)",
            fleet.name, mission_type, system.name, duration
        )
        
        return True
    
    def process_exploration_missions(
        self,
        fleets: Dict[str, Fleet],
        systems: Dict[str, StarSystem],
        current_time: float,
        delta_seconds: float
    ) -> Dict[str, List[ExplorationResult]]:
        """Process all active exploration missions and return results."""
        results = {}
        completed_missions = []
        
        for fleet_id, mission in self.active_missions.items():
            fleet = fleets.get(fleet_id)
            system = systems.get(mission.system_id)
            
            if not fleet or not system:
                completed_missions.append(fleet_id)
                continue
            
            # Update mission progress
            time_elapsed = current_time - mission.start_time
            mission.progress = min(1.0, time_elapsed / mission.duration)
            
            # Process mission advancement
            mission_results = self._process_mission_step(
                mission, fleet, system, current_time, delta_seconds
            )
            
            if mission_results:
                results[fleet_id] = mission_results
            
            # Check if mission is completed
            if mission.progress >= 1.0 or mission.completed:
                self._complete_mission(mission, fleet, system, current_time)
                completed_missions.append(fleet_id)
        
        # Remove completed missions
        for fleet_id in completed_missions:
            if fleet_id in self.active_missions:
                del self.active_missions[fleet_id]
        
        return results
    
    def attempt_jump_point_detection(
        self,
        fleet: Fleet,
        system: StarSystem,
        empire_id: str,
        current_time: float
    ) -> List[JumpPoint]:
        """Attempt to detect jump points near the fleet's current position."""
        self.initialize_system_exploration(system, empire_id)
        
        detected_points = []
        empire_data = self.system_exploration_data[system.id]["empires"][empire_id]
        
        # Check for jump points within detection range
        detection_range = CONSTANTS["JUMP_POINT_DETECTION_RANGE"] * CONSTANTS["AU_TO_KM"]
        
        for jump_point in system.jump_points:
            if jump_point.discovered_by == empire_id:
                continue  # Already discovered
            
            # Calculate distance to jump point
            distance = self._calculate_distance(fleet.position, jump_point.position)
            
            if distance <= detection_range:
                # Calculate detection probability
                detection_chance = self._calculate_detection_probability(
                    fleet, jump_point, distance, empire_data
                )
                
                if random.random() < detection_chance:
                    self._discover_jump_point(jump_point, empire_id, current_time)
                    detected_points.append(jump_point)
                    empire_data["discovered_jump_points"].append(jump_point.id)
                    
                    logger.info(
                        "Fleet %s detected jump point %s in system %s",
                        fleet.name, jump_point.name, system.name
                    )
        
        # Check hidden jump points
        hidden_points = self.hidden_jump_points.get(system.id, [])
        for hidden_point in hidden_points[:]:  # Copy list to allow modification
            distance = self._calculate_distance(fleet.position, hidden_point.position)
            
            if distance <= detection_range:
                detection_chance = self._calculate_detection_probability(
                    fleet, hidden_point, distance, empire_data
                ) * 0.5  # Hidden points are harder to detect
                
                if random.random() < detection_chance:
                    # Reveal the hidden jump point
                    self._reveal_hidden_jump_point(hidden_point, system, empire_id, current_time)
                    detected_points.append(hidden_point)
                    hidden_points.remove(hidden_point)
                    
                    logger.info(
                        "Fleet %s discovered hidden jump point %s in system %s",
                        fleet.name, hidden_point.name, system.name
                    )
        
        return detected_points
    
    def survey_jump_point(
        self,
        fleet: Fleet,
        jump_point: JumpPoint,
        empire_id: str,
        current_time: float
    ) -> bool:
        """Conduct a detailed survey of a specific jump point."""
        if jump_point.survey_level >= 3:  # Already fully surveyed
            return False
        
        # Check if fleet is close enough
        distance = self._calculate_distance(fleet.position, jump_point.position)
        survey_range = CONSTANTS["JUMP_POINT_DETECTION_RANGE"] * CONSTANTS["AU_TO_KM"] * 0.5
        
        if distance > survey_range:
            return False
        
        # Calculate survey duration
        survey_duration = CONSTANTS["SURVEY_BASE_TIME"]
        survey_duration *= jump_point.exploration_difficulty
        survey_duration /= self._calculate_fleet_survey_capability(fleet)
        
        # Start survey mission
        return self.start_exploration_mission(
            fleet=fleet,
            system=None,  # Will be filled in by caller
            mission_type="survey",
            current_time=current_time,
            target_position=jump_point.position.copy()
        )
    
    def get_exploration_status(self, system_id: str, empire_id: str) -> Dict[str, Any]:
        """Get exploration status for a system and empire."""
        if system_id not in self.system_exploration_data:
            return {"exploration_progress": 0.0, "survey_completeness": 0.0}
        
        system_data = self.system_exploration_data[system_id]
        empire_data = system_data.get("empires", {}).get(empire_id, {})
        
        return {
            "exploration_progress": empire_data.get("exploration_progress", 0.0),
            "survey_completeness": empire_data.get("survey_completeness", 0.0),
            "discovered_jump_points": len(empire_data.get("discovered_jump_points", [])),
            "last_exploration": empire_data.get("last_exploration"),
            "system_difficulty": system_data.get("exploration_difficulty", 1.0),
            "potential_discoveries": len(self.hidden_jump_points.get(system_id, []))
        }
    
    # Private helper methods
    
    def _calculate_system_difficulty(self, system: StarSystem) -> float:
        """Calculate the exploration difficulty of a system."""
        difficulty = 1.0
        
        # More planets = slightly harder to explore thoroughly
        difficulty += len(system.planets) * 0.1
        
        # More asteroid belts = more places to hide jump points
        difficulty += len(system.asteroid_belts) * 0.2
        
        # Larger habitable zone = more space to cover
        hz_size = system.habitable_zone_outer - system.habitable_zone_inner
        difficulty += hz_size * 0.1
        
        return max(0.5, min(3.0, difficulty))
    
    def _generate_hidden_jump_points(self, system: StarSystem) -> int:
        """Generate the number of potential hidden jump points in a system."""
        # Base number of hidden points
        base_hidden = 1 if random.random() < 0.4 else 0
        
        # Chance for additional hidden points
        for _ in range(2):
            if random.random() < 0.15:
                base_hidden += 1
        
        # Generate actual hidden jump points
        if base_hidden > 0 and system.id not in self.hidden_jump_points:
            self.hidden_jump_points[system.id] = []
            
            for i in range(base_hidden):
                hidden_point = self._create_hidden_jump_point(system, i)
                self.hidden_jump_points[system.id].append(hidden_point)
        
        return base_hidden
    
    def _create_hidden_jump_point(self, system: StarSystem, index: int) -> JumpPoint:
        """Create a hidden jump point in the system."""
        # Generate position in outer system
        distance_au = random.uniform(3.0, 8.0)
        angle = random.uniform(0.0, 2 * math.pi)
        r = distance_au * CONSTANTS["AU_TO_KM"]
        
        position = Vector3D(
            x=r * math.cos(angle),
            y=r * math.sin(angle),
            z=random.uniform(-0.1 * r, 0.1 * r)
        )
        
        hidden_point = JumpPoint(
            name=f"Hidden JP-{index+1}",
            position=position,
            connects_to="",  # Will be determined when revealed
            jump_point_type=JumpPointType.NATURAL,
            status=JumpPointStatus.UNKNOWN,
            stability=random.uniform(0.7, 1.0),
            size_class=random.randint(1, 3),
            exploration_difficulty=random.uniform(1.2, 2.0),
            fuel_cost_modifier=random.uniform(0.8, 1.3),
            travel_time_modifier=random.uniform(0.9, 1.2)
        )
        
        return hidden_point
    
    def _calculate_mission_duration(self, fleet: Fleet, mission_type: str, system: StarSystem) -> float:
        """Calculate the duration of an exploration mission."""
        base_times = {
            "explore": CONSTANTS["EXPLORATION_BASE_TIME"],
            "survey": CONSTANTS["SURVEY_BASE_TIME"],
            "deep_scan": CONSTANTS["SURVEY_BASE_TIME"] * 2
        }
        
        base_duration = base_times.get(mission_type, CONSTANTS["EXPLORATION_BASE_TIME"])
        
        # Modify based on system difficulty
        system_difficulty = self.system_exploration_data.get(
            system.id, {}
        ).get("exploration_difficulty", 1.0)
        
        # Modify based on fleet capabilities
        fleet_capability = self._calculate_fleet_survey_capability(fleet)
        
        duration = base_duration * system_difficulty / fleet_capability
        return max(60.0, duration)  # Minimum 1 minute
    
    def _calculate_fleet_survey_capability(self, fleet: Fleet) -> float:
        """Calculate a fleet's survey and exploration capability."""
        capability = 1.0
        
        # More ships = better survey capability
        capability += len(fleet.ships) * 0.1
        
        # TODO: Check for survey equipment, sensors, etc.
        # For now, assume all fleets have basic survey capability
        
        return max(0.5, capability)
    
    def _process_mission_step(
        self,
        mission: ExplorationMission,
        fleet: Fleet,
        system: StarSystem,
        current_time: float,
        delta_seconds: float
    ) -> List[ExplorationResult]:
        """Process a single step of an exploration mission."""
        results = []
        
        # Periodic checks for discoveries during the mission
        if mission.progress > 0.3 and random.random() < 0.1:  # 10% chance per step after 30% completion
            detected_points = self.attempt_jump_point_detection(
                fleet, system, fleet.empire_id, current_time
            )
            
            for point in detected_points:
                if point.survey_level == 1:
                    results.append(ExplorationResult.JUMP_POINT_DETECTED)
                elif point.survey_level >= 2:
                    results.append(ExplorationResult.JUMP_POINT_SURVEYED)
        
        # Check for other discoveries
        if mission.progress > 0.7 and random.random() < 0.05:
            results.append(ExplorationResult.ANOMALY_DETECTED)
        
        return results
    
    def _complete_mission(
        self,
        mission: ExplorationMission,
        fleet: Fleet,
        system: StarSystem,
        current_time: float
    ) -> None:
        """Complete an exploration mission and process final results."""
        empire_id = fleet.empire_id
        self.initialize_system_exploration(system, empire_id)
        
        empire_data = self.system_exploration_data[system.id]["empires"][empire_id]
        
        # Update exploration progress
        if mission.mission_type == "explore":
            progress_gain = 0.2 + (mission.progress * 0.3)
            empire_data["exploration_progress"] = min(
                1.0, empire_data["exploration_progress"] + progress_gain
            )
            fleet.status = FleetStatus.IDLE
            
        elif mission.mission_type == "survey":
            survey_gain = 0.15 + (mission.progress * 0.25)
            empire_data["survey_completeness"] = min(
                1.0, empire_data["survey_completeness"] + survey_gain
            )
            
            # If surveying a specific jump point, improve its survey level
            if mission.target_jump_point_id:
                for jp in system.jump_points:
                    if jp.id == mission.target_jump_point_id and jp.survey_level < 3:
                        jp.survey_level = min(3, jp.survey_level + 1)
                        jp.last_surveyed = current_time
                        if jp.survey_level >= 2:
                            jp.status = JumpPointStatus.ACTIVE
            
            fleet.status = FleetStatus.IDLE
        
        empire_data["last_exploration"] = current_time
        fleet.current_orders.clear()
        
        logger.info(
            "Fleet %s completed %s mission in system %s",
            fleet.name, mission.mission_type, system.name
        )
    
    def _calculate_distance(self, pos1: Vector3D, pos2: Vector3D) -> float:
        """Calculate distance between two positions."""
        dx = pos1.x - pos2.x
        dy = pos1.y - pos2.y
        dz = pos1.z - pos2.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def _calculate_detection_probability(
        self,
        fleet: Fleet,
        jump_point: JumpPoint,
        distance: float,
        empire_data: Dict[str, Any]
    ) -> float:
        """Calculate the probability of detecting a jump point."""
        base_chance = self.base_detection_chance
        
        # Distance factor - closer is easier
        distance_au = distance / CONSTANTS["AU_TO_KM"]
        distance_factor = max(0.1, 1.0 - (distance_au / CONSTANTS["JUMP_POINT_DETECTION_RANGE"]))
        
        # Fleet capability factor
        fleet_factor = self._calculate_fleet_survey_capability(fleet)
        
        # Jump point difficulty
        difficulty_factor = 1.0 / jump_point.exploration_difficulty
        
        # Empire experience bonus
        experience_bonus = empire_data.get("exploration_progress", 0.0) * 0.5
        
        total_chance = base_chance * distance_factor * fleet_factor * difficulty_factor + experience_bonus
        return min(0.95, max(0.01, total_chance))
    
    def _discover_jump_point(self, jump_point: JumpPoint, empire_id: str, current_time: float) -> None:
        """Mark a jump point as discovered by an empire."""
        if jump_point.discovered_by is None:
            jump_point.discovered_by = empire_id
            jump_point.discovery_date = current_time
            jump_point.status = JumpPointStatus.DETECTED
            jump_point.survey_level = 1
    
    def _reveal_hidden_jump_point(
        self,
        hidden_point: JumpPoint,
        system: StarSystem,
        empire_id: str,
        current_time: float
    ) -> None:
        """Reveal a hidden jump point by adding it to the system."""
        self._discover_jump_point(hidden_point, empire_id, current_time)
        system.jump_points.append(hidden_point)
        
        # TODO: Determine where this jump point connects to
        # For now, leave connects_to empty - it will need to be determined
        # by the jump point network manager

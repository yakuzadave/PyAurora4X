"""
Jump Point Manager for PyAurora 4X

Centralized manager that coordinates jump point discovery, network generation,
travel validation, exploration, and all jump point related operations.
This serves as the main interface for jump point functionality.
"""

import logging
import random
from typing import Dict, List, Optional, Tuple, Any

from pyaurora4x.core.models import Fleet, StarSystem, JumpPoint, Empire, Vector3D, Ship
from pyaurora4x.core.enums import (
    FleetStatus, JumpPointType, JumpPointStatus, ExplorationResult,
    OrderType, CONSTANTS
)
from pyaurora4x.engine.jump_point_exploration import JumpPointExplorationSystem
from pyaurora4x.engine.jump_travel_system import FleetJumpTravelSystem

logger = logging.getLogger(__name__)


class JumpPointNetworkManager:
    """Manages the overall jump point network connectivity."""
    
    def __init__(self):
        self.system_connections: Dict[str, List[str]] = {}  # system_id -> connected_system_ids
        self.network_graph: Dict[str, Dict[str, float]] = {}  # system_id -> {connected_system: distance}
        
    def build_network_graph(self, systems: Dict[str, StarSystem]) -> None:
        """Build or update the jump point network graph."""
        self.system_connections.clear()
        self.network_graph.clear()
        
        for system_id, system in systems.items():
            connections = []
            distances = {}
            
            for jump_point in system.jump_points:
                target_system_id = jump_point.connects_to
                if target_system_id and target_system_id in systems:
                    connections.append(target_system_id)
                    # Use jump point characteristics to calculate "distance"
                    distance = (
                        jump_point.fuel_cost_modifier * 
                        jump_point.travel_time_modifier * 
                        (2.0 - jump_point.stability)
                    )
                    distances[target_system_id] = distance
            
            self.system_connections[system_id] = connections
            self.network_graph[system_id] = distances
    
    def find_shortest_path(self, origin_system_id: str, target_system_id: str) -> List[str]:
        """Find the shortest path between two systems using Dijkstra's algorithm."""
        if origin_system_id == target_system_id:
            return [origin_system_id]
        
        # Dijkstra's algorithm implementation
        distances = {system_id: float('inf') for system_id in self.network_graph}
        distances[origin_system_id] = 0.0
        previous = {}
        unvisited = set(self.network_graph.keys())
        
        while unvisited:
            # Find unvisited node with smallest distance
            current = min(unvisited, key=lambda x: distances[x])
            unvisited.remove(current)
            
            if current == target_system_id:
                break
            
            # Update distances to neighbors
            for neighbor, edge_weight in self.network_graph.get(current, {}).items():
                if neighbor in unvisited:
                    alt_distance = distances[current] + edge_weight
                    if alt_distance < distances[neighbor]:
                        distances[neighbor] = alt_distance
                        previous[neighbor] = current
        
        # Reconstruct path
        if target_system_id not in previous and target_system_id != origin_system_id:
            return []  # No path found
        
        path = []
        current = target_system_id
        while current in previous:
            path.append(current)
            current = previous[current]
        path.append(origin_system_id)
        path.reverse()
        
        return path
    
    def get_reachable_systems(self, origin_system_id: str, max_jumps: int = 5) -> Dict[str, int]:
        """Get all systems reachable from origin within max_jumps."""
        reachable = {origin_system_id: 0}
        to_explore = [(origin_system_id, 0)]
        
        while to_explore:
            current_system, jumps = to_explore.pop(0)
            
            if jumps >= max_jumps:
                continue
            
            for connected_system in self.system_connections.get(current_system, []):
                if connected_system not in reachable or reachable[connected_system] > jumps + 1:
                    reachable[connected_system] = jumps + 1
                    to_explore.append((connected_system, jumps + 1))
        
        return reachable


class JumpPointManager:
    """Main manager for all jump point operations."""
    
    def __init__(self):
        self.exploration_system = JumpPointExplorationSystem()
        self.travel_system = FleetJumpTravelSystem()
        self.network_manager = JumpPointNetworkManager()
        
        # Empire knowledge tracking
        self.empire_knowledge: Dict[str, Dict[str, Any]] = {}  # empire_id -> knowledge
        
        logger.info("Jump Point Manager initialized")
    
    def initialize_empire_knowledge(self, empire_id: str) -> None:
        """Initialize knowledge tracking for an empire."""
        if empire_id not in self.empire_knowledge:
            self.empire_knowledge[empire_id] = {
                "known_systems": set(),
                "known_jump_points": set(),
                "exploration_missions": 0,
                "total_jumps": 0,
                "discovered_jump_points": 0
            }
    
    def update_network(self, systems: Dict[str, StarSystem]) -> None:
        """Update the jump point network with current system data."""
        self.network_manager.build_network_graph(systems)
        logger.debug("Jump point network updated with %d systems", len(systems))
    
    def process_turn_update(
        self,
        fleets: Dict[str, Fleet],
        systems: Dict[str, StarSystem],
        ships: Dict[str, Ship],
        current_time: float,
        delta_seconds: float
    ) -> Dict[str, Any]:
        """Process all jump point related activities for a turn update."""
        results = {
            "exploration_results": {},
            "travel_results": {},
            "discoveries": [],
            "completed_operations": []
        }
        
        # Process exploration missions
        exploration_results = self.exploration_system.process_exploration_missions(
            fleets, systems, current_time, delta_seconds
        )
        results["exploration_results"] = exploration_results
        
        # Process jump travel operations
        travel_results = self.travel_system.process_jump_operations(
            fleets, systems, current_time, delta_seconds
        )
        results["travel_results"] = travel_results
        
        # Check for passive jump point detection by moving fleets
        for fleet in fleets.values():
            if fleet.status in [FleetStatus.MOVING, FleetStatus.IN_TRANSIT, FleetStatus.EXPLORING]:
                system = systems.get(fleet.system_id)
                if system:
                    detected_points = self.exploration_system.attempt_jump_point_detection(
                        fleet, system, fleet.empire_id, current_time
                    )
                    
                    if detected_points:
                        results["discoveries"].extend([
                            {
                                "type": "jump_point_detection",
                                "fleet_id": fleet.id,
                                "system_id": system.id,
                                "jump_points": [jp.id for jp in detected_points]
                            }
                        ])
                        
                        # Update empire knowledge
                        self.initialize_empire_knowledge(fleet.empire_id)
                        empire_knowledge = self.empire_knowledge[fleet.empire_id]
                        empire_knowledge["discovered_jump_points"] += len(detected_points)
                        empire_knowledge["known_jump_points"].update(jp.id for jp in detected_points)
        
        return results
    
    def start_exploration_mission(
        self,
        fleet: Fleet,
        system: StarSystem,
        mission_type: str = "explore",
        current_time: float = 0.0
    ) -> Tuple[bool, str]:
        """Start an exploration mission for a fleet."""
        self.exploration_system.initialize_system_exploration(system, fleet.empire_id)
        
        success = self.exploration_system.start_exploration_mission(
            fleet, system, mission_type, current_time
        )
        
        if success:
            self.initialize_empire_knowledge(fleet.empire_id)
            self.empire_knowledge[fleet.empire_id]["exploration_missions"] += 1
            return True, f"Started {mission_type} mission in {system.name}"
        
        return False, f"Failed to start {mission_type} mission"
    
    def initiate_fleet_jump(
        self,
        fleet: Fleet,
        jump_point_id: str,
        systems: Dict[str, StarSystem],
        ships: Dict[str, Ship],
        empire_technologies: Dict[str, Any],
        current_time: float
    ) -> Tuple[bool, str]:
        """Initiate a jump for a fleet through a specific jump point."""
        # Find the jump point
        jump_point = None
        current_system = systems.get(fleet.system_id)
        
        if current_system:
            for jp in current_system.jump_points:
                if jp.id == jump_point_id:
                    jump_point = jp
                    break
        
        if not jump_point:
            return False, "Jump point not found"
        
        if not jump_point.connects_to:
            return False, "Jump point destination not set"
        
        # Check if target system exists
        target_system_id = jump_point.connects_to
        if target_system_id not in systems:
            return False, "Target system does not exist"
        
        # Initiate the jump
        success, message = self.travel_system.initiate_jump_preparation(
            fleet, jump_point, target_system_id, current_time, ships, empire_technologies
        )
        
        if success:
            self.initialize_empire_knowledge(fleet.empire_id)
            self.empire_knowledge[fleet.empire_id]["total_jumps"] += 1
            
            # Update empire knowledge of systems
            empire_knowledge = self.empire_knowledge[fleet.empire_id]
            empire_knowledge["known_systems"].add(fleet.system_id)
            empire_knowledge["known_systems"].add(target_system_id)
            empire_knowledge["known_jump_points"].add(jump_point_id)
        
        return success, message
    
    def get_available_jumps_for_fleet(
        self,
        fleet: Fleet,
        systems: Dict[str, StarSystem],
        ships: Dict[str, Ship],
        empire_technologies: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get available jump options for a fleet."""
        current_system = systems.get(fleet.system_id)
        if not current_system:
            return []
        
        available_jumps = self.travel_system.get_available_jumps(
            fleet, current_system, ships, empire_technologies
        )
        
        # Enhance with additional information
        for jump_info in available_jumps:
            jump_point_id = jump_info["jump_point_id"]
            target_system_id = jump_info["target_system_id"]
            
            # Add target system information if known
            target_system = systems.get(target_system_id)
            if target_system:
                jump_info["target_system_name"] = target_system.name
                jump_info["target_explored"] = target_system.is_explored
                
                # Add exploration status for the target system
                exploration_status = self.exploration_system.get_exploration_status(
                    target_system_id, fleet.empire_id
                )
                jump_info["target_exploration_status"] = exploration_status
        
        return available_jumps
    
    def get_fleet_jump_status(self, fleet_id: str) -> Dict[str, Any]:
        """Get current jump status for a fleet."""
        return self.travel_system.get_jump_status(fleet_id)
    
    def cancel_fleet_jump(self, fleet_id: str) -> Tuple[bool, str]:
        """Cancel an active jump operation for a fleet."""
        return self.travel_system.cancel_jump_operation(fleet_id)
    
    def get_system_exploration_status(self, system_id: str, empire_id: str) -> Dict[str, Any]:
        """Get exploration status for a system."""
        return self.exploration_system.get_exploration_status(system_id, empire_id)
    
    def get_empire_jump_network(self, empire_id: str, systems: Dict[str, StarSystem]) -> Dict[str, Any]:
        """Get the jump network as known by a specific empire."""
        self.initialize_empire_knowledge(empire_id)
        empire_knowledge = self.empire_knowledge[empire_id]
        
        network = {
            "known_systems": list(empire_knowledge["known_systems"]),
            "known_jump_points": list(empire_knowledge["known_jump_points"]),
            "system_connections": {},
            "reachable_systems": {},
            "statistics": {
                "exploration_missions": empire_knowledge["exploration_missions"],
                "total_jumps": empire_knowledge["total_jumps"],
                "discovered_jump_points": empire_knowledge["discovered_jump_points"]
            }
        }
        
        # Build empire-specific network connections
        for system_id in empire_knowledge["known_systems"]:
            system = systems.get(system_id)
            if not system:
                continue
            
            connections = []
            for jump_point in system.jump_points:
                if (jump_point.id in empire_knowledge["known_jump_points"] and
                    jump_point.is_accessible_by(empire_id)):
                    connections.append({
                        "jump_point_id": jump_point.id,
                        "jump_point_name": jump_point.name,
                        "target_system_id": jump_point.connects_to,
                        "status": jump_point.status.value,
                        "survey_level": jump_point.survey_level
                    })
            
            network["system_connections"][system_id] = connections
        
        # Calculate reachable systems from each known system
        for system_id in empire_knowledge["known_systems"]:
            # Create a temporary network for path finding
            temp_network = {}
            for sys_id, connections in network["system_connections"].items():
                temp_network[sys_id] = {}
                for conn in connections:
                    if conn["target_system_id"] in empire_knowledge["known_systems"]:
                        temp_network[sys_id][conn["target_system_id"]] = 1.0
            
            # Find reachable systems
            reachable = self._find_reachable_systems_for_empire(system_id, temp_network, 5)
            network["reachable_systems"][system_id] = reachable
        
        return network
    
    def survey_jump_point(
        self,
        fleet: Fleet,
        jump_point_id: str,
        systems: Dict[str, StarSystem],
        current_time: float
    ) -> Tuple[bool, str]:
        """Start a survey mission for a specific jump point."""
        current_system = systems.get(fleet.system_id)
        if not current_system:
            return False, "Fleet system not found"
        
        jump_point = None
        for jp in current_system.jump_points:
            if jp.id == jump_point_id:
                jump_point = jp
                break
        
        if not jump_point:
            return False, "Jump point not found in current system"
        
        success = self.exploration_system.survey_jump_point(
            fleet, jump_point, fleet.empire_id, current_time
        )
        
        if success:
            return True, f"Started survey of jump point {jump_point.name}"
        else:
            return False, "Failed to start jump point survey"
    
    def generate_enhanced_jump_network(
        self,
        systems: List[StarSystem],
        connectivity_level: float = 0.3
    ) -> None:
        """Generate an enhanced jump point network with better connectivity and hidden points."""
        logger.info("Generating enhanced jump point network for %d systems", len(systems))
        
        # Clear existing jump points
        for system in systems:
            system.jump_points.clear()
        
        # Create primary network connections (ensure all systems are reachable)
        self._create_primary_network(systems)
        
        # Add secondary connections for better connectivity
        self._add_secondary_connections(systems, connectivity_level)
        
        # Add some hidden/dormant jump points
        self._add_special_jump_points(systems)
        
        # Update the network graph
        systems_dict = {s.id: s for s in systems}
        self.update_network(systems_dict)
        
        logger.info("Enhanced jump point network generated")
    
    def _find_reachable_systems_for_empire(
        self,
        origin_system_id: str,
        network: Dict[str, Dict[str, float]],
        max_jumps: int
    ) -> Dict[str, int]:
        """Find reachable systems for empire-specific network."""
        reachable = {origin_system_id: 0}
        to_explore = [(origin_system_id, 0)]
        
        while to_explore:
            current_system, jumps = to_explore.pop(0)
            
            if jumps >= max_jumps:
                continue
            
            for connected_system in network.get(current_system, {}):
                if connected_system not in reachable or reachable[connected_system] > jumps + 1:
                    reachable[connected_system] = jumps + 1
                    to_explore.append((connected_system, jumps + 1))
        
        return reachable
    
    def _create_primary_network(self, systems: List[StarSystem]) -> None:
        """Create primary jump point connections ensuring all systems are reachable."""
        if len(systems) < 2:
            return
        
        # Create a minimum spanning tree to ensure connectivity
        connected = {systems[0].id}
        unconnected = [s for s in systems[1:]]
        
        while unconnected:
            # Find the closest pair between connected and unconnected
            best_distance = float('inf')
            best_connected = None
            best_unconnected = None
            
            for connected_sys in [s for s in systems if s.id in connected]:
                for unconnected_sys in unconnected:
                    # Calculate "distance" based on system characteristics
                    distance = self._calculate_system_distance(connected_sys, unconnected_sys)
                    if distance < best_distance:
                        best_distance = distance
                        best_connected = connected_sys
                        best_unconnected = unconnected_sys
            
            if best_connected and best_unconnected:
                # Create bidirectional jump points
                self._create_jump_point_pair(best_connected, best_unconnected)
                connected.add(best_unconnected.id)
                unconnected.remove(best_unconnected)
    
    def _add_secondary_connections(self, systems: List[StarSystem], connectivity_level: float) -> None:
        """Add secondary jump point connections for better network connectivity."""
        total_possible = len(systems) * (len(systems) - 1) // 2
        target_connections = int(total_possible * connectivity_level)
        current_connections = sum(len(s.jump_points) for s in systems) // 2
        
        additional_needed = max(0, target_connections - current_connections)
        
        for _ in range(additional_needed):
            # Pick two random systems that aren't already connected
            sys1, sys2 = random.sample(systems, 2)
            
            # Check if they're already connected
            already_connected = any(jp.connects_to == sys2.id for jp in sys1.jump_points)
            if already_connected:
                continue
            
            # Add connection with some probability based on "distance"
            distance = self._calculate_system_distance(sys1, sys2)
            connection_probability = max(0.1, 1.0 - (distance / 10.0))
            
            if random.random() < connection_probability:
                self._create_jump_point_pair(sys1, sys2)
    
    def _add_special_jump_points(self, systems: List[StarSystem]) -> None:
        """Add special jump points (unstable, dormant, etc.) to some systems."""
        for system in systems:
            # 20% chance for an unstable jump point
            if random.random() < 0.2:
                target_system = random.choice([s for s in systems if s != system])
                jump_point = self._create_jump_point(
                    system, target_system,
                    jump_type=JumpPointType.UNSTABLE,
                    stability=random.uniform(0.3, 0.7)
                )
                system.jump_points.append(jump_point)
            
            # 10% chance for a dormant jump point (initially inactive)
            if random.random() < 0.1:
                target_system = random.choice([s for s in systems if s != system])
                jump_point = self._create_jump_point(
                    system, target_system,
                    jump_type=JumpPointType.DORMANT,
                    status=JumpPointStatus.INACTIVE
                )
                system.jump_points.append(jump_point)
    
    def _calculate_system_distance(self, sys1: StarSystem, sys2: StarSystem) -> float:
        """Calculate a relative "distance" between two star systems."""
        # This is a simplified calculation - in a full implementation,
        # you might use actual galactic coordinates
        
        # Use system characteristics to determine connection likelihood
        star_mass_diff = abs(sys1.star_mass - sys2.star_mass)
        planet_count_diff = abs(len(sys1.planets) - len(sys2.planets))
        
        # Systems with similar characteristics are more likely to be connected
        distance = star_mass_diff + planet_count_diff * 0.5
        
        # Add some randomness
        distance += random.uniform(0.5, 2.0)
        
        return distance
    
    def _create_jump_point_pair(self, sys1: StarSystem, sys2: StarSystem) -> None:
        """Create a bidirectional pair of jump points between two systems."""
        # Jump point from sys1 to sys2
        jp1 = self._create_jump_point(sys1, sys2)
        sys1.jump_points.append(jp1)
        
        # Jump point from sys2 to sys1
        jp2 = self._create_jump_point(sys2, sys1)
        sys2.jump_points.append(jp2)
    
    def _create_jump_point(
        self,
        origin_system: StarSystem,
        target_system: StarSystem,
        jump_type: JumpPointType = JumpPointType.NATURAL,
        status: JumpPointStatus = JumpPointStatus.UNKNOWN,
        stability: float = None
    ) -> JumpPoint:
        """Create a jump point in the origin system connecting to target system."""
        # Generate position in the outer system
        import math
        
        distance_au = random.uniform(2.0, 6.0)
        angle = random.uniform(0.0, 2 * math.pi)
        r = distance_au * CONSTANTS["AU_TO_KM"]
        
        position = Vector3D(
            x=r * math.cos(angle),
            y=r * math.sin(angle),
            z=random.uniform(-0.05 * r, 0.05 * r)
        )
        
        if stability is None:
            stability = random.uniform(0.8, 1.0) if jump_type == JumpPointType.NATURAL else random.uniform(0.5, 0.9)
        
        jump_point = JumpPoint(
            name=f"JP-{target_system.name[:3].upper()}",
            position=position,
            connects_to=target_system.id,
            jump_point_type=jump_type,
            status=status,
            stability=stability,
            size_class=random.randint(1, 4),
            exploration_difficulty=random.uniform(0.8, 1.5),
            fuel_cost_modifier=random.uniform(0.9, 1.1),
            travel_time_modifier=random.uniform(0.9, 1.1)
        )
        
        return jump_point

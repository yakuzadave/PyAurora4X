"""
Enhanced Fleet Jump Travel System for PyAurora 4X

Manages fleet travel through jump points including fuel consumption,
travel time calculations, jump drive requirements, and multi-fleet coordination.
"""

import logging
import math
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from pyaurora4x.core.models import Fleet, StarSystem, JumpPoint, Empire, Vector3D, Ship
from pyaurora4x.core.enums import (
    FleetStatus, JumpPointStatus, ComponentType, CONSTANTS
)

logger = logging.getLogger(__name__)


class JumpStatus(Enum):
    """Status of jump operations."""
    PENDING = "pending"
    PREPARING = "preparing"
    JUMPING = "jumping"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JumpPreparation:
    """Represents preparation phase for a jump."""
    fleet_id: str
    jump_point_id: str
    target_system_id: str
    start_time: float
    preparation_time: float
    fuel_cost: float
    progress: float = 0.0
    status: JumpStatus = JumpStatus.PENDING


@dataclass
class JumpOperation:
    """Represents an active jump operation."""
    fleet_id: str
    origin_system_id: str
    target_system_id: str
    jump_point_id: str
    start_time: float
    travel_time: float
    fuel_consumed: float
    progress: float = 0.0
    status: JumpStatus = JumpStatus.JUMPING


@dataclass
class JumpRequirements:
    """Requirements and costs for a jump operation."""
    has_jump_drive: bool
    fuel_cost: float
    travel_time: float
    preparation_time: float
    max_ship_size: int
    min_ship_size: int
    tech_requirements: List[str]
    can_jump: bool
    failure_reasons: List[str]


class FleetJumpTravelSystem:
    """Manages fleet travel through jump points."""
    
    def __init__(self):
        self.active_preparations: Dict[str, JumpPreparation] = {}  # fleet_id -> preparation
        self.active_jumps: Dict[str, JumpOperation] = {}  # fleet_id -> jump operation
        self.jump_history: Dict[str, List[Dict[str, Any]]] = {}  # fleet_id -> history
        
        # Jump drive requirements
        self.jump_drive_tech_requirements = [
            "basic_jump_drive_technology",
            "gravitational_physics"
        ]
        
        logger.info("Fleet Jump Travel System initialized")
    
    def calculate_jump_requirements(
        self,
        fleet: Fleet,
        jump_point: JumpPoint,
        ships: Dict[str, Ship],
        empire_technologies: Dict[str, Any]
    ) -> JumpRequirements:
        """Calculate requirements and feasibility for a fleet to use a jump point."""
        requirements = JumpRequirements(
            has_jump_drive=False,
            fuel_cost=0.0,
            travel_time=0.0,
            preparation_time=0.0,
            max_ship_size=0,
            min_ship_size=float('inf'),
            tech_requirements=[],
            can_jump=True,
            failure_reasons=[]
        )
        
        # Check if fleet has any ships
        if not fleet.ships:
            requirements.can_jump = False
            requirements.failure_reasons.append("Fleet has no ships")
            return requirements
        
        # Check jump point accessibility
        if not jump_point.is_accessible_by(fleet.empire_id):
            requirements.can_jump = False
            requirements.failure_reasons.append("Jump point not accessible")
            return requirements
        
        # Check jump point status
        if jump_point.status not in [JumpPointStatus.ACTIVE, JumpPointStatus.MAPPED]:
            requirements.can_jump = False
            requirements.failure_reasons.append(f"Jump point status is {jump_point.status.value}")
            return requirements
        
        # Check fleet fuel levels
        if fleet.fuel_remaining < 20.0:  # Need at least 20% fuel
            requirements.can_jump = False
            requirements.failure_reasons.append("Insufficient fleet fuel")
            return requirements
        
        # Analyze fleet composition
        total_mass = 0.0
        ship_count = 0
        has_jump_capable_ships = 0
        
        for ship_id in fleet.ships:
            ship = ships.get(ship_id)
            if not ship:
                continue
                
            ship_count += 1
            total_mass += ship.current_mass
            
            # Check for jump drive (simplified - assume all ships have basic jump capability)
            # In a full implementation, would check ship design components
            has_jump_capable_ships += 1
            
            # TODO: Check actual ship size classes against jump point limits
            
        if has_jump_capable_ships == 0:
            requirements.can_jump = False
            requirements.failure_reasons.append("No ships have jump drive capability")
            return requirements
        
        requirements.has_jump_drive = True
        
        # Calculate costs and times
        requirements.fuel_cost = jump_point.calculate_fuel_cost(total_mass, ship_count)
        requirements.travel_time = jump_point.calculate_travel_time(total_mass, ship_count)
        requirements.preparation_time = self._calculate_preparation_time(fleet, jump_point)
        
        # Check if fleet has enough fuel for the jump
        fuel_percentage_needed = (requirements.fuel_cost / fleet.fuel_remaining) * 100.0
        if fuel_percentage_needed > fleet.fuel_remaining:
            requirements.can_jump = False
            requirements.failure_reasons.append(f"Insufficient fuel (need {fuel_percentage_needed:.1f}%)")
        
        # Check technology requirements
        if jump_point.tech_requirement:
            requirements.tech_requirements.append(jump_point.tech_requirement)
            # TODO: Check if empire has required technology
        
        return requirements
    
    def initiate_jump_preparation(
        self,
        fleet: Fleet,
        jump_point: JumpPoint,
        target_system_id: str,
        current_time: float,
        ships: Dict[str, Ship],
        empire_technologies: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Initiate jump preparation for a fleet."""
        if fleet.id in self.active_preparations or fleet.id in self.active_jumps:
            return False, "Fleet is already preparing for or executing a jump"
        
        # Check jump requirements
        requirements = self.calculate_jump_requirements(fleet, jump_point, ships, empire_technologies)
        if not requirements.can_jump:
            return False, f"Jump not possible: {'; '.join(requirements.failure_reasons)}"
        
        # Create preparation operation
        preparation = JumpPreparation(
            fleet_id=fleet.id,
            jump_point_id=jump_point.id,
            target_system_id=target_system_id,
            start_time=current_time,
            preparation_time=requirements.preparation_time,
            fuel_cost=requirements.fuel_cost
        )
        
        self.active_preparations[fleet.id] = preparation
        
        # Update fleet status
        fleet.status = FleetStatus.FORMING_UP  # Using existing status for preparation
        fleet.current_orders.append(f"Preparing jump to {target_system_id}")
        
        logger.info(
            "Fleet %s started jump preparation to system %s via jump point %s (prep time: %.1f seconds)",
            fleet.name, target_system_id, jump_point.name, requirements.preparation_time
        )
        
        return True, "Jump preparation initiated"
    
    def execute_jump(
        self,
        fleet: Fleet,
        preparation: JumpPreparation,
        jump_point: JumpPoint,
        current_time: float
    ) -> Tuple[bool, str]:
        """Execute the actual jump after preparation is complete."""
        if preparation.status != JumpStatus.PREPARING:
            return False, "Fleet is not ready to jump"
        
        # Consume fuel
        fleet.fuel_remaining = max(0.0, fleet.fuel_remaining - preparation.fuel_cost)
        
        # Calculate travel time with some randomization for realism
        base_travel_time = jump_point.calculate_travel_time(fleet.total_mass, len(fleet.ships))
        travel_time = base_travel_time * random.uniform(0.9, 1.1)  # ±10% variation
        
        # Create jump operation
        jump_operation = JumpOperation(
            fleet_id=fleet.id,
            origin_system_id=fleet.system_id,
            target_system_id=preparation.target_system_id,
            jump_point_id=jump_point.id,
            start_time=current_time,
            travel_time=travel_time,
            fuel_consumed=preparation.fuel_cost
        )
        
        self.active_jumps[fleet.id] = jump_operation
        
        # Update fleet status
        fleet.status = FleetStatus.IN_TRANSIT
        fleet.current_orders.clear()
        fleet.current_orders.append(f"Jumping to {preparation.target_system_id}")
        
        # Record jump point usage
        jump_point.traffic_level += 1
        jump_point.last_transit = current_time
        
        # Remove from preparations
        if fleet.id in self.active_preparations:
            del self.active_preparations[fleet.id]
        
        logger.info(
            "Fleet %s executed jump to system %s (travel time: %.1f seconds, fuel consumed: %.1f)",
            fleet.name, preparation.target_system_id, travel_time, preparation.fuel_cost
        )
        
        return True, f"Jump executed - ETA: {travel_time:.1f} seconds"
    
    def process_jump_operations(
        self,
        fleets: Dict[str, Fleet],
        systems: Dict[str, StarSystem],
        current_time: float,
        delta_seconds: float
    ) -> Dict[str, str]:
        """Process all active jump preparations and operations."""
        results = {}
        
        # Process preparations
        completed_preparations = []
        for fleet_id, preparation in self.active_preparations.items():
            fleet = fleets.get(fleet_id)
            if not fleet:
                completed_preparations.append(fleet_id)
                continue
            
            # Update preparation progress
            elapsed_time = current_time - preparation.start_time
            preparation.progress = min(1.0, elapsed_time / preparation.preparation_time)
            
            if preparation.progress >= 1.0:
                preparation.status = JumpStatus.PREPARING
                results[fleet_id] = "Jump preparation complete - ready to jump"
                
                # Auto-execute jump if preparation is complete
                jump_point = self._find_jump_point(preparation.jump_point_id, systems)
                if jump_point:
                    success, message = self.execute_jump(fleet, preparation, jump_point, current_time)
                    if success:
                        results[fleet_id] = message
                    else:
                        preparation.status = JumpStatus.FAILED
                        results[fleet_id] = f"Jump execution failed: {message}"
                        completed_preparations.append(fleet_id)
                else:
                    preparation.status = JumpStatus.FAILED
                    results[fleet_id] = "Jump point not found"
                    completed_preparations.append(fleet_id)
        
        # Clean up completed preparations
        for fleet_id in completed_preparations:
            if fleet_id in self.active_preparations:
                del self.active_preparations[fleet_id]
        
        # Process active jumps
        completed_jumps = []
        for fleet_id, jump_op in self.active_jumps.items():
            fleet = fleets.get(fleet_id)
            if not fleet:
                completed_jumps.append(fleet_id)
                continue
            
            # Update jump progress
            elapsed_time = current_time - jump_op.start_time
            jump_op.progress = min(1.0, elapsed_time / jump_op.travel_time)
            
            if jump_op.progress >= 1.0:
                # Jump completed - move fleet to target system
                success = self._complete_jump(fleet, jump_op, systems, current_time)
                if success:
                    results[fleet_id] = f"Jump to {jump_op.target_system_id} completed"
                    jump_op.status = JumpStatus.COMPLETED
                else:
                    results[fleet_id] = "Jump completion failed"
                    jump_op.status = JumpStatus.FAILED
                
                completed_jumps.append(fleet_id)
        
        # Clean up completed jumps
        for fleet_id in completed_jumps:
            if fleet_id in self.active_jumps:
                self._record_jump_history(self.active_jumps[fleet_id])
                del self.active_jumps[fleet_id]
        
        return results
    
    def cancel_jump_operation(self, fleet_id: str) -> Tuple[bool, str]:
        """Cancel an active jump preparation or operation."""
        if fleet_id in self.active_preparations:
            preparation = self.active_preparations[fleet_id]
            preparation.status = JumpStatus.CANCELLED
            del self.active_preparations[fleet_id]
            return True, "Jump preparation cancelled"
        
        if fleet_id in self.active_jumps:
            # Cannot cancel a jump in progress
            return False, "Cannot cancel jump in progress"
        
        return False, "No active jump operation to cancel"
    
    def get_jump_status(self, fleet_id: str) -> Dict[str, Any]:
        """Get the status of jump operations for a fleet."""
        status = {
            "has_operation": False,
            "operation_type": None,
            "progress": 0.0,
            "remaining_time": 0.0,
            "status": None,
            "details": {}
        }
        
        if fleet_id in self.active_preparations:
            prep = self.active_preparations[fleet_id]
            status.update({
                "has_operation": True,
                "operation_type": "preparation",
                "progress": prep.progress,
                "remaining_time": max(0.0, prep.preparation_time * (1.0 - prep.progress)),
                "status": prep.status.value,
                "details": {
                    "target_system": prep.target_system_id,
                    "fuel_cost": prep.fuel_cost,
                    "jump_point_id": prep.jump_point_id
                }
            })
        
        elif fleet_id in self.active_jumps:
            jump_op = self.active_jumps[fleet_id]
            status.update({
                "has_operation": True,
                "operation_type": "jump",
                "progress": jump_op.progress,
                "remaining_time": max(0.0, jump_op.travel_time * (1.0 - jump_op.progress)),
                "status": jump_op.status.value,
                "details": {
                    "origin_system": jump_op.origin_system_id,
                    "target_system": jump_op.target_system_id,
                    "fuel_consumed": jump_op.fuel_consumed,
                    "jump_point_id": jump_op.jump_point_id
                }
            })
        
        return status
    
    def get_jump_history(self, fleet_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get jump history for a fleet."""
        history = self.jump_history.get(fleet_id, [])
        return history[-limit:] if limit > 0 else history
    
    def get_available_jumps(
        self,
        fleet: Fleet,
        current_system: StarSystem,
        ships: Dict[str, Ship],
        empire_technologies: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get list of available jump destinations for a fleet."""
        available_jumps = []
        
        for jump_point in current_system.jump_points:
            if not jump_point.is_accessible_by(fleet.empire_id):
                continue
            
            requirements = self.calculate_jump_requirements(
                fleet, jump_point, ships, empire_technologies
            )
            
            jump_info = {
                "jump_point_id": jump_point.id,
                "jump_point_name": jump_point.name,
                "target_system_id": jump_point.connects_to,
                "can_jump": requirements.can_jump,
                "fuel_cost": requirements.fuel_cost,
                "travel_time": requirements.travel_time,
                "preparation_time": requirements.preparation_time,
                "failure_reasons": requirements.failure_reasons,
                "jump_point_status": jump_point.status.value,
                "stability": jump_point.stability,
                "size_class": jump_point.size_class
            }
            
            available_jumps.append(jump_info)
        
        return available_jumps
    
    # Private helper methods
    
    def _calculate_preparation_time(self, fleet: Fleet, jump_point: JumpPoint) -> float:
        """Calculate time needed to prepare for a jump."""
        base_time = 30.0  # 30 seconds base preparation
        
        # More ships = longer preparation
        ship_factor = len(fleet.ships) * 5.0
        
        # Jump point difficulty
        stability_factor = (2.0 - jump_point.stability) * 10.0
        
        # Fleet experience (simplified - could be based on previous jumps)
        experience_factor = 1.0  # TODO: Implement fleet experience system
        
        total_time = (base_time + ship_factor + stability_factor) / experience_factor
        return max(10.0, total_time)  # Minimum 10 seconds
    
    def _find_jump_point(self, jump_point_id: str, systems: Dict[str, StarSystem]) -> Optional[JumpPoint]:
        """Find a jump point by ID across all systems."""
        for system in systems.values():
            for jump_point in system.jump_points:
                if jump_point.id == jump_point_id:
                    return jump_point
        return None
    
    def _complete_jump(
        self,
        fleet: Fleet,
        jump_op: JumpOperation,
        systems: Dict[str, StarSystem],
        current_time: float
    ) -> bool:
        """Complete a jump operation by moving the fleet to the target system."""
        target_system = systems.get(jump_op.target_system_id)
        if not target_system:
            logger.error("Target system %s not found for fleet %s", jump_op.target_system_id, fleet.name)
            return False
        
        # Move fleet to target system
        fleet.system_id = jump_op.target_system_id
        
        # Position fleet near the target jump point (if it has one leading back)
        target_position = Vector3D()  # Default to system center
        
        # Try to find the corresponding jump point in the target system
        for jump_point in target_system.jump_points:
            if jump_point.connects_to == jump_op.origin_system_id:
                # Position fleet near this jump point
                offset_distance = 1000.0  # 1000 km offset
                angle = random.uniform(0.0, 2 * math.pi)
                
                target_position = Vector3D(
                    x=jump_point.position.x + offset_distance * math.cos(angle),
                    y=jump_point.position.y + offset_distance * math.sin(angle),
                    z=jump_point.position.z
                )
                break
        
        fleet.position = target_position
        fleet.velocity = Vector3D()  # Stop the fleet
        fleet.destination = None
        fleet.estimated_arrival = None
        fleet.status = FleetStatus.IDLE
        fleet.current_orders.clear()
        
        logger.info(
            "Fleet %s completed jump from %s to %s",
            fleet.name, jump_op.origin_system_id, jump_op.target_system_id
        )
        
        return True
    
    def _record_jump_history(self, jump_op: JumpOperation) -> None:
        """Record a completed jump operation in the fleet's history."""
        if jump_op.fleet_id not in self.jump_history:
            self.jump_history[jump_op.fleet_id] = []
        
        history_entry = {
            "origin_system": jump_op.origin_system_id,
            "target_system": jump_op.target_system_id,
            "jump_point_id": jump_op.jump_point_id,
            "start_time": jump_op.start_time,
            "travel_time": jump_op.travel_time,
            "fuel_consumed": jump_op.fuel_consumed,
            "status": jump_op.status.value
        }
        
        self.jump_history[jump_op.fleet_id].append(history_entry)
        
        # Keep only last 50 jumps per fleet
        if len(self.jump_history[jump_op.fleet_id]) > 50:
            self.jump_history[jump_op.fleet_id] = self.jump_history[jump_op.fleet_id][-50:]

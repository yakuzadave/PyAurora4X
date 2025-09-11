"""
Fleet Command Manager for PyAurora 4X

Centralized management of fleet operations, order processing, combat resolution,
formation control, and tactical coordination for advanced fleet command.
"""

import logging
import math
from typing import Dict, List, Optional, Tuple, Any
import uuid

from pyaurora4x.core.models import Fleet, Ship, Empire, Vector3D
from pyaurora4x.core.enums import (
    OrderType, OrderPriority, OrderStatus, FleetStatus, FleetFormation,
    CombatRole, WeaponType, DefenseType, LogisticsType
)
from pyaurora4x.core.fleet_command import (
    FleetOrder, FormationTemplate, FleetFormationState, ShipPositionData,
    FleetCommandState, CombatEngagement, CombatCapabilities, LogisticsRequirements,
    WeaponSystem, DefenseSystem, get_default_formation_templates
)

logger = logging.getLogger(__name__)


class FleetCommandManager:
    """Central manager for all fleet command operations."""
    
    def __init__(self):
        self.formation_templates: Dict[str, FormationTemplate] = get_default_formation_templates()
        self.fleet_command_states: Dict[str, FleetCommandState] = {}  # fleet_id -> command_state
        self.fleet_orders: Dict[str, FleetOrder] = {}  # order_id -> order
        self.combat_engagements: Dict[str, CombatEngagement] = {}  # engagement_id -> engagement
        self.formation_states: Dict[str, FleetFormationState] = {}  # fleet_id -> formation_state
        
        # Command processing
        self.order_processors = self._initialize_order_processors()
        self.combat_resolver = CombatResolver()
        self.formation_manager = FormationManager(self.formation_templates)
    
    def initialize_fleet_command(self, fleet: Fleet, empire: Empire) -> FleetCommandState:
        """Initialize command state for a fleet."""
        if fleet.id in self.fleet_command_states:
            return self.fleet_command_states[fleet.id]
        
        command_state = FleetCommandState(
            fleet_id=fleet.id,
            flagship_id=fleet.ships[0] if fleet.ships else None,
            commanding_officer_id=fleet.commander_id,
            formation_templates=self.formation_templates.copy()
        )
        
        # Initialize combat capabilities from fleet composition
        self._calculate_fleet_combat_capabilities(fleet, command_state)
        
        # Initialize logistics requirements
        self._calculate_fleet_logistics_requirements(fleet, command_state)
        
        self.fleet_command_states[fleet.id] = command_state
        logger.info("Initialized fleet command for %s", fleet.name)
        return command_state
    
    def issue_order(self, fleet_id: str, order_type: OrderType, parameters: Dict[str, Any] = None,
                   priority: OrderPriority = OrderPriority.NORMAL, **kwargs) -> Tuple[bool, str]:
        """Issue a new order to a fleet."""
        if fleet_id not in self.fleet_command_states:
            return False, "Fleet command not initialized"
        
        # Create the order
        order = FleetOrder(
            fleet_id=fleet_id,
            order_type=order_type,
            priority=priority,
            parameters=parameters or {},
            **kwargs
        )
        
        # Validate order
        is_valid, validation_message = self._validate_order(order)
        if not is_valid:
            return False, validation_message
        
        # Add to order tracking
        self.fleet_orders[order.id] = order
        
        # Add to fleet command state
        command_state = self.fleet_command_states[fleet_id]
        command_state.current_orders[order.id] = order
        command_state.order_queue.append(order.id)
        
        # Sort order queue by priority
        self._sort_order_queue(fleet_id)
        
        logger.info("Issued %s order to fleet %s (Priority: %s)", 
                   order_type.value, fleet_id, priority.value)
        return True, f"Order {order_type.value} issued successfully"
    
    def cancel_order(self, fleet_id: str, order_id: str) -> bool:
        """Cancel a fleet order."""
        if fleet_id not in self.fleet_command_states:
            return False
        
        command_state = self.fleet_command_states[fleet_id]
        
        if order_id not in command_state.current_orders:
            return False
        
        # Remove from queue and current orders
        if order_id in command_state.order_queue:
            command_state.order_queue.remove(order_id)
        
        order = command_state.current_orders[order_id]
        order.status = OrderStatus.CANCELLED
        
        del command_state.current_orders[order_id]
        
        logger.info("Cancelled order %s for fleet %s", order.order_type.value, fleet_id)
        return True
    
    def process_fleet_orders(self, fleet: Fleet, empire: Empire, delta_seconds: float) -> None:
        """Process all pending orders for a fleet."""
        if fleet.id not in self.fleet_command_states:
            return
        
        command_state = self.fleet_command_states[fleet.id]
        
        # Process orders in priority order
        for order_id in command_state.order_queue[:]:  # Copy list to avoid modification during iteration
            if order_id not in command_state.current_orders:
                continue
            
            order = command_state.current_orders[order_id]
            
            # Skip if order is not ready to execute
            if not self._check_order_preconditions(order, fleet, empire):
                continue
            
            # Process the order
            self._process_order(order, fleet, empire, delta_seconds)
            
            # Remove completed orders
            if order.status in [OrderStatus.COMPLETED, OrderStatus.FAILED, OrderStatus.CANCELLED]:
                command_state.order_queue.remove(order_id)
                del command_state.current_orders[order_id]
                command_state.completed_orders.append(order_id)
                
                if order.status == OrderStatus.COMPLETED:
                    command_state.total_missions += 1
                    if order.status == OrderStatus.COMPLETED:
                        command_state.mission_success_rate = (
                            (command_state.mission_success_rate * (command_state.total_missions - 1) + 1.0)
                            / command_state.total_missions
                        )
    
    def set_fleet_formation(self, fleet_id: str, formation_template_id: str) -> Tuple[bool, str]:
        """Set a formation for a fleet."""
        if fleet_id not in self.fleet_command_states:
            return False, "Fleet command not initialized"
        
        if formation_template_id not in self.formation_templates:
            return False, f"Formation template {formation_template_id} not found"
        
        template = self.formation_templates[formation_template_id]
        command_state = self.fleet_command_states[fleet_id]
        
        # Create or update formation state
        formation_state = FleetFormationState(
            fleet_id=fleet_id,
            formation_template_id=formation_template_id,
            current_spacing=template.formation_spacing,
            current_scale=template.formation_scale
        )
        
        self.formation_states[fleet_id] = formation_state
        command_state.formation_state = formation_state
        
        # Issue formation order
        return self.issue_order(
            fleet_id=fleet_id,
            order_type=OrderType.FORM_UP,
            parameters={"formation_template_id": formation_template_id},
            priority=OrderPriority.HIGH
        )
    
    def start_combat_engagement(self, attacking_fleet_ids: List[str], defending_fleet_ids: List[str],
                              system_id: str) -> str:
        """Start a combat engagement between fleets."""
        engagement = CombatEngagement(
            attacking_fleets=attacking_fleet_ids,
            defending_fleets=defending_fleet_ids,
            system_id=system_id,
            start_time=0.0  # Would use current game time
        )
        
        self.combat_engagements[engagement.id] = engagement
        
        # Update fleet statuses
        for fleet_id in attacking_fleet_ids + defending_fleet_ids:
            if fleet_id in self.fleet_command_states:
                self.fleet_command_states[fleet_id].current_engagement = engagement.id
        
        logger.info("Started combat engagement %s", engagement.id)
        return engagement.id
    
    def process_combat_engagements(self, fleets: Dict[str, Fleet], delta_seconds: float) -> None:
        """Process all active combat engagements."""
        for engagement_id, engagement in list(self.combat_engagements.items()):
            result = self.combat_resolver.process_engagement(engagement, fleets, delta_seconds)
            
            if result.get("completed", False):
                # Remove completed engagements
                del self.combat_engagements[engagement_id]
                
                # Update fleet states
                all_fleet_ids = engagement.attacking_fleets + engagement.defending_fleets
                for fleet_id in all_fleet_ids:
                    if fleet_id in self.fleet_command_states:
                        self.fleet_command_states[fleet_id].current_engagement = None
                        
                        # Update combat experience
                        command_state = self.fleet_command_states[fleet_id]
                        command_state.combat_experience += result.get("experience_gained", 1.0)
    
    def process_formation_updates(self, fleets: Dict[str, Fleet], delta_seconds: float) -> None:
        """Update fleet formations."""
        for fleet_id, formation_state in self.formation_states.items():
            if fleet_id not in fleets:
                continue
                
            fleet = fleets[fleet_id]
            template = self.formation_templates.get(formation_state.formation_template_id)
            
            if not template:
                continue
            
            self.formation_manager.update_formation(fleet, formation_state, template, delta_seconds)
    
    def get_fleet_tactical_status(self, fleet_id: str) -> Dict[str, Any]:
        """Get comprehensive tactical status for a fleet."""
        if fleet_id not in self.fleet_command_states:
            return {"error": "Fleet command not initialized"}
        
        command_state = self.fleet_command_states[fleet_id]
        formation_state = self.formation_states.get(fleet_id)
        
        return {
            "fleet_id": fleet_id,
            "command_effectiveness": command_state.command_effectiveness,
            "current_orders": len(command_state.current_orders),
            "pending_orders": len(command_state.order_queue),
            "formation": {
                "active": formation_state is not None and formation_state.is_formed,
                "template": formation_state.formation_template_id if formation_state else None,
                "integrity": formation_state.formation_integrity if formation_state else 0.0,
                "cohesion": formation_state.formation_cohesion if formation_state else 0.0,
            },
            "combat": {
                "in_combat": command_state.current_engagement is not None,
                "combat_rating": command_state.combat_capabilities.combat_rating,
                "experience": command_state.combat_experience,
                "morale": command_state.combat_capabilities.morale,
            },
            "logistics": {
                "fuel_status": command_state.logistics_requirements.current_fuel / 
                             command_state.logistics_requirements.fuel_capacity,
                "supply_status": command_state.logistics_requirements.supply_status,
                "maintenance_due": self._calculate_maintenance_status(command_state),
            },
            "performance": {
                "mission_success_rate": command_state.mission_success_rate,
                "total_missions": command_state.total_missions,
            }
        }
    
    # Private helper methods
    
    def _initialize_order_processors(self) -> Dict[OrderType, callable]:
        """Initialize order processing functions."""
        return {
            OrderType.MOVE_TO: self._process_move_to_order,
            OrderType.ATTACK: self._process_attack_order,
            OrderType.DEFEND: self._process_defend_order,
            OrderType.PATROL: self._process_patrol_order,
            OrderType.ESCORT: self._process_escort_order,
            OrderType.FORM_UP: self._process_form_up_order,
            OrderType.CHANGE_FORMATION: self._process_change_formation_order,
            OrderType.SURVEY: self._process_survey_order,
            OrderType.REFUEL: self._process_refuel_order,
            OrderType.REPAIR: self._process_repair_order,
            OrderType.RESUPPLY: self._process_resupply_order,
        }
    
    def _validate_order(self, order: FleetOrder) -> Tuple[bool, str]:
        """Validate that an order can be executed."""
        # Basic validation
        if not order.fleet_id:
            return False, "Invalid fleet ID"
        
        if order.fleet_id not in self.fleet_command_states:
            return False, "Fleet command not initialized"
        
        # Order-specific validation
        if order.order_type == OrderType.MOVE_TO and not order.target_position:
            return False, "Move order requires target position"
        
        if order.order_type == OrderType.ATTACK and not order.target_fleet_id:
            return False, "Attack order requires target fleet"
        
        if order.order_type == OrderType.FORM_UP:
            formation_id = order.parameters.get("formation_template_id")
            if not formation_id or formation_id not in self.formation_templates:
                return False, "Formation order requires valid formation template"
        
        return True, "Order is valid"
    
    def _sort_order_queue(self, fleet_id: str) -> None:
        """Sort the order queue by priority."""
        command_state = self.fleet_command_states[fleet_id]
        priority_order = {
            OrderPriority.EMERGENCY: 0,
            OrderPriority.HIGH: 1,
            OrderPriority.NORMAL: 2,
            OrderPriority.LOW: 3,
            OrderPriority.BACKGROUND: 4,
        }
        
        command_state.order_queue.sort(
            key=lambda order_id: priority_order.get(
                command_state.current_orders[order_id].priority, 5
            )
        )
    
    def _check_order_preconditions(self, order: FleetOrder, fleet: Fleet, empire: Empire) -> bool:
        """Check if an order's preconditions are met."""
        if not order.preconditions:
            return True
        
        # Implementation would check various preconditions
        # For now, return True
        return True
    
    def _process_order(self, order: FleetOrder, fleet: Fleet, empire: Empire, delta_seconds: float) -> None:
        """Process a single order."""
        if order.status == OrderStatus.PENDING:
            order.status = OrderStatus.ACTIVE
            order.start_time = 0.0  # Would use current game time
        
        # Get the appropriate processor
        processor = self.order_processors.get(order.order_type)
        if processor:
            try:
                processor(order, fleet, empire, delta_seconds)
            except Exception as e:
                logger.error("Error processing order %s: %s", order.order_type.value, e)
                order.status = OrderStatus.FAILED
                order.failure_reason = str(e)
        else:
            logger.warning("No processor found for order type %s", order.order_type.value)
            order.status = OrderStatus.FAILED
            order.failure_reason = "No processor available"
    
    def _calculate_fleet_combat_capabilities(self, fleet: Fleet, command_state: FleetCommandState) -> None:
        """Calculate combat capabilities for a fleet."""
        # Simplified combat capability calculation
        # In a full implementation, this would examine individual ships and their loadouts
        ship_count = len(fleet.ships)
        
        command_state.combat_capabilities.total_firepower = ship_count * 10.0
        command_state.combat_capabilities.total_defense = ship_count * 8.0
        command_state.combat_capabilities.combat_rating = ship_count * 9.0
        command_state.combat_capabilities.max_engagement_range = 15000.0
    
    def _calculate_fleet_logistics_requirements(self, fleet: Fleet, command_state: FleetCommandState) -> None:
        """Calculate logistics requirements for a fleet."""
        ship_count = len(fleet.ships)
        
        # Simplified logistics calculation
        command_state.logistics_requirements.fuel_capacity = ship_count * 1000.0
        command_state.logistics_requirements.current_fuel = ship_count * 1000.0
        command_state.logistics_requirements.fuel_consumption_rate = ship_count * 2.0
        command_state.logistics_requirements.crew_requirements = ship_count * 50
    
    def _calculate_maintenance_status(self, command_state: FleetCommandState) -> float:
        """Calculate maintenance status (0.0 = no maintenance needed, 1.0 = urgent maintenance)."""
        time_since_maintenance = 0.0  # Would calculate from current time
        maintenance_interval = command_state.logistics_requirements.maintenance_interval
        
        return min(1.0, time_since_maintenance / maintenance_interval)
    
    # Order processors
    
    def _process_move_to_order(self, order: FleetOrder, fleet: Fleet, empire: Empire, delta_seconds: float):
        """Process a move-to order."""
        if not order.target_position:
            order.status = OrderStatus.FAILED
            order.failure_reason = "No target position specified"
            return
        
        # Calculate distance to target
        current_pos = fleet.position
        target_pos = order.target_position
        
        distance = math.sqrt(
            (target_pos.x - current_pos.x) ** 2 +
            (target_pos.y - current_pos.y) ** 2 +
            (target_pos.z - current_pos.z) ** 2
        )
        
        # Simple movement calculation
        speed = fleet.max_speed if fleet.max_speed > 0 else 1000.0  # m/s
        movement_distance = speed * delta_seconds
        
        if distance <= movement_distance:
            # Reached destination
            fleet.position = target_pos
            fleet.status = FleetStatus.IDLE
            order.status = OrderStatus.COMPLETED
            order.completion_time = 0.0  # Would use current game time
            order.progress = 1.0
        else:
            # Move toward target
            direction_x = (target_pos.x - current_pos.x) / distance
            direction_y = (target_pos.y - current_pos.y) / distance
            direction_z = (target_pos.z - current_pos.z) / distance
            
            fleet.position.x += direction_x * movement_distance
            fleet.position.y += direction_y * movement_distance
            fleet.position.z += direction_z * movement_distance
            
            fleet.status = FleetStatus.MOVING
            order.progress = 1.0 - (distance - movement_distance) / distance
    
    def _process_attack_order(self, order: FleetOrder, fleet: Fleet, empire: Empire, delta_seconds: float):
        """Process an attack order."""
        # Simplified attack order processing
        fleet.status = FleetStatus.IN_COMBAT
        order.progress = min(1.0, order.progress + delta_seconds / 100.0)  # 100 second combat
        
        if order.progress >= 1.0:
            order.status = OrderStatus.COMPLETED
            fleet.status = FleetStatus.IDLE
    
    def _process_defend_order(self, order: FleetOrder, fleet: Fleet, empire: Empire, delta_seconds: float):
        """Process a defend order."""
        fleet.status = FleetStatus.IDLE  # Defensive posture
        order.status = OrderStatus.COMPLETED  # Instant defensive posture
    
    def _process_patrol_order(self, order: FleetOrder, fleet: Fleet, empire: Empire, delta_seconds: float):
        """Process a patrol order."""
        fleet.status = FleetStatus.PATROLLING
        # Patrol orders are typically continuous
        order.progress = min(1.0, order.progress + delta_seconds / 3600.0)  # 1 hour patrol
        
        if order.is_repeating and order.progress >= 1.0:
            order.progress = 0.0
            order.repeat_count += 1
            
            if order.max_repeats and order.repeat_count >= order.max_repeats:
                order.status = OrderStatus.COMPLETED
                fleet.status = FleetStatus.IDLE
    
    def _process_escort_order(self, order: FleetOrder, fleet: Fleet, empire: Empire, delta_seconds: float):
        """Process an escort order."""
        fleet.status = FleetStatus.ESCORTING
        order.status = OrderStatus.COMPLETED  # Instant escort assignment
    
    def _process_form_up_order(self, order: FleetOrder, fleet: Fleet, empire: Empire, delta_seconds: float):
        """Process a formation order."""
        formation_id = order.parameters.get("formation_template_id")
        if not formation_id:
            order.status = OrderStatus.FAILED
            return
        
        fleet.status = FleetStatus.FORMING_UP
        order.progress = min(1.0, order.progress + delta_seconds / 30.0)  # 30 second formation
        
        if order.progress >= 1.0:
            fleet.status = FleetStatus.IN_FORMATION
            order.status = OrderStatus.COMPLETED
            
            # Update formation state
            if fleet.id in self.formation_states:
                self.formation_states[fleet.id].is_formed = True
    
    def _process_change_formation_order(self, order: FleetOrder, fleet: Fleet, empire: Empire, delta_seconds: float):
        """Process a change formation order."""
        self._process_form_up_order(order, fleet, empire, delta_seconds)
    
    def _process_survey_order(self, order: FleetOrder, fleet: Fleet, empire: Empire, delta_seconds: float):
        """Process a survey order."""
        fleet.status = FleetStatus.SURVEYING
        order.progress = min(1.0, order.progress + delta_seconds / 300.0)  # 5 minute survey
        
        if order.progress >= 1.0:
            order.status = OrderStatus.COMPLETED
            fleet.status = FleetStatus.IDLE
    
    def _process_refuel_order(self, order: FleetOrder, fleet: Fleet, empire: Empire, delta_seconds: float):
        """Process a refuel order."""
        fleet.status = FleetStatus.REFUELING
        
        # Simple refueling logic
        command_state = self.fleet_command_states.get(fleet.id)
        if command_state:
            logistics = command_state.logistics_requirements
            refuel_rate = logistics.fuel_capacity * 0.1  # 10% per update
            fuel_needed = logistics.fuel_capacity - logistics.current_fuel
            
            if fuel_needed <= 0:
                order.status = OrderStatus.COMPLETED
                fleet.status = FleetStatus.IDLE
            else:
                refuel_amount = min(refuel_rate * delta_seconds, fuel_needed)
                logistics.current_fuel += refuel_amount
                order.progress = logistics.current_fuel / logistics.fuel_capacity
    
    def _process_repair_order(self, order: FleetOrder, fleet: Fleet, empire: Empire, delta_seconds: float):
        """Process a repair order."""
        fleet.status = FleetStatus.REPAIRING
        order.progress = min(1.0, order.progress + delta_seconds / 600.0)  # 10 minute repair
        
        if order.progress >= 1.0:
            order.status = OrderStatus.COMPLETED
            fleet.status = FleetStatus.IDLE
    
    def _process_resupply_order(self, order: FleetOrder, fleet: Fleet, empire: Empire, delta_seconds: float):
        """Process a resupply order."""
        fleet.status = FleetStatus.RESUPPLYING
        order.progress = min(1.0, order.progress + delta_seconds / 180.0)  # 3 minute resupply
        
        if order.progress >= 1.0:
            order.status = OrderStatus.COMPLETED
            fleet.status = FleetStatus.IDLE


class CombatResolver:
    """Handles combat engagement resolution."""
    
    def process_engagement(self, engagement: CombatEngagement, fleets: Dict[str, Fleet], 
                          delta_seconds: float) -> Dict[str, Any]:
        """Process a combat engagement."""
        # Very simplified combat resolution
        engagement.current_time += delta_seconds
        engagement.intensity = min(1.0, engagement.intensity + delta_seconds / 60.0)
        
        # Simple resolution after 2 minutes
        if engagement.current_time - engagement.start_time >= 120.0:
            return {
                "completed": True,
                "winner": engagement.attacking_fleets[0] if engagement.attacking_fleets else None,
                "experience_gained": 2.0
            }
        
        return {"completed": False}


class FormationManager:
    """Manages fleet formations and ship positioning."""
    
    def __init__(self, formation_templates: Dict[str, FormationTemplate]):
        self.formation_templates = formation_templates
    
    def update_formation(self, fleet: Fleet, formation_state: FleetFormationState, 
                        template: FormationTemplate, delta_seconds: float) -> None:
        """Update fleet formation positioning."""
        if not formation_state.is_formed:
            return
        
        # Simple formation maintenance
        formation_state.formation_integrity = min(1.0, 
            formation_state.formation_integrity + delta_seconds / 10.0)
        formation_state.formation_cohesion = min(1.0,
            formation_state.formation_cohesion + delta_seconds / 15.0)
        
        # Update formation center to fleet position
        formation_state.formation_center = fleet.position.copy()
        formation_state.last_formation_update = 0.0  # Would use current game time

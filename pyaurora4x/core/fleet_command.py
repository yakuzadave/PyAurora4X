"""
Fleet Command System for PyAurora 4X

Defines advanced fleet operations, orders, formations, combat mechanics,
and logistics for comprehensive fleet management and tactical gameplay.
"""

from typing import Dict, List, Optional, Any, Union, Tuple
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from pyaurora4x.core.enums import (
    OrderType, OrderPriority, OrderStatus, FleetFormation, FleetStatus,
    CombatRole, WeaponType, DefenseType, LogisticsType, TechnologyType
)
from pyaurora4x.core.models import Vector3D


class FleetOrder(BaseModel):
    """Represents a fleet order with parameters and execution details."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    fleet_id: str
    order_type: OrderType
    priority: OrderPriority = OrderPriority.NORMAL
    status: OrderStatus = OrderStatus.PENDING
    
    # Order parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)
    target_position: Optional[Vector3D] = None
    target_fleet_id: Optional[str] = None
    target_system_id: Optional[str] = None
    target_planet_id: Optional[str] = None
    
    # Execution details
    created_time: float = 0.0
    start_time: Optional[float] = None
    completion_time: Optional[float] = None
    estimated_duration: Optional[float] = None
    
    # Conditional execution
    preconditions: List[str] = Field(default_factory=list)
    postconditions: List[str] = Field(default_factory=list)
    
    # Order chain (for complex multi-step operations)
    parent_order_id: Optional[str] = None
    child_order_ids: List[str] = Field(default_factory=list)
    
    # Progress and status
    progress: float = 0.0  # 0.0 to 1.0
    status_message: str = ""
    failure_reason: Optional[str] = None
    
    # Repeating orders
    is_repeating: bool = False
    repeat_count: int = 0
    max_repeats: Optional[int] = None


class FormationTemplate(BaseModel):
    """Template defining a fleet formation with ship positions and roles."""
    
    id: str
    name: str
    formation_type: FleetFormation
    description: str
    
    # Formation parameters
    ship_positions: Dict[str, Vector3D] = Field(default_factory=dict)  # ship_role -> relative_position
    formation_spacing: float = 1000.0  # meters between ships
    formation_scale: float = 1.0  # scale factor for formation size
    
    # Role assignments
    role_requirements: Dict[CombatRole, int] = Field(default_factory=dict)  # role -> minimum_count
    optimal_ship_count: int = 6
    max_ship_count: int = 20
    min_ship_count: int = 3
    
    # Formation bonuses and penalties
    movement_speed_modifier: float = 1.0
    detection_modifier: float = 1.0
    combat_effectiveness_modifier: float = 1.0
    coordination_bonus: float = 0.0
    
    # Technology requirements
    tech_requirements: List[TechnologyType] = Field(default_factory=list)
    
    # Formation behavior
    maintain_formation: bool = True
    break_on_combat: bool = False
    reform_after_combat: bool = True


class ShipPositionData(BaseModel):
    """Tracks individual ship position within a formation."""
    
    ship_id: str
    assigned_role: CombatRole
    relative_position: Vector3D  # Position relative to formation center
    actual_position: Vector3D  # Current actual position
    target_position: Vector3D  # Where ship should be moving to
    
    # Status
    in_position: bool = False
    position_tolerance: float = 100.0  # meters
    last_position_update: float = 0.0


class FleetFormationState(BaseModel):
    """Current formation state for a fleet."""
    
    fleet_id: str
    formation_template_id: str
    
    # Formation state
    is_formed: bool = False
    formation_center: Vector3D = Field(default_factory=Vector3D)
    formation_heading: Vector3D = Field(default_factory=Vector3D)  # Formation facing direction
    formation_speed: float = 0.0
    
    # Ship positions
    ship_positions: Dict[str, ShipPositionData] = Field(default_factory=dict)
    
    # Formation integrity
    formation_integrity: float = 1.0  # 0.0 to 1.0, how well ships maintain positions
    formation_cohesion: float = 1.0  # How coordinated the formation movement is
    
    # Formation modifications
    current_spacing: float = 1000.0
    current_scale: float = 1.0
    
    # Status
    last_formation_update: float = 0.0
    formation_breaking: bool = False
    reformation_in_progress: bool = False


class WeaponSystem(BaseModel):
    """Represents a weapon system on a ship."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    weapon_type: WeaponType
    
    # Weapon characteristics
    damage: float = 10.0
    range: float = 10000.0  # meters
    accuracy: float = 0.8  # 0.0 to 1.0
    rate_of_fire: float = 1.0  # shots per second
    energy_cost: float = 5.0  # energy per shot
    
    # Ammunition (for missile weapons)
    ammunition_capacity: Optional[int] = None
    current_ammunition: Optional[int] = None
    
    # Status
    operational: bool = True
    condition: float = 100.0  # 0 to 100 percent
    overheated: bool = False
    
    # Targeting
    target_types: List[str] = Field(default_factory=list)  # Types of targets this weapon is effective against
    tracking_speed: float = 1.0  # How quickly weapon can track targets


class DefenseSystem(BaseModel):
    """Represents a defensive system on a ship."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    defense_type: DefenseType
    
    # Defense characteristics
    protection_value: float = 10.0
    coverage_angle: float = 360.0  # degrees
    regeneration_rate: float = 1.0  # points per second
    energy_cost: float = 2.0  # energy per second when active
    
    # Status
    operational: bool = True
    condition: float = 100.0
    current_strength: float = 100.0
    
    # Effectiveness
    effectiveness: Dict[WeaponType, float] = Field(default_factory=dict)  # weapon_type -> multiplier


class CombatCapabilities(BaseModel):
    """Represents the combat capabilities of a ship or fleet."""
    
    # Weapon systems
    weapons: List[WeaponSystem] = Field(default_factory=list)
    total_firepower: float = 0.0
    max_engagement_range: float = 0.0
    
    # Defensive systems
    defenses: List[DefenseSystem] = Field(default_factory=list)
    total_defense: float = 0.0
    shield_strength: float = 0.0
    armor_strength: float = 0.0
    
    # Combat statistics
    combat_rating: float = 0.0
    experience_level: float = 0.0  # 0.0 to 10.0
    morale: float = 100.0  # 0 to 100
    
    # Electronic warfare
    sensor_strength: float = 100.0
    ecm_strength: float = 0.0  # Electronic countermeasures
    eccm_strength: float = 0.0  # Electronic counter-countermeasures


class LogisticsRequirements(BaseModel):
    """Represents logistics requirements for a ship or fleet."""
    
    # Fuel requirements
    fuel_capacity: float = 1000.0
    fuel_consumption_rate: float = 1.0  # units per hour
    current_fuel: float = 1000.0
    
    # Supply requirements
    ammunition_requirements: Dict[str, int] = Field(default_factory=dict)
    spare_parts_requirements: Dict[str, int] = Field(default_factory=dict)
    crew_requirements: int = 100
    
    # Maintenance
    maintenance_interval: float = 720.0  # hours
    last_maintenance: float = 0.0
    maintenance_efficiency: float = 1.0  # 0.0 to 1.0
    
    # Supply status
    supply_status: Dict[LogisticsType, float] = Field(default_factory=dict)  # type -> percentage
    logistics_range: float = 0.0  # Maximum operational range from supply base


class CombatEngagement(BaseModel):
    """Represents an active combat engagement between fleets."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Participants
    attacking_fleets: List[str] = Field(default_factory=list)
    defending_fleets: List[str] = Field(default_factory=list)
    neutral_fleets: List[str] = Field(default_factory=list)  # Observers or non-combatants
    
    # Engagement parameters
    start_time: float = 0.0
    current_time: float = 0.0
    engagement_range: float = 10000.0  # meters
    battlefield_size: Vector3D = Field(default_factory=lambda: Vector3D(x=50000, y=50000, z=10000))
    
    # Combat state
    phase: str = "approach"  # approach, engagement, pursuit, disengagement
    intensity: float = 0.0  # 0.0 to 1.0
    casualties: Dict[str, int] = Field(default_factory=dict)  # fleet_id -> ships_lost
    
    # Environmental factors
    system_id: str
    environmental_modifiers: Dict[str, float] = Field(default_factory=dict)
    
    # Tactical situation
    initiative: Optional[str] = None  # Fleet ID with tactical initiative
    surprise_factor: float = 0.0  # -1.0 to 1.0
    tactical_advantage: Dict[str, float] = Field(default_factory=dict)  # fleet_id -> advantage


class FleetCommandState(BaseModel):
    """Enhanced state tracking for fleet command operations."""
    
    fleet_id: str
    
    # Command and control
    flagship_id: Optional[str] = None
    commanding_officer_id: Optional[str] = None
    command_effectiveness: float = 1.0
    communication_range: float = 100000.0  # meters
    
    # Orders and execution
    order_queue: List[str] = Field(default_factory=list)  # FleetOrder IDs in priority order
    current_orders: Dict[str, FleetOrder] = Field(default_factory=dict)
    completed_orders: List[str] = Field(default_factory=list)
    
    # Formation state
    formation_state: Optional[FleetFormationState] = None
    formation_templates: Dict[str, FormationTemplate] = Field(default_factory=dict)
    
    # Combat capabilities
    combat_capabilities: CombatCapabilities = Field(default_factory=CombatCapabilities)
    current_engagement: Optional[str] = None  # CombatEngagement ID
    
    # Logistics state
    logistics_requirements: LogisticsRequirements = Field(default_factory=LogisticsRequirements)
    supply_lines: List[str] = Field(default_factory=list)  # Fleet/Colony IDs providing supply
    
    # Tactical information
    known_contacts: Dict[str, Dict[str, Any]] = Field(default_factory=dict)  # contact_id -> data
    threat_assessment: Dict[str, float] = Field(default_factory=dict)  # fleet_id -> threat_level
    
    # Performance metrics
    mission_success_rate: float = 0.0
    total_missions: int = 0
    combat_experience: float = 0.0
    
    # Status tracking
    last_command_update: float = 0.0
    automation_level: float = 0.0  # 0.0 = manual, 1.0 = fully automated
    standing_orders: List[OrderType] = Field(default_factory=list)


def get_default_formation_templates() -> Dict[str, FormationTemplate]:
    """Returns default fleet formation templates."""
    
    templates = {}
    
    # Line Ahead Formation
    templates["line_ahead"] = FormationTemplate(
        id="line_ahead",
        name="Line Ahead",
        formation_type=FleetFormation.LINE_AHEAD,
        description="Ships arranged in a single column, maximizing forward firepower",
        ship_positions={
            "flagship": Vector3D(x=0, y=0, z=0),
            "escort_1": Vector3D(x=0, y=-1500, z=0),
            "escort_2": Vector3D(x=0, y=1500, z=0),
            "support_1": Vector3D(x=0, y=-3000, z=0),
            "support_2": Vector3D(x=0, y=3000, z=0),
        },
        formation_spacing=1500.0,
        role_requirements={
            CombatRole.FLAGSHIP: 1,
            CombatRole.CRUISER: 2,
            CombatRole.DESTROYER: 2,
        },
        optimal_ship_count=5,
        movement_speed_modifier=1.1,
        combat_effectiveness_modifier=1.2,
    )
    
    # Battle Line Formation
    templates["battle_line"] = FormationTemplate(
        id="battle_line",
        name="Battle Line",
        formation_type=FleetFormation.BATTLE_LINE,
        description="Traditional naval battle line for maximum broadside firepower",
        ship_positions={
            "flagship": Vector3D(x=0, y=0, z=0),
            "battleship_1": Vector3D(x=-2000, y=0, z=0),
            "battleship_2": Vector3D(x=2000, y=0, z=0),
            "cruiser_1": Vector3D(x=-4000, y=0, z=0),
            "cruiser_2": Vector3D(x=4000, y=0, z=0),
            "destroyer_1": Vector3D(x=-1000, y=-1500, z=0),
            "destroyer_2": Vector3D(x=1000, y=-1500, z=0),
        },
        formation_spacing=2000.0,
        role_requirements={
            CombatRole.FLAGSHIP: 1,
            CombatRole.BATTLESHIP: 2,
            CombatRole.CRUISER: 2,
            CombatRole.DESTROYER: 2,
        },
        optimal_ship_count=7,
        movement_speed_modifier=0.8,
        combat_effectiveness_modifier=1.5,
        coordination_bonus=0.2,
    )
    
    # Screening Formation
    templates["screening_formation"] = FormationTemplate(
        id="screening_formation",
        name="Screening Formation",
        formation_type=FleetFormation.SCREENING_FORMATION,
        description="Fast ships providing advance warning and protection",
        ship_positions={
            "flagship": Vector3D(x=0, y=0, z=0),
            "destroyer_1": Vector3D(x=0, y=3000, z=0),
            "destroyer_2": Vector3D(x=-2500, y=1500, z=0),
            "destroyer_3": Vector3D(x=2500, y=1500, z=0),
            "frigate_1": Vector3D(x=-4000, y=3000, z=0),
            "frigate_2": Vector3D(x=4000, y=3000, z=0),
        },
        formation_spacing=2500.0,
        role_requirements={
            CombatRole.FLAGSHIP: 1,
            CombatRole.DESTROYER: 3,
            CombatRole.FRIGATE: 2,
        },
        optimal_ship_count=6,
        movement_speed_modifier=1.3,
        detection_modifier=1.4,
        combat_effectiveness_modifier=0.9,
    )
    
    # Box Formation
    templates["box_formation"] = FormationTemplate(
        id="box_formation",
        name="Box Formation",
        formation_type=FleetFormation.BOX_FORMATION,
        description="Defensive box formation providing all-around protection",
        ship_positions={
            "flagship": Vector3D(x=0, y=0, z=0),
            "guardian_1": Vector3D(x=-2000, y=-2000, z=0),
            "guardian_2": Vector3D(x=2000, y=-2000, z=0),
            "guardian_3": Vector3D(x=-2000, y=2000, z=0),
            "guardian_4": Vector3D(x=2000, y=2000, z=0),
            "support_1": Vector3D(x=0, y=-2000, z=0),
            "support_2": Vector3D(x=0, y=2000, z=0),
            "support_3": Vector3D(x=-2000, y=0, z=0),
            "support_4": Vector3D(x=2000, y=0, z=0),
        },
        formation_spacing=2000.0,
        role_requirements={
            CombatRole.FLAGSHIP: 1,
            CombatRole.CRUISER: 4,
            CombatRole.DESTROYER: 4,
        },
        optimal_ship_count=9,
        movement_speed_modifier=0.7,
        combat_effectiveness_modifier=1.1,
        coordination_bonus=0.3,
        maintain_formation=True,
    )
    
    # Escort Formation  
    templates["escort_formation"] = FormationTemplate(
        id="escort_formation",
        name="Escort Formation",
        formation_type=FleetFormation.ESCORT_FORMATION,
        description="Specialized formation for protecting valuable assets",
        ship_positions={
            "protected_asset": Vector3D(x=0, y=0, z=0),
            "escort_1": Vector3D(x=0, y=1500, z=0),
            "escort_2": Vector3D(x=-1300, y=-750, z=0),
            "escort_3": Vector3D(x=1300, y=-750, z=0),
            "picket_1": Vector3D(x=0, y=3000, z=0),
            "picket_2": Vector3D(x=-2600, y=-1500, z=0),
            "picket_3": Vector3D(x=2600, y=-1500, z=0),
        },
        formation_spacing=1500.0,
        role_requirements={
            CombatRole.LOGISTICS: 1,  # The protected asset
            CombatRole.DESTROYER: 3,
            CombatRole.FRIGATE: 3,
        },
        optimal_ship_count=7,
        movement_speed_modifier=0.9,
        combat_effectiveness_modifier=1.0,
        coordination_bonus=0.1,
        maintain_formation=True,
        break_on_combat=False,
    )
    
    return templates

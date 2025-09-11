"""
Enumerations and constants for PyAurora 4X

Defines the various types and statuses used throughout the game.
"""

from enum import Enum


class PlanetType(Enum):
    """Types of planets in star systems."""
    TERRESTRIAL = "terrestrial"
    GAS_GIANT = "gas_giant"
    ICE_GIANT = "ice_giant"
    ASTEROID = "asteroid"
    DWARF_PLANET = "dwarf_planet"


class StarType(Enum):
    """Stellar classification types."""
    M_DWARF = "M"      # Red dwarf
    K_DWARF = "K"      # Orange dwarf
    G_DWARF = "G"      # Yellow dwarf (like our Sun)
    F_DWARF = "F"      # Yellow-white dwarf
    A_STAR = "A"       # White star
    B_STAR = "B"       # Blue-white star
    O_STAR = "O"       # Blue star
    WHITE_DWARF = "WD" # White dwarf
    NEUTRON_STAR = "NS" # Neutron star
    BLACK_HOLE = "BH"  # Black hole


class FleetStatus(Enum):
    """Status of fleets and their current activities."""
    IDLE = "idle"
    MOVING = "moving"
    IN_TRANSIT = "in_transit"
    ORBITING = "orbiting"
    SURVEYING = "surveying"
    MINING = "mining"
    EXPLORING = "exploring"
    IN_COMBAT = "in_combat"
    REPAIRING = "repairing"
    REFUELING = "refueling"
    LOADING = "loading"
    UNLOADING = "unloading"
    FORMING_UP = "forming_up"
    IN_FORMATION = "in_formation"
    INTERCEPTING = "intercepting"
    RETREATING = "retreating"
    PATROLLING = "patrolling"
    BLOCKADING = "blockading"
    ESCORTING = "escorting"
    RESUPPLYING = "resupplying"


class TechnologyType(Enum):
    """Categories of technologies for research."""
    PROPULSION = "propulsion"
    ENERGY = "energy"
    WEAPONS = "weapons"
    SHIELDS = "shields"
    SENSORS = "sensors"
    CONSTRUCTION = "construction"
    BIOLOGY = "biology"
    PHYSICS = "physics"
    ENGINEERING = "engineering"
    LOGISTICS = "logistics"
    COMPUTING = "computing"
    MATERIALS = "materials"


class ShipType(Enum):
    """Classifications of ship types."""
    FIGHTER = "fighter"
    CORVETTE = "corvette"
    FRIGATE = "frigate"
    DESTROYER = "destroyer"
    CRUISER = "cruiser"
    BATTLECRUISER = "battlecruiser"
    BATTLESHIP = "battleship"
    DREADNOUGHT = "dreadnought"
    CARRIER = "carrier"
    TRANSPORT = "transport"
    FREIGHTER = "freighter"
    MINING_SHIP = "mining_ship"
    SURVEY_SHIP = "survey_ship"
    COLONY_SHIP = "colony_ship"
    CONSTRUCTION_SHIP = "construction_ship"
    TANKER = "tanker"
    REPAIR_SHIP = "repair_ship"


class ShipRole(Enum):
    """Functional role of a ship within a fleet."""

    COMMAND = "command"
    ASSAULT = "assault"
    SUPPORT = "support"
    SCOUT = "scout"
    TRANSPORT = "transport"
    SURVEY = "survey"
    MINER = "miner"


class OfficerRank(Enum):
    """Ranks for naval officers."""

    CAPTAIN = "captain"
    COMMANDER = "commander"
    COMMODORE = "commodore"
    ADMIRAL = "admiral"


class ComponentType(Enum):
    """Types of ship components."""
    ENGINE = "engine"
    FUEL_TANK = "fuel_tank"
    CREW_QUARTERS = "crew_quarters"
    BRIDGE = "bridge"
    SENSOR = "sensor"
    WEAPON = "weapon"
    SHIELD = "shield"
    ARMOR = "armor"
    POWER_PLANT = "power_plant"
    CARGO_BAY = "cargo_bay"
    MINING_EQUIPMENT = "mining_equipment"
    JUMP_DRIVE = "jump_drive"
    LIFE_SUPPORT = "life_support"
    COMPUTER = "computer"


class OrderType(Enum):
    """Types of orders that can be given to fleets/ships."""
    # Movement orders
    MOVE_TO = "move_to"
    ORBIT = "orbit"
    JUMP = "jump"
    HOLD_POSITION = "hold_position"
    FOLLOW = "follow"
    INTERCEPT = "intercept"
    RETREAT = "retreat"
    
    # Exploration and survey orders
    EXPLORE = "explore"
    SURVEY = "survey"
    PATROL = "patrol"
    SCOUT = "scout"
    
    # Combat orders
    ATTACK = "attack"
    DEFEND = "defend"
    ESCORT = "escort"
    BLOCKADE = "blockade"
    BOMBARDMENT = "bombardment"
    
    # Logistics and support
    TRANSPORT = "transport"
    REFUEL = "refuel"
    REPAIR = "repair"
    RESUPPLY = "resupply"
    MINE = "mine"
    
    # Special operations
    COLONIZE = "colonize"
    RAID = "raid"
    RECONNAISSANCE = "reconnaissance"
    SEARCH_AND_RESCUE = "search_and_rescue"
    
    # Formation orders
    FORM_UP = "form_up"
    CHANGE_FORMATION = "change_formation"
    MAINTAIN_FORMATION = "maintain_formation"


class DiplomaticRelation(Enum):
    """Diplomatic relations between empires."""
    WAR = "war"
    HOSTILE = "hostile"
    UNFRIENDLY = "unfriendly"
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    ALLIED = "allied"
    VASSAL = "vassal"
    OVERLORD = "overlord"


class ResourceType(Enum):
    """Types of resources in the game."""
    # Basic resources
    MINERALS = "minerals"
    ENERGY = "energy"
    RESEARCH = "research"
    FOOD = "food"
    
    # Advanced materials
    RARE_METALS = "rare_metals"
    CRYSTALS = "crystals"
    EXOTIC_MATTER = "exotic_matter"
    
    # Manufactured goods
    ALLOYS = "alloys"
    COMPONENTS = "components"
    FUEL = "fuel"
    
    # Population resources
    POPULATION = "population"
    INFRASTRUCTURE = "infrastructure"


class VictoryCondition(Enum):
    """Possible victory conditions for the game."""
    CONQUEST = "conquest"           # Control all systems
    RESEARCH = "research"           # Complete all tech trees
    ECONOMIC = "economic"          # Achieve economic dominance
    DIPLOMATIC = "diplomatic"      # Unite all empires peacefully
    EXPLORATION = "exploration"    # Explore entire galaxy
    CUSTOM = "custom"              # Custom win conditions


class BuildingType(Enum):
    """Types of colonial buildings and infrastructure."""
    
    # Mining and resource extraction
    MINE = "mine"
    AUTOMATED_MINE = "automated_mine"
    DEEP_CORE_MINE = "deep_core_mine"
    
    # Manufacturing and production
    FACTORY = "factory"
    AUTOMATED_FACTORY = "automated_factory"
    NANO_FACTORY = "nano_factory"
    
    # Research facilities
    RESEARCH_LAB = "research_lab"
    ADVANCED_LAB = "advanced_lab"
    THEORETICAL_PHYSICS_LAB = "theoretical_physics_lab"
    
    # Population support
    HABITAT = "habitat"
    LIFE_SUPPORT = "life_support"
    RECREATION_CENTER = "recreation_center"
    
    # Military and defense
    DEFENSE_STATION = "defense_station"
    MISSILE_BASE = "missile_base"
    SHIELD_GENERATOR = "shield_generator"
    
    # Infrastructure
    POWER_PLANT = "power_plant"
    FUSION_PLANT = "fusion_plant"
    SPACEPORT = "spaceport"
    ORBITAL_SHIPYARD = "orbital_shipyard"
    
    # Specialized facilities
    SENSOR_ARRAY = "sensor_array"
    COMMUNICATION_HUB = "communication_hub"
    TERRAFORM_PROCESSOR = "terraform_processor"


class ConstructionStatus(Enum):
    """Status of construction projects."""
    
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class FleetFormation(Enum):
    """Fleet formation types for tactical arrangements."""
    
    # Basic formations
    LINE_AHEAD = "line_ahead"
    LINE_ABREAST = "line_abreast"
    COLUMN = "column"
    WEDGE = "wedge"
    
    # Tactical formations
    BATTLE_LINE = "battle_line"
    SCREENING_FORMATION = "screening_formation"
    BOX_FORMATION = "box_formation"
    DIAMOND_FORMATION = "diamond_formation"
    
    # Specialized formations
    ESCORT_FORMATION = "escort_formation"
    CONVOY_FORMATION = "convoy_formation"
    PATROL_FORMATION = "patrol_formation"
    SEARCH_FORMATION = "search_formation"
    
    # Defensive formations
    DEFENSIVE_CIRCLE = "defensive_circle"
    FORTRESS_FORMATION = "fortress_formation"
    
    # Custom formation
    CUSTOM = "custom"


class OrderPriority(Enum):
    """Priority levels for fleet orders."""
    
    EMERGENCY = "emergency"      # Highest priority, interrupt current operations
    HIGH = "high"                # High priority, complete after current critical task
    NORMAL = "normal"            # Normal priority, queue normally
    LOW = "low"                  # Low priority, execute when nothing else to do
    BACKGROUND = "background"    # Lowest priority, continuous/maintenance tasks


class OrderStatus(Enum):
    """Status of individual fleet orders."""
    
    PENDING = "pending"          # Order received, not yet started
    ACTIVE = "active"            # Order currently being executed
    PAUSED = "paused"            # Order execution temporarily halted
    COMPLETED = "completed"      # Order successfully completed
    FAILED = "failed"            # Order failed to execute
    CANCELLED = "cancelled"      # Order cancelled before completion
    SUSPENDED = "suspended"      # Order suspended due to conditions


class CombatRole(Enum):
    """Combat roles for ships in tactical engagements."""
    
    FLAGSHIP = "flagship"        # Fleet command ship
    BATTLESHIP = "battleship"    # Heavy combat vessel
    CRUISER = "cruiser"          # Medium combat vessel
    DESTROYER = "destroyer"      # Fast attack vessel
    FRIGATE = "frigate"          # Light combat/escort vessel
    CORVETTE = "corvette"        # Light patrol vessel
    FIGHTER = "fighter"          # Small interceptor
    BOMBER = "bomber"            # Strike aircraft
    SUPPORT = "support"          # Non-combat support
    LOGISTICS = "logistics"      # Supply and transport
    ELECTRONIC_WARFARE = "electronic_warfare"  # ECM/ECCM specialist
    RECONNAISSANCE = "reconnaissance"  # Scout and intelligence


class WeaponType(Enum):
    """Types of weapons for combat calculations."""
    
    # Energy weapons
    LASER = "laser"
    PLASMA = "plasma"
    PARTICLE_BEAM = "particle_beam"
    ION_CANNON = "ion_cannon"
    
    # Projectile weapons
    RAILGUN = "railgun"
    MASS_DRIVER = "mass_driver"
    AUTOCANNON = "autocannon"
    GAUSS_RIFLE = "gauss_rifle"
    
    # Missile weapons
    MISSILE = "missile"
    TORPEDO = "torpedo"
    GUIDED_PROJECTILE = "guided_projectile"
    
    # Special weapons
    ANTIMATTER = "antimatter"
    GRAVITY_WEAPON = "gravity_weapon"
    SUBSPACE_DISRUPTOR = "subspace_disruptor"


class DefenseType(Enum):
    """Types of defensive systems."""
    
    # Passive defenses
    ARMOR = "armor"
    REACTIVE_ARMOR = "reactive_armor"
    ABLATIVE_ARMOR = "ablative_armor"
    
    # Energy shields
    DEFLECTOR_SHIELD = "deflector_shield"
    ENERGY_BARRIER = "energy_barrier"
    KINETIC_BARRIER = "kinetic_barrier"
    
    # Active defenses
    POINT_DEFENSE = "point_defense"
    COUNTERMEASURES = "countermeasures"
    ELECTRONIC_COUNTERMEASURES = "electronic_countermeasures"


class LogisticsType(Enum):
    """Types of logistics operations."""
    
    FUEL_SUPPLY = "fuel_supply"
    AMMUNITION_SUPPLY = "ammunition_supply"
    SPARE_PARTS = "spare_parts"
    FOOD_AND_SUPPLIES = "food_and_supplies"
    MEDICAL_SUPPLIES = "medical_supplies"
    REPAIR_MATERIALS = "repair_materials"
    PERSONNEL_TRANSFER = "personnel_transfer"
    INTELLIGENCE_DATA = "intelligence_data"


class JumpPointType(Enum):
    """Types of jump points for interstellar travel."""
    
    NATURAL = "natural"          # Naturally occurring jump point
    ARTIFICIAL = "artificial"    # Constructed jump gate
    UNSTABLE = "unstable"        # Temporary or unreliable connection
    DORMANT = "dormant"          # Inactive jump point requiring activation
    RESTRICTED = "restricted"    # Access limited by technology or politics


class JumpPointStatus(Enum):
    """Discovery and exploration status of jump points."""
    
    UNKNOWN = "unknown"          # Not yet discovered
    DETECTED = "detected"        # Detected but not surveyed
    SURVEYED = "surveyed"        # Basic survey completed
    MAPPED = "mapped"            # Fully mapped and charted
    ACTIVE = "active"            # Ready for travel
    INACTIVE = "inactive"        # Temporarily unusable
    DESTROYED = "destroyed"      # Permanently disabled


class ExplorationResult(Enum):
    """Results of exploration and survey missions."""
    
    NO_DISCOVERY = "no_discovery"
    WEAK_SIGNAL = "weak_signal"
    JUMP_POINT_DETECTED = "jump_point_detected"
    JUMP_POINT_SURVEYED = "jump_point_surveyed"
    SYSTEM_MAPPED = "system_mapped"
    ANOMALY_DETECTED = "anomaly_detected"
    HOSTILE_CONTACT = "hostile_contact"


class GameDifficulty(Enum):
    """Game difficulty levels."""
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    NIGHTMARE = "nightmare"


class TimeScale(Enum):
    """Time acceleration scales."""
    PAUSED = 0
    REAL_TIME = 1
    FAST = 5
    FASTER = 30
    FASTEST = 300
    EXTREME = 3600


# Game constants
CONSTANTS = {
    "LIGHT_SPEED": 299792458,  # m/s
    "AU_TO_KM": 149597870.7,   # km per AU
    "EARTH_MASS": 5.972e24,    # kg
    "EARTH_RADIUS": 6371,      # km
    "SOLAR_MASS": 1.989e30,    # kg
    "SOLAR_RADIUS": 695700,    # km
    "SECONDS_PER_YEAR": 365.25 * 24 * 3600,
    "DEFAULT_CREW_SIZE": 100,
    "DEFAULT_FUEL_CAPACITY": 1000,
    "DEFAULT_CARGO_CAPACITY": 500,
    
    # Jump point and exploration constants
    "JUMP_FUEL_COST_BASE": 100,      # Base fuel cost for jump
    "JUMP_FUEL_COST_PER_SHIP": 10,   # Additional fuel per ship
    "JUMP_TIME_BASE": 30,            # Base time for jump in seconds
    "EXPLORATION_BASE_TIME": 300,    # Base time for exploration in seconds
    "SURVEY_BASE_TIME": 600,         # Base time for survey in seconds
    "JUMP_POINT_DETECTION_RANGE": 2.0,  # AU range for jump point detection
    "EXPLORATION_SUCCESS_BASE": 0.3, # Base chance for exploration success
}

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
    MOVE_TO = "move_to"
    ORBIT = "orbit"
    SURVEY = "survey"
    MINE = "mine"
    EXPLORE = "explore"
    ATTACK = "attack"
    DEFEND = "defend"
    PATROL = "patrol"
    ESCORT = "escort"
    TRANSPORT = "transport"
    COLONIZE = "colonize"
    REFUEL = "refuel"
    REPAIR = "repair"
    JUMP = "jump"
    FOLLOW = "follow"
    HOLD_POSITION = "hold_position"


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
}

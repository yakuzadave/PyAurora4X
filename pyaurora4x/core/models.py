"""
Core data models for PyAurora 4X

Defines the main game entities using Pydantic for validation and serialization.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from pyaurora4x.core.enums import (
    PlanetType,
    StarType,
    FleetStatus,
    TechnologyType,
    ShipType,
)


class Vector3D(BaseModel):
    """3D vector for positions and velocities."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def copy(self) -> "Vector3D":
        """Create a copy of this vector."""
        return Vector3D(x=self.x, y=self.y, z=self.z)

    def magnitude(self) -> float:
        """Calculate the magnitude of the vector."""
        return (self.x**2 + self.y**2 + self.z**2) ** 0.5

    def normalize(self) -> "Vector3D":
        """Return a normalized version of this vector."""
        mag = self.magnitude()
        if mag == 0:
            return Vector3D()
        return Vector3D(x=self.x / mag, y=self.y / mag, z=self.z / mag)


class Technology(BaseModel):
    """Represents a technology that can be researched."""

    id: str
    name: str
    description: str
    tech_type: TechnologyType
    research_cost: int
    prerequisites: List[str] = Field(default_factory=list)
    unlocks: List[str] = Field(default_factory=list)
    is_researched: bool = False


class ShipComponent(BaseModel):
    """Represents a ship component/module."""

    id: str
    name: str
    component_type: str
    mass: float
    cost: int
    power_requirement: float
    crew_requirement: int
    tech_requirements: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)


class ShipDesign(BaseModel):
    """Represents a ship design template."""

    id: str
    name: str
    ship_type: ShipType
    components: List[str] = Field(default_factory=list)
    total_mass: float = 0.0
    total_cost: int = 0
    crew_requirement: int = 0
    is_obsolete: bool = False


class Ship(BaseModel):
    """Represents an individual ship."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    design_id: str
    fleet_id: Optional[str] = None
    empire_id: str

    # Current status
    current_mass: float = 0.0
    current_crew: int = 0
    fuel: float = 100.0
    condition: float = 100.0  # Ship condition percentage

    # Combat stats
    shields: float = 0.0
    armor: float = 0.0
    structure: float = 100.0

    # Orders and AI
    current_orders: List[str] = Field(default_factory=list)
    automation_enabled: bool = False


class Fleet(BaseModel):
    """Represents a fleet of ships."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    empire_id: str

    # Location and movement
    system_id: str
    position: Vector3D
    velocity: Vector3D = Field(default_factory=Vector3D)

    # Fleet composition
    ships: List[str] = Field(default_factory=list)  # Ship IDs

    # Status and orders
    status: FleetStatus = FleetStatus.IDLE
    current_orders: List[str] = Field(default_factory=list)
    destination: Optional[Vector3D] = None
    estimated_arrival: Optional[float] = None

    # Fleet capabilities
    total_mass: float = 0.0
    max_speed: float = 0.0
    fuel_remaining: float = 100.0


class Colony(BaseModel):
    """Represents a planetary colony."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    empire_id: str
    planet_id: str

    # Population and infrastructure
    population: int = 1000
    infrastructure: Dict[str, int] = Field(default_factory=dict)

    # Resources and production
    stockpiles: Dict[str, float] = Field(default_factory=dict)
    production: Dict[str, float] = Field(default_factory=dict)

    # Colony status
    established_date: float = 0.0
    happiness: float = 50.0
    growth_rate: float = 1.0


class Planet(BaseModel):
    """Represents a planet in a star system."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    planet_type: PlanetType

    # Physical properties
    mass: float  # Earth masses
    radius: float  # Earth radii
    surface_temperature: float  # Kelvin
    gravity: float = 1.0  # Earth gravities

    # Orbital parameters
    orbital_distance: float  # AU
    orbital_period: float  # Earth years
    eccentricity: float = 0.0
    inclination: float = 0.0  # degrees
    longitude_of_ascending_node: float = 0.0  # degrees
    argument_of_periapsis: float = 0.0  # degrees
    mean_anomaly: float = 0.0  # degrees

    # Current position and velocity
    position: Vector3D
    velocity: Vector3D = Field(default_factory=Vector3D)

    # Atmospheric and surface conditions
    atmosphere_composition: Dict[str, float] = Field(default_factory=dict)
    has_atmosphere: bool = True
    atmospheric_pressure: float = 1.0  # Earth atmospheres

    # Resources and habitability
    mineral_resources: Dict[str, float] = Field(default_factory=dict)
    habitability: float = 0.0  # 0-100 scale

    # Colonization
    colony_id: Optional[str] = None
    is_surveyed: bool = False
    survey_data: Dict[str, Any] = Field(default_factory=dict)


class AsteroidBelt(BaseModel):
    """Represents an asteroid belt in a star system."""

    distance: float  # AU from the star (center of belt)
    width: float  # AU width of the belt


class JumpPoint(BaseModel):
    """Connection between two star systems for FTL travel."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    position: Vector3D
    connects_to: str  # target star system id


class StarSystem(BaseModel):
    """Represents a complete star system."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str

    # Star properties
    star_type: StarType
    star_mass: float  # Solar masses
    star_luminosity: float  # Solar luminosities
    star_temperature: float = 5778.0  # Kelvin

    # System composition
    planets: List[Planet] = Field(default_factory=list)
    asteroid_belts: List[AsteroidBelt] = Field(default_factory=list)

    # Navigation and zones
    habitable_zone_inner: float = 0.95  # AU
    habitable_zone_outer: float = 1.37  # AU
    jump_points: List[JumpPoint] = Field(default_factory=list)

    # Exploration status
    is_explored: bool = False
    discovered_by: Optional[str] = None
    discovery_date: Optional[float] = None


class Empire(BaseModel):
    """Represents a player or AI empire."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    is_player: bool = False

    # Empire location and territory
    home_system_id: str
    home_planet_id: str
    controlled_systems: List[str] = Field(default_factory=list)

    # Empire assets
    fleets: List[str] = Field(default_factory=list)  # Fleet IDs
    colonies: List[str] = Field(default_factory=list)  # Colony IDs
    ship_designs: List[str] = Field(default_factory=list)  # Ship design IDs

    # Technology and research
    technologies: Dict[str, Technology] = Field(default_factory=dict)
    current_research: Optional[str] = None
    research_points: float = 0.0
    research_allocation: Dict[TechnologyType, float] = Field(default_factory=dict)

    # Resources and economy
    resources: Dict[str, float] = Field(default_factory=dict)
    income: Dict[str, float] = Field(default_factory=dict)

    # Diplomacy
    diplomatic_relations: Dict[str, str] = Field(
        default_factory=dict
    )  # empire_id -> relation

    # Empire characteristics
    government_type: str = "Democracy"
    culture: str = "Human"
    established_date: float = 0.0

    # AI settings (for non-player empires)
    ai_personality: str = "Balanced"
    ai_aggression: float = 0.5
    ai_expansion: float = 0.5
    ai_research_focus: List[TechnologyType] = Field(default_factory=list)


class GameState(BaseModel):
    """Represents the complete game state for saving/loading."""

    version: str = "0.1.0"
    created_date: datetime = Field(default_factory=datetime.now)
    last_saved: datetime = Field(default_factory=datetime.now)

    # Core game data
    current_time: float = 0.0
    game_start_time: datetime = Field(default_factory=datetime.now)

    # Game objects
    empires: Dict[str, Empire] = Field(default_factory=dict)
    star_systems: Dict[str, StarSystem] = Field(default_factory=dict)
    fleets: Dict[str, Fleet] = Field(default_factory=dict)
    ships: Dict[str, Ship] = Field(default_factory=dict)
    colonies: Dict[str, Colony] = Field(default_factory=dict)

    # Game settings
    time_acceleration: float = 1.0
    difficulty: str = "Normal"
    victory_conditions: List[str] = Field(default_factory=list)

    # Metadata
    player_empire_id: Optional[str] = None
    turn_number: int = 0
    total_playtime: float = 0.0  # seconds

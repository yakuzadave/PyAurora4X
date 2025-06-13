"""
Unit tests for PyAurora 4X core models

Tests the data models, validation, and serialization.
"""


from pyaurora4x.core.models import (
    Vector3D, Empire, Fleet, Ship, Colony, StarSystem, Planet, Technology
)
from pyaurora4x.core.enums import (
    PlanetType, StarType, FleetStatus, TechnologyType
)


class TestVector3D:
    """Test the Vector3D model."""
    
    def test_vector_creation(self):
        """Test vector creation."""
        v = Vector3D(x=1.0, y=2.0, z=3.0)
        assert v.x == 1.0
        assert v.y == 2.0
        assert v.z == 3.0
    
    def test_vector_magnitude(self):
        """Test magnitude calculation."""
        v = Vector3D(x=3.0, y=4.0, z=0.0)
        assert v.magnitude() == 5.0
    
    def test_vector_normalize(self):
        """Test vector normalization."""
        v = Vector3D(x=3.0, y=4.0, z=0.0)
        normalized = v.normalize()
        assert abs(normalized.magnitude() - 1.0) < 1e-10
        assert normalized.x == 0.6
        assert normalized.y == 0.8
        assert normalized.z == 0.0
    
    def test_vector_copy(self):
        """Test vector copying."""
        v1 = Vector3D(x=1.0, y=2.0, z=3.0)
        v2 = v1.copy()
        assert v2.x == v1.x
        assert v2.y == v1.y
        assert v2.z == v1.z
        assert v2 is not v1


class TestTechnology:
    """Test the Technology model."""
    
    def test_technology_creation(self):
        """Test technology creation."""
        tech = Technology(
            id="test_tech",
            name="Test Technology",
            description="A test technology",
            tech_type=TechnologyType.PROPULSION,
            research_cost=100,
            prerequisites=["basic_tech"],
            unlocks=["advanced_tech"],
            is_researched=False
        )
        
        assert tech.id == "test_tech"
        assert tech.name == "Test Technology"
        assert tech.tech_type == TechnologyType.PROPULSION
        assert tech.research_cost == 100
        assert "basic_tech" in tech.prerequisites
        assert "advanced_tech" in tech.unlocks
        assert not tech.is_researched
    
    def test_technology_serialization(self):
        """Test technology serialization."""
        tech = Technology(
            id="test_tech",
            name="Test Technology",
            description="A test technology",
            tech_type=TechnologyType.PROPULSION,
            research_cost=100
        )
        
        data = tech.dict()
        assert data["id"] == "test_tech"
        assert data["name"] == "Test Technology"
        assert data["research_cost"] == 100


class TestPlanet:
    """Test the Planet model."""
    
    def test_planet_creation(self):
        """Test planet creation."""
        position = Vector3D(x=149597870.7, y=0.0, z=0.0)  # 1 AU
        
        planet = Planet(
            id="test_planet",
            name="Test Planet",
            planet_type=PlanetType.TERRESTRIAL,
            mass=1.0,
            radius=1.0,
            surface_temperature=288.0,
            orbital_distance=1.0,
            orbital_period=1.0,
            position=position
        )
        
        assert planet.id == "test_planet"
        assert planet.planet_type == PlanetType.TERRESTRIAL
        assert planet.mass == 1.0
        assert planet.position.x == 149597870.7
    
    def test_planet_defaults(self):
        """Test planet default values."""
        position = Vector3D()
        planet = Planet(
            name="Test Planet",
            planet_type=PlanetType.TERRESTRIAL,
            mass=1.0,
            radius=1.0,
            surface_temperature=288.0,
            orbital_distance=1.0,
            orbital_period=1.0,
            position=position
        )
        
        assert planet.eccentricity == 0.0
        assert planet.inclination == 0.0
        assert planet.gravity == 1.0
        assert not planet.is_surveyed


class TestStarSystem:
    """Test the StarSystem model."""
    
    def test_star_system_creation(self):
        """Test star system creation."""
        planet1 = Planet(
            name="Planet I",
            planet_type=PlanetType.TERRESTRIAL,
            mass=1.0,
            radius=1.0,
            surface_temperature=288.0,
            orbital_distance=1.0,
            orbital_period=1.0,
            position=Vector3D()
        )
        
        system = StarSystem(
            id="test_system",
            name="Test System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0,
            planets=[planet1]
        )
        
        assert system.id == "test_system"
        assert system.star_type == StarType.G_DWARF
        assert len(system.planets) == 1
        assert system.planets[0].name == "Planet I"
    
    def test_star_system_defaults(self):
        """Test star system default values."""
        system = StarSystem(
            name="Test System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0
        )
        
        assert system.star_temperature == 5778.0
        assert system.habitable_zone_inner == 0.95
        assert system.habitable_zone_outer == 1.37
        assert not system.is_explored
        assert len(system.planets) == 0


class TestFleet:
    """Test the Fleet model."""
    
    def test_fleet_creation(self):
        """Test fleet creation."""
        position = Vector3D(x=1000.0, y=2000.0, z=3000.0)
        
        fleet = Fleet(
            id="test_fleet",
            name="Test Fleet",
            empire_id="test_empire",
            system_id="test_system",
            position=position
        )
        
        assert fleet.id == "test_fleet"
        assert fleet.empire_id == "test_empire"
        assert fleet.position.x == 1000.0
        assert fleet.status == FleetStatus.IDLE
    
    def test_fleet_defaults(self):
        """Test fleet default values."""
        fleet = Fleet(
            name="Test Fleet",
            empire_id="test_empire",
            system_id="test_system",
            position=Vector3D()
        )
        
        assert len(fleet.ships) == 0
        assert len(fleet.current_orders) == 0
        assert fleet.total_mass == 0.0
        assert fleet.max_speed == 0.0
        assert fleet.fuel_remaining == 100.0


class TestEmpire:
    """Test the Empire model."""
    
    def test_empire_creation(self):
        """Test empire creation."""
        empire = Empire(
            id="test_empire",
            name="Test Empire",
            is_player=True,
            home_system_id="home_system",
            home_planet_id="home_planet"
        )
        
        assert empire.id == "test_empire"
        assert empire.name == "Test Empire"
        assert empire.is_player
        assert empire.home_system_id == "home_system"
    
    def test_empire_defaults(self):
        """Test empire default values."""
        empire = Empire(
            name="Test Empire",
            home_system_id="home_system",
            home_planet_id="home_planet"
        )
        
        assert not empire.is_player
        assert len(empire.fleets) == 0
        assert len(empire.colonies) == 0
        assert empire.research_points == 0.0
        assert empire.government_type == "Democracy"
        assert empire.culture == "Human"
    
    def test_empire_serialization(self):
        """Test empire serialization."""
        empire = Empire(
            name="Test Empire",
            home_system_id="home_system",
            home_planet_id="home_planet"
        )
        
        data = empire.dict()
        assert data["name"] == "Test Empire"
        assert data["home_system_id"] == "home_system"
        assert data["is_player"] is False


class TestShip:
    """Test the Ship model."""
    
    def test_ship_creation(self):
        """Test ship creation."""
        ship = Ship(
            name="Test Ship",
            design_id="test_design",
            empire_id="test_empire"
        )
        
        assert ship.name == "Test Ship"
        assert ship.design_id == "test_design"
        assert ship.empire_id == "test_empire"
        assert ship.fuel == 100.0
        assert ship.condition == 100.0
        assert ship.structure == 100.0
    
    def test_ship_defaults(self):
        """Test ship default values."""
        ship = Ship(
            name="Test Ship",
            design_id="test_design",
            empire_id="test_empire"
        )
        
        assert ship.current_mass == 0.0
        assert ship.current_crew == 0
        assert ship.shields == 0.0
        assert ship.armor == 0.0
        assert len(ship.current_orders) == 0
        assert not ship.automation_enabled


class TestColony:
    """Test the Colony model."""
    
    def test_colony_creation(self):
        """Test colony creation."""
        colony = Colony(
            name="Test Colony",
            empire_id="test_empire",
            planet_id="test_planet"
        )
        
        assert colony.name == "Test Colony"
        assert colony.empire_id == "test_empire"
        assert colony.planet_id == "test_planet"
        assert colony.population == 1000
    
    def test_colony_defaults(self):
        """Test colony default values."""
        colony = Colony(
            name="Test Colony",
            empire_id="test_empire",
            planet_id="test_planet"
        )
        
        assert colony.established_date == 0.0
        assert colony.happiness == 50.0
        assert colony.growth_rate == 1.0
        assert len(colony.infrastructure) == 0
        assert len(colony.stockpiles) == 0


"""
Star system generation for PyAurora 4X

Generates realistic star systems with planets and orbital parameters.
"""

import random
import math
from typing import List, Optional
import logging

from pyaurora4x.core.models import (
    StarSystem,
    Planet,
    Vector3D,
    AsteroidBelt,
    JumpPoint,
)
from pyaurora4x.core.enums import PlanetType, StarType

logger = logging.getLogger(__name__)


class StarSystemGenerator:
    """
    Generates star systems with realistic parameters.

    Uses astronomical data and algorithms to create diverse but plausible
    star systems for the game.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the star system generator.

        Args:
            seed: Random seed for reproducible generation
        """
        if seed is not None:
            random.seed(seed)

        self.system_counter = 0
        logger.debug("Star system generator initialized")

    def generate_system(self, system_id: Optional[str] = None) -> StarSystem:
        """
        Generate a complete star system.

        Args:
            system_id: Optional custom system ID

        Returns:
            Generated star system
        """
        if system_id is None:
            system_id = f"system_{self.system_counter}"
            self.system_counter += 1

        # Generate star properties
        star_type = self._generate_star_type()
        star_mass = self._generate_star_mass(star_type)
        star_luminosity = self._generate_star_luminosity(star_mass)

        # Generate system name
        system_name = self._generate_system_name()

        # Generate planets
        num_planets = self._generate_planet_count(star_type)
        planets = self._generate_planets(num_planets, star_mass, star_luminosity)

        # Generate asteroid belts
        asteroid_belts = self._generate_asteroid_belts(planets)

        # Calculate habitable zone
        habitable_zone_inner, habitable_zone_outer = self._calculate_habitable_zone(
            star_luminosity
        )

        system = StarSystem(
            id=system_id,
            name=system_name,
            star_type=star_type,
            star_mass=star_mass,
            star_luminosity=star_luminosity,
            planets=planets,
            asteroid_belts=asteroid_belts,
            habitable_zone_inner=habitable_zone_inner,
            habitable_zone_outer=habitable_zone_outer,
        )

        logger.info(f"Generated star system: {system_name} ({len(planets)} planets)")
        return system

    def _generate_star_type(self) -> StarType:
        """Generate a star type based on stellar statistics."""
        rand = random.random()

        # Based on rough stellar distribution
        if rand < 0.76:
            return StarType.M_DWARF
        elif rand < 0.88:
            return StarType.K_DWARF
        elif rand < 0.96:
            return StarType.G_DWARF
        elif rand < 0.99:
            return StarType.F_DWARF
        else:
            return StarType.A_STAR

    def _generate_star_mass(self, star_type: StarType) -> float:
        """
        Generate star mass based on type.

        Args:
            star_type: Type of star

        Returns:
            Star mass in solar masses
        """
        mass_ranges = {
            StarType.M_DWARF: (0.08, 0.45),
            StarType.K_DWARF: (0.45, 0.8),
            StarType.G_DWARF: (0.8, 1.04),
            StarType.F_DWARF: (1.04, 1.4),
            StarType.A_STAR: (1.4, 2.1),
        }

        min_mass, max_mass = mass_ranges[star_type]
        return random.uniform(min_mass, max_mass)

    def _generate_star_luminosity(self, star_mass: float) -> float:
        """
        Calculate star luminosity from mass using mass-luminosity relation.

        Args:
            star_mass: Star mass in solar masses

        Returns:
            Star luminosity in solar luminosities
        """
        # Simplified mass-luminosity relation: L ∝ M^3.5
        return star_mass**3.5

    def _generate_planet_count(self, star_type: StarType) -> int:
        """
        Generate number of planets based on star type.

        Args:
            star_type: Type of star

        Returns:
            Number of planets to generate
        """
        # Simplified distribution - real distributions are more complex
        base_count = {
            StarType.M_DWARF: 2,
            StarType.K_DWARF: 3,
            StarType.G_DWARF: 4,
            StarType.F_DWARF: 3,
            StarType.A_STAR: 2,
        }

        base = base_count[star_type]
        variation = random.randint(-1, 3)
        return max(1, base + variation)

    def _generate_planets(
        self, count: int, star_mass: float, star_luminosity: float
    ) -> List[Planet]:
        """
        Generate planets for the star system.

        Args:
            count: Number of planets to generate
            star_mass: Star mass in solar masses
            star_luminosity: Star luminosity in solar luminosities

        Returns:
            List of generated planets
        """
        planets = []

        # Generate orbital distances using Titius-Bode-like law
        orbital_distances = self._generate_orbital_distances(count)

        for i, distance in enumerate(orbital_distances):
            planet = self._generate_planet(i, distance, star_mass, star_luminosity)
            planets.append(planet)

        return planets

    def _generate_orbital_distances(self, count: int) -> List[float]:
        """
        Generate orbital distances using a Titius-Bode-like progression.

        Args:
            count: Number of orbital distances to generate

        Returns:
            List of orbital distances in AU
        """
        distances = []

        # Start with inner planet distance
        base_distance = random.uniform(0.1, 0.4)

        for i in range(count):
            if i == 0:
                distance = base_distance
            else:
                # Each planet is roughly 1.4-2.0 times farther than the previous
                factor = random.uniform(1.4, 2.0)
                distance = distances[-1] * factor

            distances.append(distance)

        return distances

    def _generate_planet(
        self,
        index: int,
        orbital_distance: float,
        star_mass: float,
        star_luminosity: float,
    ) -> Planet:
        """
        Generate a single planet.

        Args:
            index: Planet index (0-based)
            orbital_distance: Orbital distance in AU
            star_mass: Star mass in solar masses
            star_luminosity: Star luminosity in solar luminosities

        Returns:
            Generated planet
        """
        planet_id = f"planet_{index}"
        planet_name = self._generate_planet_name(index)

        # Calculate orbital period using Kepler's third law
        orbital_period = self._calculate_orbital_period(orbital_distance, star_mass)

        # Generate planet properties
        planet_type = self._determine_planet_type(orbital_distance, star_luminosity)
        mass = self._generate_planet_mass(planet_type)
        radius = self._generate_planet_radius(mass, planet_type)

        # Generate orbital elements
        eccentricity = random.uniform(0.0, 0.3)
        inclination = random.gauss(0.0, 5.0)  # Most planets have low inclination
        longitude_of_ascending_node = random.uniform(0.0, 360.0)
        argument_of_periapsis = random.uniform(0.0, 360.0)
        mean_anomaly = random.uniform(0.0, 360.0)

        # Calculate initial position (simplified)
        position = self._calculate_initial_position(
            orbital_distance, eccentricity, mean_anomaly
        )

        return Planet(
            id=planet_id,
            name=planet_name,
            planet_type=planet_type,
            mass=mass,
            radius=radius,
            orbital_distance=orbital_distance,
            orbital_period=orbital_period,
            eccentricity=eccentricity,
            inclination=inclination,
            longitude_of_ascending_node=longitude_of_ascending_node,
            argument_of_periapsis=argument_of_periapsis,
            mean_anomaly=mean_anomaly,
            position=position,
            atmosphere_composition={},
            surface_temperature=self._calculate_surface_temperature(
                orbital_distance, star_luminosity
            ),
        )

    def _calculate_orbital_period(self, distance_au: float, star_mass: float) -> float:
        """
        Calculate orbital period using Kepler's third law.

        Args:
            distance_au: Orbital distance in AU
            star_mass: Star mass in solar masses

        Returns:
            Orbital period in Earth years
        """
        # Kepler's third law: P^2 = (4π^2/GM) * a^3
        # For solar masses and AU: P^2 = a^3 / M
        return math.sqrt(distance_au**3 / star_mass)

    def _determine_planet_type(
        self, distance_au: float, star_luminosity: float
    ) -> PlanetType:
        """
        Determine planet type based on distance from star.

        Args:
            distance_au: Orbital distance in AU
            star_luminosity: Star luminosity in solar luminosities

        Returns:
            Planet type
        """
        # Calculate effective temperature zone
        habitable_inner, habitable_outer = self._calculate_habitable_zone(
            star_luminosity
        )

        if distance_au < 0.4:
            return PlanetType.TERRESTRIAL  # Hot rocky planet
        elif distance_au < habitable_inner:
            return PlanetType.TERRESTRIAL  # Warm rocky planet
        elif distance_au <= habitable_outer:
            return PlanetType.TERRESTRIAL  # Potentially habitable
        elif distance_au < 5.0:
            return PlanetType.GAS_GIANT  # Jupiter-like
        else:
            return PlanetType.ICE_GIANT  # Neptune-like

    def _calculate_habitable_zone(self, star_luminosity: float) -> tuple:
        """
        Calculate habitable zone boundaries.

        Args:
            star_luminosity: Star luminosity in solar luminosities

        Returns:
            Tuple of (inner_boundary, outer_boundary) in AU
        """
        # Conservative habitable zone calculation
        inner = 0.95 * math.sqrt(star_luminosity)
        outer = 1.37 * math.sqrt(star_luminosity)
        return inner, outer

    def _generate_planet_mass(self, planet_type: PlanetType) -> float:
        """
        Generate planet mass based on type.

        Args:
            planet_type: Type of planet

        Returns:
            Planet mass in Earth masses
        """
        mass_ranges = {
            PlanetType.TERRESTRIAL: (0.1, 2.0),
            PlanetType.GAS_GIANT: (50.0, 500.0),
            PlanetType.ICE_GIANT: (10.0, 50.0),
        }

        min_mass, max_mass = mass_ranges[planet_type]
        return random.uniform(min_mass, max_mass)

    def _generate_planet_radius(self, mass: float, planet_type: PlanetType) -> float:
        """
        Generate planet radius based on mass and type.

        Args:
            mass: Planet mass in Earth masses
            planet_type: Type of planet

        Returns:
            Planet radius in Earth radii
        """
        if planet_type == PlanetType.TERRESTRIAL:
            # Mass-radius relation for rocky planets
            return mass**0.27
        elif planet_type == PlanetType.GAS_GIANT:
            # Gas giants have complex mass-radius relations
            return mass**0.1
        else:  # ICE_GIANT
            return mass**0.15

    def _calculate_initial_position(
        self, distance_au: float, eccentricity: float, mean_anomaly_deg: float
    ) -> Vector3D:
        """
        Calculate initial planet position.

        Args:
            distance_au: Orbital distance in AU
            eccentricity: Orbital eccentricity
            mean_anomaly_deg: Mean anomaly in degrees

        Returns:
            Initial position vector
        """
        # Convert to radians
        mean_anomaly = math.radians(mean_anomaly_deg)

        # Solve Kepler's equation for eccentric anomaly (simplified)
        eccentric_anomaly = mean_anomaly + eccentricity * math.sin(mean_anomaly)

        # Calculate true anomaly
        true_anomaly = 2 * math.atan2(
            math.sqrt(1 + eccentricity) * math.sin(eccentric_anomaly / 2),
            math.sqrt(1 - eccentricity) * math.cos(eccentric_anomaly / 2),
        )

        # Calculate distance
        r = distance_au * (1 - eccentricity * math.cos(eccentric_anomaly))

        # Convert to Cartesian coordinates (in km)
        x = r * math.cos(true_anomaly) * 149597870.7  # AU to km
        y = r * math.sin(true_anomaly) * 149597870.7
        z = 0.0  # Simplified - assume orbit in xy plane

        return Vector3D(x=x, y=y, z=z)

    def _calculate_surface_temperature(
        self, distance_au: float, star_luminosity: float
    ) -> float:
        """
        Calculate approximate surface temperature.

        Args:
            distance_au: Orbital distance in AU
            star_luminosity: Star luminosity in solar luminosities

        Returns:
            Surface temperature in Kelvin
        """
        # Simplified blackbody temperature calculation
        solar_temp = 278.5  # Earth's equilibrium temperature
        temp = solar_temp * math.sqrt(star_luminosity) / math.sqrt(distance_au)
        return temp

    def _generate_system_name(self) -> str:
        """Generate a name for the star system."""
        # Simple naming scheme - could be expanded with more variety
        prefixes = [
            "Alpha",
            "Beta",
            "Gamma",
            "Delta",
            "Epsilon",
            "Zeta",
            "Eta",
            "Theta",
            "Iota",
            "Kappa",
            "Lambda",
            "Mu",
            "Nu",
            "Xi",
            "Omicron",
            "Pi",
            "Rho",
            "Sigma",
            "Tau",
            "Upsilon",
            "Phi",
            "Chi",
            "Psi",
            "Omega",
        ]

        suffixes = [
            "Centauri",
            "Draconis",
            "Orionis",
            "Cygni",
            "Andromedae",
            "Cassiopeiae",
            "Lyrae",
            "Aquilae",
            "Bootis",
            "Virginis",
            "Leonis",
            "Ursae",
            "Cephei",
            "Persei",
            "Aurigae",
            "Geminorum",
        ]

        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)

        return f"{prefix} {suffix}"

    def _generate_planet_name(self, index: int) -> str:
        """
        Generate a name for a planet.

        Args:
            index: Planet index (0-based)

        Returns:
            Planet name
        """
        # Convert index to Roman numerals for traditional naming
        roman_numerals = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

        if index < len(roman_numerals):
            return f"Planet {roman_numerals[index]}"
        else:
            return f"Planet {index + 1}"

    def _generate_asteroid_belts(self, planets: List[Planet]) -> List[AsteroidBelt]:
        """Generate asteroid belts for the system.

        Args:
            planets: List of already generated planets.

        Returns:
            List of AsteroidBelt objects with distance and width in AU.
        """
        belts: List[AsteroidBelt] = []

        # Determine number of belts (0-2) with simple probabilities
        belt_count = random.choices([0, 1, 2], weights=[0.5, 0.35, 0.15])[0]
        if belt_count == 0:
            return belts

        # Base the outer range on the outermost planet if available
        max_distance = max((p.orbital_distance for p in planets), default=5.0)
        max_distance = max_distance * 1.5

        for _ in range(belt_count):
            distance = random.uniform(0.5, max_distance)
            width = random.uniform(0.1, 0.5)
            belts.append(AsteroidBelt(distance=distance, width=width))

        # Sort belts by distance for consistency
        belts.sort(key=lambda b: b.distance)
        return belts

    def generate_jump_network(self, systems: List[StarSystem]) -> None:
        """Create simple jump point connections between systems."""
        if len(systems) < 2:
            return

        for i, system in enumerate(systems):
            target = systems[(i + 1) % len(systems)]

            jp1 = self._create_jump_point(system)
            jp1.connects_to = target.id
            system.jump_points.append(jp1)

            jp2 = self._create_jump_point(target)
            jp2.connects_to = system.id
            target.jump_points.append(jp2)

    def _create_jump_point(self, system: StarSystem) -> JumpPoint:
        distance_au = random.uniform(0.2, 2.0)
        angle = random.uniform(0.0, 2 * math.pi)
        r = distance_au * 149597870.7
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        pos = Vector3D(x=x, y=y, z=0.0)
        return JumpPoint(position=pos, connects_to="")

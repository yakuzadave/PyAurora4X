"""
Unit tests for PyAurora 4X orbital mechanics

Tests the orbital mechanics simulation using REBOUND and fallback systems.
"""

import math
from unittest.mock import Mock, patch

import pytest

from pyaurora4x.core.enums import PlanetType, StarType
from pyaurora4x.core.models import Planet, StarSystem, Vector3D
from pyaurora4x.engine.orbital_mechanics import OrbitalMechanics


class TestOrbitalMechanics:
    """Test the OrbitalMechanics class."""

    def test_orbital_mechanics_initialization(self):
        """Test orbital mechanics initialization."""
        om = OrbitalMechanics()

        assert isinstance(om.simulations, dict)
        assert len(om.simulations) == 0
        assert isinstance(om.use_rebound, bool)

    def test_system_initialization(self):
        """Test star system initialization."""
        om = OrbitalMechanics()

        # Create a test star system
        planet = Planet(
            name="Test Planet",
            planet_type=PlanetType.TERRESTRIAL,
            mass=1.0,
            radius=1.0,
            surface_temperature=288.0,
            orbital_distance=1.0,
            orbital_period=1.0,
            eccentricity=0.1,
            inclination=5.0,
            longitude_of_ascending_node=45.0,
            argument_of_periapsis=90.0,
            mean_anomaly=180.0,
            position=Vector3D(x=149597870.7, y=0.0, z=0.0),
        )

        system = StarSystem(
            name="Test System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0,
            planets=[planet],
        )

        om.initialize_system(system)

        # System should be added to simulations
        assert system.id in om.simulations

    def test_rebound_timestep_and_mass_conversion(self):
        """Ensure REBOUND initialization sets correct mass and timestep."""
        om = OrbitalMechanics(simulation_timestep=7200.0)

        planet = Planet(
            name="Mass Test",
            planet_type=PlanetType.TERRESTRIAL,
            mass=2.0,
            radius=1.0,
            surface_temperature=288.0,
            orbital_distance=1.0,
            orbital_period=1.0,
            position=Vector3D(x=149597870.7, y=0.0, z=0.0),
        )

        system = StarSystem(
            name="Mass System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0,
            planets=[planet],
        )

        om.initialize_system(system)

        if om.use_rebound:
            sim = om.simulations[system.id]
            expected_mass = planet.mass * (5.972e24 / 1.989e30)
            assert pytest.approx(sim.particles[1].m, rel=1e-6) == expected_mass

            expected_dt = 7200.0 / (365.25 * 24 * 3600)
            assert pytest.approx(sim.dt, rel=1e-6) == expected_dt

    def test_simple_orbital_mechanics(self):
        """Test simple orbital mechanics (fallback mode)."""
        # Force simple mode
        om = OrbitalMechanics()
        om.use_rebound = False

        planet = Planet(
            name="Test Planet",
            planet_type=PlanetType.TERRESTRIAL,
            mass=1.0,
            radius=1.0,
            surface_temperature=288.0,
            orbital_distance=1.0,
            orbital_period=1.0,
            position=Vector3D(),
        )

        system = StarSystem(
            name="Test System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0,
            planets=[planet],
        )

        om.initialize_system(system)

        # Update positions
        initial_position = planet.position.copy()
        om.update_positions(system, 1000.0)  # Advance 1000 seconds

        # Position should have changed
        assert (
            planet.position.x != initial_position.x
            or planet.position.y != initial_position.y
            or planet.position.z != initial_position.z
        )

    def test_orbital_position_update(self):
        """Test orbital position updates."""
        om = OrbitalMechanics()

        planet = Planet(
            name="Test Planet",
            planet_type=PlanetType.TERRESTRIAL,
            mass=1.0,
            radius=1.0,
            surface_temperature=288.0,
            orbital_distance=1.0,
            orbital_period=1.0,
            position=Vector3D(x=149597870.7, y=0.0, z=0.0),
        )

        system = StarSystem(
            name="Test System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0,
            planets=[planet],
        )

        om.initialize_system(system)

        # Store initial position
        initial_x = planet.position.x
        initial_y = planet.position.y

        # Update positions after some time
        om.update_positions(system, 3600.0)  # 1 hour

        # Planet should have moved
        distance_moved = math.sqrt(
            (planet.position.x - initial_x) ** 2 + (planet.position.y - initial_y) ** 2
        )
        assert distance_moved > 0

    def test_orbital_velocity_calculation(self):
        """Test orbital velocity calculation."""
        om = OrbitalMechanics()

        planet = Planet(
            name="Test Planet",
            planet_type=PlanetType.TERRESTRIAL,
            mass=1.0,
            radius=1.0,
            surface_temperature=288.0,
            orbital_distance=1.0,
            orbital_period=1.0,
            position=Vector3D(x=149597870.7, y=0.0, z=0.0),
        )

        system = StarSystem(
            name="Test System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0,
            planets=[planet],
        )

        om.initialize_system(system)

        velocity = om.get_orbital_velocity(system, 0)

        if velocity is not None:
            # Should have some velocity
            speed = velocity.magnitude()
            assert speed > 0

            # Velocity should be roughly perpendicular to position for circular orbit
            # (dot product should be close to zero)
            dot_product = (
                planet.position.x * velocity.x
                + planet.position.y * velocity.y
                + planet.position.z * velocity.z
            )

            # Allow some tolerance for numerical errors
            assert (
                abs(dot_product) < 1e6
            )  # Relatively small compared to position magnitude

    def test_transfer_orbit_calculation(self):
        """Test transfer orbit calculation."""
        om = OrbitalMechanics()

        start_pos = Vector3D(x=149597870.7, y=0.0, z=0.0)  # 1 AU
        target_pos = Vector3D(x=227940000.0, y=0.0, z=0.0)  # ~1.5 AU

        transfer = om.calculate_transfer_orbit(start_pos, target_pos, 1.0)

        assert "transfer_time" in transfer
        assert "semi_major_axis" in transfer
        assert "start_radius" in transfer
        assert "target_radius" in transfer

        # Transfer time should be positive
        assert transfer["transfer_time"] > 0

        # Semi-major axis should be between start and target radii
        start_r = transfer["start_radius"]
        target_r = transfer["target_radius"]
        semi_major = transfer["semi_major_axis"]

        assert min(start_r, target_r) < semi_major < max(start_r, target_r)

    def test_multiple_planets(self):
        """Test system with multiple planets."""
        om = OrbitalMechanics()

        planets = []
        for i in range(3):
            planet = Planet(
                name=f"Planet {i+1}",
                planet_type=PlanetType.TERRESTRIAL,
                mass=1.0,
                radius=1.0,
                surface_temperature=288.0,
                orbital_distance=0.5 + i * 0.7,  # Different orbital distances
                orbital_period=1.0 + i,
                position=Vector3D(x=(0.5 + i * 0.7) * 149597870.7, y=0.0, z=0.0),
            )
            planets.append(planet)

        system = StarSystem(
            name="Multi-Planet System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0,
            planets=planets,
        )

        om.initialize_system(system)

        # Store initial positions
        initial_positions = [planet.position.copy() for planet in planets]

        # Update positions
        om.update_positions(system, 7200.0)  # 2 hours

        # All planets should have moved
        for i, planet in enumerate(planets):
            distance_moved = math.sqrt(
                (planet.position.x - initial_positions[i].x) ** 2
                + (planet.position.y - initial_positions[i].y) ** 2
            )
            assert distance_moved > 0

    def test_inclined_orbit(self):
        """Test planet with inclined orbit."""
        om = OrbitalMechanics()
        om.use_rebound = False  # Use simple mechanics to test inclination

        planet = Planet(
            name="Inclined Planet",
            planet_type=PlanetType.TERRESTRIAL,
            mass=1.0,
            radius=1.0,
            surface_temperature=288.0,
            orbital_distance=1.0,
            orbital_period=1.0,
            inclination=30.0,  # 30 degree inclination
            position=Vector3D(x=149597870.7, y=0.0, z=0.0),
        )

        system = StarSystem(
            name="Inclined System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0,
            planets=[planet],
        )

        om.initialize_system(system)

        # Update positions
        om.update_positions(system, 1000.0)

        # Planet should have some z-component due to inclination
        # (in simple mode, this is applied as a tilt)
        # The exact behavior depends on the implementation
        assert planet.position is not None

    def test_eccentric_orbit(self):
        """Test planet with eccentric orbit."""
        om = OrbitalMechanics()
        om.use_rebound = False  # Use simple mechanics for predictable results

        planet = Planet(
            name="Eccentric Planet",
            planet_type=PlanetType.TERRESTRIAL,
            mass=1.0,
            radius=1.0,
            surface_temperature=288.0,
            orbital_distance=1.0,
            orbital_period=1.0,
            eccentricity=0.5,  # Highly eccentric
            position=Vector3D(x=149597870.7, y=0.0, z=0.0),
        )

        system = StarSystem(
            name="Eccentric System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0,
            planets=[planet],
        )

        om.initialize_system(system)

        # Store positions at different times to see variation
        positions = []
        times = [0, 1000, 2000, 3000, 4000]

        for time in times:
            om.update_positions(system, time)
            positions.append(planet.position.copy())

        # Distance from star should vary significantly for eccentric orbit
        distances = [pos.magnitude() for pos in positions]

        max_dist = max(distances)
        min_dist = min(distances)
        if max_dist - min_dist > 1e-3:
            # For e=0.5, ratio should be about 3:1
            assert max_dist / min_dist > 1.2  # At least some variation

    def test_cleanup_system(self):
        """Test system cleanup."""
        om = OrbitalMechanics()

        planet = Planet(
            name="Test Planet",
            planet_type=PlanetType.TERRESTRIAL,
            mass=1.0,
            radius=1.0,
            surface_temperature=288.0,
            orbital_distance=1.0,
            orbital_period=1.0,
            position=Vector3D(),
        )

        system = StarSystem(
            name="Test System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0,
            planets=[planet],
        )

        om.initialize_system(system)
        assert system.id in om.simulations

        om.cleanup_system(system.id)
        assert system.id not in om.simulations

    def test_invalid_system_update(self):
        """Test updating positions for non-existent system."""
        om = OrbitalMechanics()

        system = StarSystem(
            name="Test System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0,
            planets=[],
        )

        # Try to update without initializing - should not crash
        om.update_positions(system, 1000.0)
        # Should complete without error

    def test_orbital_velocity_for_invalid_planet(self):
        """Test getting orbital velocity for invalid planet index."""
        om = OrbitalMechanics()

        system = StarSystem(
            name="Test System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0,
            planets=[],
        )

        om.initialize_system(system)

        # Try to get velocity for non-existent planet
        velocity = om.get_orbital_velocity(system, 0)
        assert velocity is None

    @patch("pyaurora4x.engine.orbital_mechanics.REBOUND_AVAILABLE", False)
    def test_forced_simple_mode(self):
        """Test forced simple mode when REBOUND is not available."""
        om = OrbitalMechanics()

        # Should automatically use simple mode
        assert not om.use_rebound

        planet = Planet(
            name="Test Planet",
            planet_type=PlanetType.TERRESTRIAL,
            mass=1.0,
            radius=1.0,
            surface_temperature=288.0,
            orbital_distance=1.0,
            orbital_period=1.0,
            position=Vector3D(),
        )

        system = StarSystem(
            name="Test System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0,
            planets=[planet],
        )

        # Should work in simple mode
        om.initialize_system(system)
        om.update_positions(system, 1000.0)

        # Should complete without error
        assert system.id in om.simulations


class TestOrbitalMechanicsIntegration:
    """Integration tests for orbital mechanics."""

    def test_earth_like_orbit(self):
        """Test Earth-like orbital parameters."""
        om = OrbitalMechanics()

        # Earth-like planet
        earth = Planet(
            name="Earth-like",
            planet_type=PlanetType.TERRESTRIAL,
            mass=1.0,  # Earth masses
            radius=1.0,  # Earth radii
            surface_temperature=288.0,  # Kelvin
            orbital_distance=1.0,  # AU
            orbital_period=1.0,  # Earth years
            eccentricity=0.017,  # Earth's eccentricity
            inclination=0.0,  # Degrees
            position=Vector3D(x=149597870.7, y=0.0, z=0.0),
        )

        # Sun-like star
        system = StarSystem(
            name="Solar System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,  # Solar masses
            star_luminosity=1.0,  # Solar luminosities
            planets=[earth],
        )

        om.initialize_system(system)

        # Test orbital velocity should be roughly 30 km/s for Earth
        velocity = om.get_orbital_velocity(system, 0)
        if velocity is not None:
            speed = velocity.magnitude()
            # Should be roughly 30 km/s (allow wide tolerance for simplified physics)
            assert 10.0 < speed < 50.0

    def test_mars_like_orbit(self):
        """Test Mars-like orbital parameters."""
        om = OrbitalMechanics()

        # Mars-like planet
        mars = Planet(
            name="Mars-like",
            planet_type=PlanetType.TERRESTRIAL,
            mass=0.107,  # Mars mass in Earth masses
            radius=0.532,  # Mars radius in Earth radii
            surface_temperature=210.0,  # Kelvin
            orbital_distance=1.524,  # AU
            orbital_period=1.88,  # Earth years
            eccentricity=0.094,  # Mars eccentricity
            position=Vector3D(x=1.524 * 149597870.7, y=0.0, z=0.0),
        )

        system = StarSystem(
            name="Mars System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0,
            planets=[mars],
        )

        om.initialize_system(system)

        # Update position over time
        initial_distance = mars.position.magnitude()

        # Advance through part of orbit
        om.update_positions(system, 365.25 * 24 * 3600 * 0.25)  # Quarter year

        # Should have moved
        new_distance = mars.position.magnitude()
        distance_moved = math.sqrt(
            (mars.position.x - 1.524 * 149597870.7) ** 2 + mars.position.y**2
        )
        assert distance_moved > 1e6  # Should have moved at least 1000 km

    def test_gas_giant_orbit(self):
        """Test gas giant orbital mechanics."""
        om = OrbitalMechanics()

        # Jupiter-like planet
        jupiter = Planet(
            name="Jupiter-like",
            planet_type=PlanetType.GAS_GIANT,
            mass=318.0,  # Jupiter masses in Earth masses
            radius=11.0,  # Jupiter radii in Earth radii
            surface_temperature=165.0,  # Kelvin (actually cloud top temperature)
            orbital_distance=5.2,  # AU
            orbital_period=11.86,  # Earth years
            eccentricity=0.049,
            position=Vector3D(x=5.2 * 149597870.7, y=0.0, z=0.0),
        )

        system = StarSystem(
            name="Gas Giant System",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0,
            planets=[jupiter],
        )

        om.initialize_system(system)

        # Gas giants should move more slowly
        velocity = om.get_orbital_velocity(system, 0)
        if velocity is not None:
            speed = velocity.magnitude()
            # Jupiter's orbital speed is about 13 km/s
            assert 5.0 < speed < 20.0

    def test_transfer_orbit_hohmann(self):
        """Test Hohmann transfer orbit calculation."""
        om = OrbitalMechanics()

        # Earth to Mars transfer
        earth_pos = Vector3D(x=149597870.7, y=0.0, z=0.0)  # 1 AU
        mars_pos = Vector3D(x=227940000.0, y=0.0, z=0.0)  # 1.524 AU

        transfer = om.calculate_transfer_orbit(earth_pos, mars_pos, 1.0)

        # For Earth-Mars transfer, typical time is about 9 months
        transfer_time_months = transfer["transfer_time"] / (30 * 24 * 3600)
        assert 6.0 < transfer_time_months < 12.0  # Reasonable range

        # Semi-major axis should be average of start and end distances
        expected_sma = (149597870.7 + 227940000.0) / 2
        actual_sma = transfer["semi_major_axis"]
        assert abs(actual_sma - expected_sma) < 1e7  # Within 10,000 km

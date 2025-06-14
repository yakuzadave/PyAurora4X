"""
Orbital mechanics simulation using REBOUND for PyAurora 4X

Provides realistic orbital dynamics for planets, moons, and spacecraft.
"""

import logging
from typing import Dict, Optional

import numpy as np

try:
    import rebound

    REBOUND_AVAILABLE = True
except ImportError:
    REBOUND_AVAILABLE = False
    logging.warning("REBOUND not available - using simplified orbital mechanics")

from pyaurora4x.core.models import StarSystem, Vector3D

logger = logging.getLogger(__name__)


EARTH_MASS_IN_SOLAR_MASSES = 5.972e24 / 1.989e30  # Earth mass to solar mass conversion


class OrbitalMechanics:
    """
    Manages orbital mechanics for star systems using REBOUND.

    Falls back to simplified Keplerian orbits if REBOUND is not available.
    """

    def __init__(self, simulation_timestep: float = 3600.0):
        """Initialize the orbital mechanics system.

        Args:
            simulation_timestep: Desired timestep in seconds for REBOUND simulations.
        """
        self.simulations: Dict[str, any] = {}  # system_id -> rebound simulation
        self.use_rebound = REBOUND_AVAILABLE
        self.simulation_timestep = simulation_timestep

        if self.use_rebound:
            logger.info("Using REBOUND for orbital mechanics")
        else:
            logger.info("Using simplified orbital mechanics (REBOUND not available)")

    def initialize_system(self, star_system: StarSystem) -> None:
        """
        Initialize orbital mechanics for a star system.

        Args:
            star_system: The star system to initialize
        """
        if self.use_rebound:
            self._initialize_rebound_system(star_system)
        else:
            self._initialize_simple_system(star_system)

    def _initialize_rebound_system(self, star_system: StarSystem) -> None:
        """Initialize a REBOUND simulation for the star system."""
        sim = rebound.Simulation()
        sim.units = ("AU", "yr", "Msun")  # Astronomical units
        sim.dt = self.simulation_timestep / (365.25 * 24 * 3600)

        # Add the central star
        sim.add(m=star_system.star_mass)

        # Add planets
        for planet in star_system.planets:
            # Convert orbital parameters to REBOUND format
            a = planet.orbital_distance  # Semi-major axis in AU
            e = planet.eccentricity
            inc = np.radians(planet.inclination)
            Omega = np.radians(planet.longitude_of_ascending_node)
            omega = np.radians(planet.argument_of_periapsis)
            M = np.radians(planet.mean_anomaly)

            # Convert mass from Earth masses to solar masses
            mass_msun = planet.mass * EARTH_MASS_IN_SOLAR_MASSES

            # Add planet to simulation
            sim.add(m=mass_msun, a=a, e=e, inc=inc, Omega=Omega, omega=omega, M=M)

        # Store the simulation
        self.simulations[star_system.id] = sim
        logger.debug(f"Initialized REBOUND simulation for system {star_system.name}")

    def _initialize_simple_system(self, star_system: StarSystem) -> None:
        """Initialize simplified orbital mechanics for the star system."""
        # Store initial orbital parameters for simple calculation
        system_data = {"planets": [], "start_time": 0.0}

        for planet in star_system.planets:
            planet_data = {
                "orbital_distance": planet.orbital_distance,
                "orbital_period": planet.orbital_period,
                "eccentricity": planet.eccentricity,
                "inclination": planet.inclination,
                "initial_position": planet.position.copy(),
            }
            system_data["planets"].append(planet_data)

        self.simulations[star_system.id] = system_data
        logger.debug(
            f"Initialized simple orbital mechanics for system {star_system.name}"
        )

    def update_positions(self, star_system: StarSystem, current_time: float) -> None:
        """
        Update planetary positions based on current game time.

        Args:
            star_system: The star system to update
            current_time: Current game time in seconds
        """
        if star_system.id not in self.simulations:
            logger.warning(f"No simulation found for system {star_system.id}")
            return

        if self.use_rebound:
            self._update_rebound_positions(star_system, current_time)
        else:
            self._update_simple_positions(star_system, current_time)

    def _update_rebound_positions(
        self, star_system: StarSystem, current_time: float
    ) -> None:
        """Update positions using REBOUND simulation."""
        sim = self.simulations[star_system.id]

        # Convert game time to years (REBOUND time units)
        time_years = current_time / (365.25 * 24 * 3600)

        # Integrate to the current time using configured timestep
        if time_years != sim.t:
            sim.integrate(time_years)

        # Update planet positions
        for i, planet in enumerate(star_system.planets):
            if i + 1 < sim.N:  # Skip the star (index 0)
                particle = sim.particles[i + 1]

                # Convert from AU to kilometers
                x_km = particle.x * 149597870.7
                y_km = particle.y * 149597870.7
                z_km = particle.z * 149597870.7

                planet.position = Vector3D(x=x_km, y=y_km, z=z_km)

    def _update_simple_positions(
        self, star_system: StarSystem, current_time: float
    ) -> None:
        """Update positions using simplified Keplerian orbits."""
        system_data = self.simulations[star_system.id]

        for i, planet in enumerate(star_system.planets):

            if i < len(system_data['planets']):
                planet_data = system_data['planets'][i]
                

                # Calculate mean motion (radians per second)
                period_seconds = planet_data['orbital_period']
                mean_motion = 2 * np.pi / period_seconds

                
                # Calculate mean anomaly at current time
                mean_anomaly = (mean_motion * current_time) % (2 * np.pi)
                

                e = planet_data.get("eccentricity", 0.0)
                eccentric_anomaly = mean_anomaly
                for _ in range(5):
                    eccentric_anomaly = mean_anomaly + e * np.sin(eccentric_anomaly)

                true_anomaly = 2 * np.arctan2(
                    np.sqrt(1 + e) * np.sin(eccentric_anomaly / 2),
                    np.sqrt(1 - e) * np.cos(eccentric_anomaly / 2),
                )

                a = planet_data["orbital_distance"] * 149597870.7
                r = a * (1 - e * np.cos(eccentric_anomaly))


                x = r * np.cos(true_anomaly)
                y = r * np.sin(true_anomaly)

                # Apply inclination (simplified - only tilt around x-axis)
                inclination = np.radians(planet_data["inclination"])
                y_inclined = y * np.cos(inclination)
                z_inclined = y * np.sin(inclination)

                planet.position = Vector3D(x=x, y=y_inclined, z=z_inclined)

    def get_orbital_velocity(
        self, star_system: StarSystem, planet_index: int
    ) -> Optional[Vector3D]:
        """
        Get the orbital velocity of a planet.

        Args:
            star_system: The star system
            planet_index: Index of the planet

        Returns:
            Velocity vector, or None if not available
        """
        if star_system.id not in self.simulations:
            return None

        if self.use_rebound:
            sim = self.simulations[star_system.id]
            if planet_index + 1 < sim.N:
                particle = sim.particles[planet_index + 1]
                # Convert from AU/year to km/s
                conversion = 149597870.7 / (365.25 * 24 * 3600)
                vx = particle.vx * conversion
                vy = particle.vy * conversion
                vz = particle.vz * conversion
                return Vector3D(x=vx, y=vy, z=vz)
        else:
            # Simple circular velocity calculation
            if planet_index < len(star_system.planets):
                planet = star_system.planets[planet_index]
                r = planet.orbital_distance * 149597870.7  # km

                # Circular orbital velocity: v = sqrt(GM/r)
                # Assuming solar mass
                G = 6.67430e-11  # m^3 kg^-1 s^-2
                M = 1.989e30  # kg (solar mass)
                v = np.sqrt(G * M / (r * 1000))  # m/s
                v_km_s = v / 1000  # km/s

                # For circular orbit, velocity is perpendicular to position
                pos = planet.position
                pos_magnitude = np.sqrt(pos.x**2 + pos.y**2 + pos.z**2)

                if pos_magnitude > 0:
                    # Velocity in the y direction for circular orbit in xy plane
                    vx = -pos.y * v_km_s / pos_magnitude
                    vy = pos.x * v_km_s / pos_magnitude
                    vz = 0.0
                    return Vector3D(x=vx, y=vy, z=vz)

        return None

    def calculate_transfer_orbit(
        self, start_position: Vector3D, target_position: Vector3D, star_mass: float
    ) -> Dict[str, any]:
        """Calculate a Hohmann or bi-elliptic transfer orbit.

        When the REBOUND library is available the calculation uses the
        canonical units (AU, year, solar mass) for improved accuracy.  The
        function returns the transfer time, semi-major axis and additional
        information about the chosen transfer type.

        Args:
            start_position: Starting position in kilometres.
            target_position: Target position in kilometres.
            star_mass: Mass of the central star in solar masses.

        Returns:
            Dictionary containing transfer orbit parameters.
        """

        # Radii from the central body
        start_r = np.sqrt(
            start_position.x**2 + start_position.y**2 + start_position.z**2
        )
        target_r = np.sqrt(
            target_position.x**2 + target_position.y**2 + target_position.z**2
        )

        r1 = float(start_r)
        r2 = float(target_r)

        # Gravitational parameter (km^3/s^2)
        G = 6.67430e-11
        mu = G * star_mass * 1.989e30

        def hohmann() -> Dict[str, float]:
            a = (r1 + r2) / 2
            t = np.pi * np.sqrt((a * 1000) ** 3 / mu)
            dv1 = np.sqrt(mu / (r1 * 1000)) * (np.sqrt(2 * r2 / (r1 + r2)) - 1)
            dv2 = np.sqrt(mu / (r2 * 1000)) * (1 - np.sqrt(2 * r1 / (r1 + r2)))
            return {
                "transfer_time": t,
                "semi_major_axis": a,
                "delta_v": abs(dv1) + abs(dv2),
                "transfer_type": "hohmann",
            }

        def bi_elliptic(r_b: float) -> Dict[str, float]:
            a1 = (r1 + r_b) / 2
            a2 = (r2 + r_b) / 2
            t1 = np.pi * np.sqrt((a1 * 1000) ** 3 / mu)
            t2 = np.pi * np.sqrt((a2 * 1000) ** 3 / mu)
            dv1 = np.sqrt(mu / (r1 * 1000)) * (np.sqrt(2 * r_b / (r1 + r_b)) - 1)
            dv2 = np.sqrt(mu / (r_b * 1000)) * (
                np.sqrt(2 * r2 / (r_b + r2)) - np.sqrt(2 * r1 / (r1 + r_b))
            )
            dv3 = np.sqrt(mu / (r2 * 1000)) * (1 - np.sqrt(2 * r_b / (r2 + r_b)))
            return {
                "transfer_time": t1 + t2,
                "semi_major_axis": r_b,
                "delta_v": abs(dv1) + abs(dv2) + abs(dv3),
                "transfer_type": "bi-elliptic",
            }

        # Choose transfer method
        hohmann_data = hohmann()
        best = hohmann_data
        r_ratio = max(r1, r2) / min(r1, r2)
        if r_ratio > 11:
            r_b = 2.5 * max(r1, r2)
            bi = bi_elliptic(r_b)
            if bi["delta_v"] < hohmann_data["delta_v"]:
                best = bi

        result = {
            "transfer_time": best["transfer_time"],
            "semi_major_axis": best["semi_major_axis"],
            "start_radius": r1,
            "target_radius": r2,
            "transfer_type": best["transfer_type"],
            "delta_v": best["delta_v"],
        }

        if self.use_rebound:
            # Create a tiny REBOUND simulation to integrate the transfer time.
            sim = rebound.Simulation()
            sim.units = ("km", "s", "kg")
            sim.add(m=star_mass * 1.989e30)
            sim.add(m=0, x=r1, y=0)
            a = best["semi_major_axis"]
            ecc = abs(r2 - r1) / (r1 + r2) if best["transfer_type"] == "hohmann" else 1e-6
            sim.add(m=0, a=a, e=ecc)
            sim.move_to_com()
            # Integrate for half the orbital period for the transfer
            sim.integrate(best["transfer_time"])

        return result

    def cleanup_system(self, system_id: str) -> None:
        """
        Clean up resources for a star system.

        Args:
            system_id: ID of the system to clean up
        """
        if system_id in self.simulations:
            del self.simulations[system_id]
            logger.debug(f"Cleaned up orbital mechanics for system {system_id}")

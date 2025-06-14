import pytest

from pyaurora4x.engine.star_system import StarSystemGenerator
from pyaurora4x.core.models import StarSystem


class TestStarSystemGenerator:
    """Tests for the star system generator."""

    def test_deterministic_generation(self):
        generator1 = StarSystemGenerator(seed=42)
        system1 = generator1.generate_system("sys")

        generator2 = StarSystemGenerator(seed=42)
        system2 = generator2.generate_system("sys")

        assert system1.model_dump() == system2.model_dump()

    def test_planet_parameters_and_unique_ids(self):
        generator = StarSystemGenerator(seed=123)
        system = generator.generate_system("sys")

        planet_ids = [p.id for p in system.planets]
        assert len(planet_ids) == len(set(planet_ids))

        for planet in system.planets:
            assert planet.mass > 0
            assert planet.radius > 0
            assert planet.orbital_distance > 0
            assert planet.orbital_period > 0
            assert 0.0 <= planet.eccentricity <= 0.3

    def test_habitable_zone_calculation(self):
        generator = StarSystemGenerator()
        inner, outer = generator._calculate_habitable_zone(1.0)
        assert inner == pytest.approx(0.95)
        assert outer == pytest.approx(1.37)

        inner2, outer2 = generator._calculate_habitable_zone(4.0)
        assert inner2 == pytest.approx(1.9)
        assert outer2 == pytest.approx(2.74)

    def test_planet_naming_logic(self):
        generator = StarSystemGenerator()
        assert generator._generate_planet_name(0) == "Planet I"
        assert generator._generate_planet_name(5) == "Planet VI"
        assert generator._generate_planet_name(9) == "Planet X"
        assert generator._generate_planet_name(10) == "Planet 11"

    def test_asteroid_belt_generation_and_serialization(self):
        generator = StarSystemGenerator(seed=99)
        systems = [generator.generate_system(f"sys{i}") for i in range(5)]

        assert any(s.asteroid_belts for s in systems)

        for system in systems:
            data = system.model_dump()
            recreated = StarSystem.model_validate(data)
            assert recreated.asteroid_belts == system.asteroid_belts

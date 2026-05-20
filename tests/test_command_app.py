"""Tests for the command-dashboard Textual app helpers."""

from __future__ import annotations

from types import SimpleNamespace

from pyaurora4x.core.enums import PlanetType, StarType
from pyaurora4x.core.models import AsteroidBelt, Fleet, Planet, StarSystem, Vector3D
from pyaurora4x.ui.command_app import (
    _current_systems,
    _focus_items,
    _format_duration,
    _format_eta,
    _format_number,
    _planet_style,
    _resource_rows,
    _system_coord,
)


def _make_planet(name: str = "Arcadia") -> Planet:
    return Planet(
        id=f"planet-{name.lower()}",
        name=name,
        planet_type=PlanetType.TERRESTRIAL,
        mass=1.0,
        radius=1.0,
        surface_temperature=288.0,
        orbital_distance=1.0,
        orbital_period=1.0,
        position=Vector3D(),
    )


def _make_system(system_id: str = "alpha", name: str = "Alpha") -> StarSystem:
    return StarSystem(
        id=system_id,
        name=name,
        star_type=StarType.G_DWARF,
        star_mass=1.0,
        star_luminosity=1.0,
        planets=[_make_planet()],
        asteroid_belts=[AsteroidBelt(distance=2.0, width=0.25)],
    )


def test_terminal_number_and_duration_formatting() -> None:
    assert _format_number(42.0) == "42"
    assert _format_number(1_500.0) == "1.5k"
    assert _format_number(2_500_000.0) == "2.5m"
    assert _format_number(12.25) == "12.2"

    assert _format_duration(-1) == "--"
    assert _format_duration(30) == "30s"
    assert _format_duration(90) == "1.5m"
    assert _format_duration(7_200) == "2.0h"
    assert _format_duration(172_800) == "2.0d"

    assert _format_eta(amount=100.0, capacity=160.0, rate=1.0) == "1.0m"
    assert _format_eta(amount=160.0, capacity=160.0, rate=1.0) == "--"
    assert _format_eta(amount=100.0, capacity=160.0, rate=0.0) == "--"


def test_system_coord_is_stable_and_placeholder_safe() -> None:
    system = _make_system(system_id="stable-system-id")

    assert _system_coord(None) == "SY-0000 C000"
    assert _system_coord(system) == _system_coord(system)
    assert _system_coord(system).startswith("SY-")
    assert " C" in _system_coord(system)


def test_current_systems_sort_by_name() -> None:
    beta = _make_system(system_id="beta", name="Beta")
    alpha = _make_system(system_id="alpha", name="Alpha")
    simulation = SimpleNamespace(star_systems={beta.id: beta, alpha.id: alpha})

    assert [system.name for system in _current_systems(simulation)] == [
        "Alpha",
        "Beta",
    ]


def test_planet_style_uses_single_width_glyphs() -> None:
    terrestrial = _make_planet("Terra")
    gas = _make_planet("Jovia")
    gas.planet_type = PlanetType.GAS_GIANT
    ice = _make_planet("Cryos")
    ice.planet_type = PlanetType.ICE_GIANT

    assert _planet_style(terrestrial) == ("T", "green")
    assert _planet_style(gas) == ("G", "yellow")
    assert _planet_style(ice) == ("I", "cyan")


def test_focus_items_include_system_bodies_and_fleet_color() -> None:
    system = _make_system()
    player_fleet = Fleet(
        id="player-fleet",
        name="First Fleet",
        empire_id="player",
        system_id=system.id,
        position=Vector3D(),
    )
    hostile_fleet = Fleet(
        id="hostile-fleet",
        name="Raiders",
        empire_id="ai-1",
        system_id=system.id,
        position=Vector3D(),
    )

    items = _focus_items(system, [player_fleet, hostile_fleet])

    assert [item.kind for item in items] == [
        "star",
        "planet",
        "belt",
        "fleet",
        "fleet",
    ]
    assert items[0].glyph == "*"
    assert items[1].glyph == "T"
    assert items[2].glyph == "A"
    assert items[3].color == "magenta"
    assert items[4].color == "red"
    assert _focus_items(None, []) == []


def test_resource_rows_merge_empire_income_and_colony_production() -> None:
    empire = SimpleNamespace(
        resources={"minerals": 1_000.0, "fuel": 250.0},
        income={"minerals": 25.0},
        colonies=["colony-1"],
    )
    colony = SimpleNamespace(production={"fuel": 10.0, "research": 2.0})

    class FakeSimulation:
        def get_player_empire(self):
            return empire

        def get_colony(self, colony_id: str):
            return {"colony-1": colony}.get(colony_id)

    rows = _resource_rows(FakeSimulation())

    assert [row.name for row in rows] == ["Minerals", "Fuel"]
    assert rows[0].amount == 1_000.0
    assert rows[0].rate == 25.0
    assert rows[1].amount == 250.0
    assert rows[1].rate == 10.0
    assert rows[0].capacity >= rows[0].amount

"""
Dense command-dashboard Textual app for PyAurora 4X.

This alternate app presents the simulation in a single cockpit-like terminal view:
resources on the left, star map in the center, command options on the right, and
selected object details along the bottom.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import math
import random
from typing import Any, Protocol

from rich.markup import escape
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static

from pyaurora4x.core.models import AsteroidBelt, Fleet, Planet, StarSystem, Vector3D
from pyaurora4x.data.save_manager import SaveManager
from pyaurora4x.engine.simulation import GameSimulation

AU_IN_KM = 149_597_870.7
FocusableBody = StarSystem | Planet | AsteroidBelt | Fleet


class EmpireDisplay(Protocol):
    """Read-only empire surface needed by the command dashboard."""

    @property
    def id(self) -> str: ...

    @property
    def name(self) -> str: ...

    @property
    def resources(self) -> Mapping[str, float]: ...

    @property
    def income(self) -> Mapping[str, float]: ...

    @property
    def colonies(self) -> Sequence[str]: ...

    @property
    def fleets(self) -> Sequence[str]: ...

    @property
    def government_type(self) -> str: ...

    @property
    def culture(self) -> str: ...

    @property
    def research_points(self) -> float: ...


class ColonyDisplay(Protocol):
    """Read-only colony surface needed by the command dashboard."""

    @property
    def id(self) -> str: ...

    @property
    def name(self) -> str: ...

    @property
    def construction_queue(self) -> Sequence[str]: ...

    @property
    def production(self) -> Mapping[str, float]: ...

    @property
    def population(self) -> int: ...

    @property
    def power_generation(self) -> float: ...

    @property
    def power_consumption(self) -> float: ...

    @property
    def efficiency(self) -> float: ...


class SimulationDisplay(Protocol):
    """Read-only simulation surface consumed by display helpers."""

    @property
    def current_time(self) -> float: ...

    @property
    def is_paused(self) -> bool: ...

    @property
    def star_systems(self) -> Mapping[str, StarSystem]: ...

    @property
    def fleets(self) -> Mapping[str, Fleet]: ...

    def get_player_empire(self) -> EmpireDisplay | None: ...

    def get_colony(self, colony_id: str) -> ColonyDisplay | None: ...

    def get_fleet(self, fleet_id: str) -> Fleet | None: ...


@dataclass(slots=True)
class FocusItem:
    """A star-map object that can be selected in the command dashboard."""

    kind: str
    label: str
    body: FocusableBody
    glyph: str
    color: str


@dataclass(slots=True)
class ResourceRow:
    """Display-ready resource information."""

    name: str
    amount: float
    capacity: float
    rate: float
    color: str


def _enum_value(value: object) -> str:
    """Return a clean display value for enums and plain strings."""
    enum_value = getattr(value, "value", value)
    return str(enum_value)


def _format_number(value: float) -> str:
    """Format large game numbers in a compact terminal-friendly form."""
    abs_value = abs(value)
    if abs_value >= 1_000_000:
        return f"{value / 1_000_000:.1f}m"
    if abs_value >= 1_000:
        return f"{value / 1_000:.1f}k"
    if value == int(value):
        return str(int(value))
    return f"{value:.1f}"


def _format_duration(seconds: float) -> str:
    """Format elapsed or remaining game time."""
    if seconds < 0:
        return "--"
    if seconds < 60:
        return f"{seconds:.0f}s"
    if seconds < 3600:
        return f"{seconds / 60:.1f}m"
    if seconds < 86400:
        return f"{seconds / 3600:.1f}h"
    if seconds < 365.25 * 86400:
        return f"{seconds / 86400:.1f}d"
    return f"{seconds / (365.25 * 86400):.2f}y"


def _format_eta(amount: float, capacity: float, rate: float) -> str:
    """Estimate time until a resource reaches capacity."""
    if rate <= 0 or capacity <= amount:
        return "--"
    return _format_duration((capacity - amount) / rate)


def _system_coord(system: StarSystem | None) -> str:
    """Create a stable pseudo-coordinate for a star system."""
    if system is None:
        return "SY-0000 C000"

    digest = hashlib.sha1(system.id.encode("utf-8")).hexdigest().upper()
    return f"SY-{digest[:4]} C{digest[4:7]}"


def _player_empire(simulation: SimulationDisplay) -> EmpireDisplay | None:
    """Return the player empire, tolerating partially initialized simulations."""
    try:
        return simulation.get_player_empire()
    except Exception:
        return None


def _player_colonies(simulation: SimulationDisplay) -> list[ColonyDisplay]:
    """Return colonies controlled by the player empire."""
    empire = _player_empire(simulation)
    if empire is None:
        return []

    colonies: list[ColonyDisplay] = []
    for colony_id in empire.colonies:
        colony = simulation.get_colony(colony_id)
        if colony is not None:
            colonies.append(colony)
    return colonies


def _resource_rows(simulation: SimulationDisplay) -> list[ResourceRow]:
    """Build display rows from empire resources, income, and colony production."""
    empire = _player_empire(simulation)
    colonies = _player_colonies(simulation)

    if empire is None:
        return []

    resource_keys = list(empire.resources.keys())
    if not resource_keys:
        resource_keys = ["minerals", "fuel", "research", "wealth"]

    production_totals: dict[str, float] = {}
    for colony in colonies:
        for resource_name, value in colony.production.items():
            production_totals[resource_name] = production_totals.get(resource_name, 0.0) + value

    palette = ["red", "yellow", "cyan", "magenta", "green", "blue"]
    rows: list[ResourceRow] = []
    for index, resource_name in enumerate(resource_keys[:6]):
        amount = float(empire.resources.get(resource_name, 0.0))
        rate = float(empire.income.get(resource_name, production_totals.get(resource_name, 0.0)))
        capacity = max(1_000.0, amount * 1.5, rate * 24.0)
        label = resource_name.replace("_", " ").title()
        rows.append(
            ResourceRow(
                name=label,
                amount=amount,
                capacity=capacity,
                rate=rate,
                color=palette[index % len(palette)],
            )
        )

    return rows


def _current_systems(simulation: SimulationDisplay) -> list[StarSystem]:
    """Return star systems in a stable order."""
    return sorted(simulation.star_systems.values(), key=lambda system: system.name)


def _planet_style(planet: Planet) -> tuple[str, str]:
    """Return a single-width glyph and Rich color for a planet."""
    planet_type = _enum_value(planet.planet_type).lower()
    if "gas" in planet_type:
        return "G", "yellow"
    if "ice" in planet_type:
        return "I", "cyan"
    if "terrestrial" in planet_type:
        return "T", "green"
    return "P", "magenta"


def _focus_items(system: StarSystem | None, fleets: Sequence[Fleet]) -> list[FocusItem]:
    """Create the selectable object list for the current system."""
    if system is None:
        return []

    items = [FocusItem("star", system.name, system, "*", "yellow")]

    for planet in system.planets:
        glyph, color = _planet_style(planet)
        items.append(FocusItem("planet", planet.name, planet, glyph, color))

    for index, belt in enumerate(system.asteroid_belts, start=1):
        items.append(FocusItem("belt", f"Asteroid Belt {index}", belt, "A", "dim"))

    for fleet in fleets:
        color = "magenta" if fleet.empire_id == "player" else "red"
        items.append(FocusItem("fleet", fleet.name, fleet, "F", color))

    return items


def _system_fleets(simulation: SimulationDisplay, system: StarSystem | None) -> list[Fleet]:
    """Return fleets currently located in a star system."""
    if system is None:
        return []
    return [fleet for fleet in simulation.fleets.values() if fleet.system_id == system.id]


def _safe_percent(value: float) -> str:
    """Format a 0 to 100-ish value as a percent."""
    return f"{value:.0f}%"


def _position_to_au(position: Vector3D) -> tuple[float, float]:
    """Convert a model-space position from kilometers to AU."""
    return position.x / AU_IN_KM, position.y / AU_IN_KM


class CommandTopBar(Static):
    """Top status strip."""

    def update_from_simulation(
        self,
        simulation: SimulationDisplay,
        system: StarSystem | None,
    ) -> None:
        empire = _player_empire(simulation)
        colonies = _player_colonies(simulation)
        status = "paused" if simulation.is_paused else "running"
        empire_name = escape(empire.name) if empire else "Unclaimed Command"
        system_name = escape(system.name) if system else "No System"
        coord = _system_coord(system)
        build_status = "idle"

        if colonies:
            queue_size = sum(len(colony.construction_queue) for colony in colonies)
            build_status = f"busy ({queue_size} queued)" if queue_size else "idle"

        self.update(
            "[bold magenta]PYAURORA 4X // COMMAND LINE[/]\n"
            f"[magenta]{empire_name}[/] | {system_name} > {coord} | "
            f"Colonies: {len(colonies)} | Fleets: {len(simulation.fleets)} | "
            f"Build: {build_status} | Clock: {_format_duration(simulation.current_time)} | "
            f"State: {status}"
        )


class CommandResourcePanel(Static):
    """Left resource and asset panel."""

    def update_from_simulation(self, simulation: SimulationDisplay) -> None:
        empire = _player_empire(simulation)
        colonies = _player_colonies(simulation)
        rows = _resource_rows(simulation)

        lines: list[str] = [
            "[bold magenta]RESOURCES[/]",
            "",
            "[dim]Resource          Now     Cap       /t    ETA[/]",
        ]

        if rows:
            for row in rows:
                lines.append(
                    f"[{row.color}]{row.name:<13}[/] "
                    f"{_format_number(row.amount):>6} "
                    f"{_format_number(row.capacity):>7} "
                    f"[green]↑{_format_number(row.rate):>5}[/] "
                    f"{_format_eta(row.amount, row.capacity, row.rate):>6}"
                )
        else:
            lines.append("[dim](no empire resource ledger)[/]")

        lines.extend(["", "[bold magenta]Building[/]"])
        if colonies:
            queued = False
            for colony in colonies:
                for project_id in colony.construction_queue[:3]:
                    lines.append(f"[green]{escape(colony.name):<18}[/] | {escape(project_id)}")
                    queued = True
            if not queued:
                lines.append("[dim](none)[/]")
        else:
            lines.append("[dim](none)[/]")

        lines.extend(["", "[bold magenta]Colonies[/]"])
        if colonies:
            for colony in colonies[:8]:
                power_delta = colony.power_generation - colony.power_consumption
                lines.append(
                    f"• {escape(colony.name):<18} "
                    f"Pop {_format_number(float(colony.population)):>6} "
                    f"Eff {_safe_percent(colony.efficiency * 100)} "
                    f"Pow {power_delta:+.1f}"
                )
        else:
            lines.append("[dim](none)[/]")

        lines.extend(["", "[bold magenta]Fleets[/]"])
        if empire and empire.fleets:
            for fleet_id in empire.fleets[:8]:
                fleet = simulation.get_fleet(fleet_id)
                if fleet is None:
                    continue
                lines.append(
                    f"• {escape(fleet.name):<18} "
                    f"Ships {len(fleet.ships):>2} "
                    f"Fuel {_safe_percent(fleet.fuel_remaining)}"
                )
        else:
            lines.append("[dim](none)[/]")

        lines.extend(["", "[bold magenta]Empire[/]"])
        if empire:
            lines.append(f"Government : {escape(empire.government_type)}")
            lines.append(f"Culture    : {escape(empire.culture)}")
            lines.append(f"Research   : {_format_number(empire.research_points)} pts")
        else:
            lines.append("[dim](no player empire)[/]")

        self.update("\n".join(lines))


class CommandFilterBar(Static):
    """Center filter and key hint strip."""

    def update_from_simulation(
        self,
        simulation: SimulationDisplay,
        system: StarSystem | None,
        focus_index: int,
        focus_count: int,
    ) -> None:
        system_label = escape(system.name) if system else "No System"
        self.update(
            "[bold magenta]STAR MAP[/]\n"
            "[N] Next System  [B] Back System  [Up/Down] Select Object  "
            "[A] Advance 30s  [Y] Advance 1y  [Space] Pause  [S] Save\n"
            "[F] Faction: All  [C] Culture: All  [T] Alignment: All  "
            f"System: {system_label}  Object: {focus_index + 1}/{max(focus_count, 1)}"
        )


class CommandStarMap(Static):
    """Central spatial star-map widget."""

    width_cells = 78
    height_cells = 22

    def update_from_simulation(
        self,
        simulation: SimulationDisplay,
        system: StarSystem | None,
        selected: FocusItem | None,
    ) -> None:
        if system is None:
            self.update("[dim]No star system loaded.[/]")
            return

        fleets = _system_fleets(simulation, system)
        focus_items = _focus_items(system, fleets)
        selected_body = selected.body if selected else None
        center_x = self.width_cells // 2
        center_y = self.height_cells // 2
        grid = [[" " for _ in range(self.width_cells)] for _ in range(self.height_cells)]
        styles = [["" for _ in range(self.width_cells)] for _ in range(self.height_cells)]

        def put(x: int, y: int, glyph: str, style: str = "", is_selected: bool = False) -> None:
            if 0 <= x < self.width_cells and 0 <= y < self.height_cells:
                grid[y][x] = glyph[:1]
                styles[y][x] = f"reverse {style}" if is_selected else style

        seed = int(hashlib.sha1(system.id.encode("utf-8")).hexdigest()[:8], 16)
        rng = random.Random(seed)
        for _ in range(95):
            x = rng.randrange(self.width_cells)
            y = rng.randrange(self.height_cells)
            if grid[y][x] == " ":
                put(x, y, ".", rng.choice(["dim", "red", "yellow", "cyan", "magenta", "green"]))

        max_au = 1.0
        if system.planets:
            max_au = max(max_au, max(planet.orbital_distance for planet in system.planets))
        if system.asteroid_belts:
            max_au = max(max_au, max(belt.distance + belt.width for belt in system.asteroid_belts))
        max_au = max(max_au, system.habitable_zone_outer)

        x_scale = (self.width_cells / 2 - 4) / max_au
        y_scale = (self.height_cells / 2 - 2) / max_au

        def project_au(x_au: float, y_au: float) -> tuple[int, int]:
            return int(center_x + x_au * x_scale), int(center_y + y_au * y_scale * 0.55)

        def object_position(body: FocusableBody, fallback_angle: float, distance_au: float) -> tuple[int, int]:
            position = getattr(body, "position", None)
            if isinstance(position, Vector3D) and position.magnitude() > 0:
                x_au, y_au = _position_to_au(position)
                return project_au(x_au, y_au)
            return project_au(math.cos(fallback_angle) * distance_au, math.sin(fallback_angle) * distance_au)

        for planet in system.planets:
            orbit_rx = max(1.0, planet.orbital_distance * x_scale)
            orbit_ry = max(1.0, planet.orbital_distance * y_scale * 0.55)
            point_count = max(20, min(140, int(orbit_rx * 5)))
            for point_index in range(point_count):
                angle = 2 * math.pi * point_index / point_count
                x = int(center_x + math.cos(angle) * orbit_rx)
                y = int(center_y + math.sin(angle) * orbit_ry)
                if 0 <= x < self.width_cells and 0 <= y < self.height_cells and grid[y][x] == " ":
                    put(x, y, "·", "dim")

        for belt in system.asteroid_belts:
            radius = belt.distance
            point_count = max(28, min(160, int(radius * x_scale * 5)))
            for point_index in range(point_count):
                if point_index % 2 == 0:
                    continue
                angle = 2 * math.pi * point_index / point_count
                x, y = project_au(math.cos(angle) * radius, math.sin(angle) * radius)
                if 0 <= x < self.width_cells and 0 <= y < self.height_cells and grid[y][x] == " ":
                    put(x, y, ":", "dim")

        put(center_x, center_y, "*", "yellow", selected_body is system)

        for index, planet in enumerate(system.planets):
            angle = 2 * math.pi * index / max(len(system.planets), 1)
            x, y = object_position(planet, angle, planet.orbital_distance)
            glyph, color = _planet_style(planet)
            put(x, y, glyph, color, selected_body is planet)

        for index, fleet in enumerate(fleets):
            angle = 2 * math.pi * (index + 0.5) / max(len(fleets), 1)
            x, y = object_position(fleet, angle, max_au * 0.75)
            color = "magenta" if fleet.empire_id == "player" else "red"
            put(x, y, "F", color, selected_body is fleet)

        for item in focus_items:
            if item.kind != "belt" or not isinstance(item.body, AsteroidBelt):
                continue
            belt = item.body
            x, y = project_au(belt.distance, 0.0)
            put(x, y, "A", "dim", selected_body is belt)

        rendered_lines: list[str] = []
        for y in range(self.height_cells):
            cells: list[str] = []
            for x in range(self.width_cells):
                glyph = grid[y][x]
                style = styles[y][x]
                if style:
                    cells.append(f"[{style}]{escape(glyph)}[/]")
                else:
                    cells.append(escape(glyph))
            rendered_lines.append("".join(cells))

        self.update("\n".join(rendered_lines))


class CommandDetailPanel(Static):
    """Selected object details."""

    def update_from_simulation(
        self,
        simulation: SimulationDisplay,
        system: StarSystem | None,
        selected: FocusItem | None,
    ) -> None:
        if system is None or selected is None:
            self.update("[bold magenta]SELECTED[/]\n[dim]No selectable object.[/]")
            return

        body = selected.body
        header = f"[bold magenta]SELECTED[/] {escape(selected.kind.upper())}: [{selected.color}]{escape(selected.label)}[/]"

        if selected.kind == "star" and isinstance(body, StarSystem):
            text = (
                f"{header}\n"
                f"Coord     : {_system_coord(system)}\n"
                "Type      : Star System\n"
                f"Star      : {_enum_value(system.star_type)} | Mass {system.star_mass:.2f} M☉ | Lum {system.star_luminosity:.2f} L☉\n"
                f"Bodies    : {len(system.planets)} planets | {len(system.asteroid_belts)} belts | {len(system.jump_points)} jump points\n"
                f"Hab Zone  : {system.habitable_zone_inner:.2f} AU to {system.habitable_zone_outer:.2f} AU"
            )
        elif selected.kind == "planet" and isinstance(body, Planet):
            colony_line = "none"
            if body.colony_id:
                colony = simulation.get_colony(body.colony_id)
                if colony:
                    colony_line = (
                        f"{colony.name} | Pop {_format_number(float(colony.population))} | "
                        f"Eff {_safe_percent(colony.efficiency * 100)}"
                    )
            resources = ", ".join(
                f"{name}:{_format_number(float(value))}"
                for name, value in body.mineral_resources.items()
            ) or "unknown"
            text = (
                f"{header}\n"
                f"Coord     : {_system_coord(system)} / Orbit {body.orbital_distance:.2f} AU\n"
                f"Type      : {_enum_value(body.planet_type)} | Grav {body.gravity:.2f}g | Temp {body.surface_temperature:.0f}K\n"
                f"Hab       : {_safe_percent(body.habitability)} | Surveyed: {body.is_surveyed}\n"
                f"Colony    : {escape(colony_line)}\n"
                f"Resources : {escape(resources)}"
            )
        elif selected.kind == "fleet" and isinstance(body, Fleet):
            text = (
                f"{header}\n"
                f"Coord     : {_system_coord(system)}\n"
                f"Status    : {_enum_value(body.status)} | Ships {len(body.ships)} | Fuel {_safe_percent(body.fuel_remaining)}\n"
                f"Mass      : {_format_number(body.total_mass)} | Max Speed {_format_number(body.max_speed)}\n"
                f"Orders    : {escape(', '.join(body.current_orders) if body.current_orders else 'none')}\n"
                f"ETA       : {_format_duration(body.estimated_arrival or -1)}"
            )
        elif selected.kind == "belt" and isinstance(body, AsteroidBelt):
            text = (
                f"{header}\n"
                f"Coord     : {_system_coord(system)} / Radius {body.distance:.2f} AU\n"
                "Type      : Asteroid Belt\n"
                f"Width     : {body.width:.2f} AU\n"
                "Signal    : probable minerals and volatiles\n"
                "Orders    : survey, prospect, patrol"
            )
        else:
            text = f"{header}\n[dim]No detail renderer for this object type.[/]"

        self.update(text)


class CommandOptionsPanel(Static):
    """Right command/options panel."""

    def update_from_simulation(self, simulation: SimulationDisplay, system: StarSystem | None) -> None:
        system_name = escape(system.name) if system else "No System"
        self.update(
            "[bold magenta]OPTIONS[/]\n\n"
            "[bold]COLONY[/]\n"
            "[1] Infrastructure\n"
            "[2] Shipyards\n"
            "[3] Logistics\n\n"
            "[bold]EMPIRE[/]\n"
            "[4] Colonies\n"
            "[5] Factions\n"
            "[6] Economy\n\n"
            "[bold]MILITARY[/]\n"
            "[7] Fleets\n"
            "[8] Garrisons\n"
            "[9] Combat Logs\n"
            "[T] Tactics\n\n"
            "[bold]INTELLIGENCE[/]\n"
            f"[reverse magenta][M] Star Map[/] {system_name}\n"
            "[C] Codex\n"
            "[N] Next System\n"
            "[B] Previous System\n"
            "[Up/Down] Select\n\n"
            "[bold]SYSTEM[/]\n"
            "[A] Advance 30s\n"
            "[Y] Advance 1y\n"
            "[Space] Pause/Resume\n"
            "[S] Save\n"
            "[Q] Quit"
        )


class CommandBottomBar(Static):
    """Bottom ledger/status strip."""

    def update_from_simulation(self, simulation: SimulationDisplay) -> None:
        rows = _resource_rows(simulation)
        totals = " | ".join(
            f"[{row.color}]{escape(row.name[:3])} {_format_number(row.amount)}[/]"
            for row in rows[:4]
        ) or "[dim]no ledger[/]"
        per_tick = " | ".join(
            f"[{row.color}]{escape(row.name[:3])} {_format_number(row.rate)}/t[/]"
            for row in rows[:4]
        ) or "[dim]no income[/]"

        self.update(
            f"[magenta]< COMMANDS[/]      [bold magenta]TOTAL[/] {totals}      "
            f"[bold magenta]S/D[/] {per_tick}      [dim]SPU >[/]"
        )


class CommandDashboard(Container):
    """Composite widget for the whole command dashboard."""

    def compose(self) -> ComposeResult:
        yield CommandTopBar(classes="command-top")
        with Horizontal(classes="command-main"):
            yield CommandResourcePanel(classes="command-left")
            with Vertical(classes="command-center"):
                yield CommandFilterBar(classes="command-filter")
                yield CommandStarMap(classes="command-map")
                yield CommandDetailPanel(classes="command-detail")
            yield CommandOptionsPanel(classes="command-right")
        yield CommandBottomBar(classes="command-bottom")

    def update_from_simulation(
        self,
        simulation: SimulationDisplay,
        system: StarSystem | None,
        selected: FocusItem | None,
        focus_index: int,
        focus_count: int,
    ) -> None:
        self.query_one(CommandTopBar).update_from_simulation(simulation, system)
        self.query_one(CommandResourcePanel).update_from_simulation(simulation)
        self.query_one(CommandFilterBar).update_from_simulation(
            simulation,
            system,
            focus_index,
            focus_count,
        )
        self.query_one(CommandStarMap).update_from_simulation(simulation, system, selected)
        self.query_one(CommandDetailPanel).update_from_simulation(simulation, system, selected)
        self.query_one(CommandOptionsPanel).update_from_simulation(simulation, system)
        self.query_one(CommandBottomBar).update_from_simulation(simulation)


class PyAuroraCommandApp(App[None]):
    """Single-screen command-line dashboard for PyAurora 4X."""

    CSS = """
    Screen {
        background: #101014;
        color: #d8d0d8;
    }

    CommandDashboard {
        height: 100%;
        background: #101014;
    }

    .command-top {
        height: 4;
        padding: 0 1;
        border: solid #7e4a8e;
        background: #17151c;
    }

    .command-main {
        height: 1fr;
    }

    .command-left {
        width: 25%;
        min-width: 42;
        padding: 1;
        border-right: solid #666666;
    }

    .command-center {
        width: 1fr;
    }

    .command-filter {
        height: 4;
        padding: 0 1;
        border-bottom: solid #666666;
    }

    .command-map {
        height: 1fr;
        padding: 1;
        overflow: hidden;
    }

    .command-detail {
        height: 8;
        padding: 0 1;
        border-top: solid #666666;
    }

    .command-right {
        width: 19%;
        min-width: 30;
        padding: 1;
        border-left: solid #666666;
    }

    .command-bottom {
        height: 2;
        padding: 0 1;
        border-top: solid #666666;
        border-bottom: solid #7e4a8e;
        background: #17151c;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
        Binding("n", "next_system", "Next System"),
        Binding("b", "previous_system", "Previous System"),
        Binding("down", "next_focus", "Next Object"),
        Binding("up", "previous_focus", "Previous Object"),
        Binding("a", "advance_time", "Advance 30s"),
        Binding("y", "advance_one_year", "Advance 1y"),
        Binding("space", "toggle_pause", "Pause/Resume"),
        Binding("s", "save_game", "Save Game"),
        Binding("h", "show_help", "Help"),
    ]

    def __init__(
        self,
        new_game_systems: int = 3,
        new_game_empires: int = 2,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.simulation: GameSimulation | None = None
        self.save_manager = SaveManager()
        self.load_file: str | None = None
        self.load_data: dict[str, Any] | None = None
        self.new_game_systems = new_game_systems
        self.new_game_empires = new_game_empires
        self.system_index = 0
        self.focus_index = 0

    def compose(self) -> ComposeResult:
        yield CommandDashboard(id="command_dashboard")

    def on_mount(self) -> None:
        self.title = "PyAurora 4X"
        self.sub_title = "Command Line Dashboard"
        self.set_interval(1.0, self._on_tick)

    def on_ready(self) -> None:
        if self.load_data is not None:
            self.load_game_data(self.load_data)
        else:
            self.start_new_game()

    def start_new_game(self) -> None:
        self.simulation = GameSimulation()
        self.simulation.initialize_new_game(
            num_systems=self.new_game_systems,
            num_empires=self.new_game_empires,
        )
        self.system_index = 0
        self.focus_index = 0
        self.refresh_dashboard()
        self.notify("New command session started.")

    def load_game_data(self, game_data: dict[str, Any]) -> None:
        self.simulation = GameSimulation()
        self.simulation.load_game_state(game_data)
        self.system_index = 0
        self.focus_index = 0
        self.refresh_dashboard()
        self.notify("Game loaded into command dashboard.")

    def _on_tick(self) -> None:
        if self.simulation is None:
            return
        self.refresh_dashboard()

    def _current_system(self) -> StarSystem | None:
        if self.simulation is None:
            return None
        systems = _current_systems(self.simulation)
        if not systems:
            return None
        self.system_index %= len(systems)
        return systems[self.system_index]

    def _current_focus_items(self) -> list[FocusItem]:
        if self.simulation is None:
            return []
        system = self._current_system()
        return _focus_items(system, _system_fleets(self.simulation, system))

    def _current_focus_item(self) -> FocusItem | None:
        items = self._current_focus_items()
        if not items:
            return None
        self.focus_index %= len(items)
        return items[self.focus_index]

    def refresh_dashboard(self) -> None:
        if self.simulation is None:
            return

        system = self._current_system()
        items = self._current_focus_items()
        selected = self._current_focus_item()
        dashboard = self.query_one(CommandDashboard)
        dashboard.update_from_simulation(
            self.simulation,
            system,
            selected,
            self.focus_index,
            len(items),
        )

    def action_next_system(self) -> None:
        if self.simulation is None:
            return
        systems = _current_systems(self.simulation)
        if not systems:
            return
        self.system_index = (self.system_index + 1) % len(systems)
        self.focus_index = 0
        self.refresh_dashboard()

    def action_previous_system(self) -> None:
        if self.simulation is None:
            return
        systems = _current_systems(self.simulation)
        if not systems:
            return
        self.system_index = (self.system_index - 1) % len(systems)
        self.focus_index = 0
        self.refresh_dashboard()

    def action_next_focus(self) -> None:
        items = self._current_focus_items()
        if not items:
            return
        self.focus_index = (self.focus_index + 1) % len(items)
        self.refresh_dashboard()

    def action_previous_focus(self) -> None:
        items = self._current_focus_items()
        if not items:
            return
        self.focus_index = (self.focus_index - 1) % len(items)
        self.refresh_dashboard()

    def action_advance_time(self) -> None:
        if self.simulation is None:
            return
        self.simulation.advance_time(30)
        self.refresh_dashboard()
        self.notify("Advanced time by 30 seconds.")

    def action_advance_one_year(self) -> None:
        if self.simulation is None:
            return
        self.simulation.advance_time(365.25 * 24 * 3600)
        self.refresh_dashboard()
        self.notify("Advanced time by one year.")

    def action_toggle_pause(self) -> None:
        if self.simulation is None:
            return
        if self.simulation.is_paused:
            self.simulation.resume()
            self.notify("Simulation resumed.")
        else:
            self.simulation.pause()
            self.notify("Simulation paused.")
        self.refresh_dashboard()

    def action_save_game(self) -> None:
        if self.simulation is None:
            return
        save_name = f"command_autosave_{int(self.simulation.current_time)}"
        self.save_manager.save_game(self.simulation.get_game_state(), save_name)
        self.notify(f"Game saved as {save_name}.")

    def action_show_help(self) -> None:
        self.notify(
            "N/B cycle systems, Up/Down selects objects, A advances 30s, Y advances 1y, Space pauses, S saves."
        )

    async def action_quit(self) -> None:
        self.exit()

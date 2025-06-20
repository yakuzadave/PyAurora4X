from pyaurora4x.ui.widgets.fleet_panel import FleetPanel
from pyaurora4x.ui.widgets.planet_select_dialog import PlanetSelectDialog
from pyaurora4x.core.models import (
    Fleet,
    Vector3D,
    Planet,
    StarSystem,
)
from pyaurora4x.core.enums import FleetStatus, PlanetType, StarType
from pyaurora4x.engine.orbital_mechanics import OrbitalMechanics
from textual.widgets._option_list import Option
from textual.widgets import OptionList
from pyaurora4x.ui.widgets.fleet_panel import FleetCommandEvent
from pyaurora4x.core.utils import format_time


class DummyFleetPanel(FleetPanel):
    """FleetPanel with a flexible refresh signature for testing."""

    def refresh(self, *args, **kwargs):  # type: ignore[override]
        pass

    def refresh_fleet_data(self) -> None:  # type: ignore[override]
        pass


def create_fleet(name: str, arrival: float) -> Fleet:
    return Fleet(
        name=name,
        empire_id="emp",
        system_id="sys",
        position=Vector3D(x=0, y=0, z=0),
        destination=Vector3D(x=100, y=0, z=0),
        estimated_arrival=arrival,
        status=FleetStatus.MOVING,
    )


def test_generate_fleet_details_future_eta():
    panel = DummyFleetPanel()
    fleet = create_fleet("Alpha", 1500.0)
    result = panel._generate_fleet_details(fleet, current_time=1000.0)
    assert f"ETA: {format_time(500.0)}" in result


def test_generate_fleet_details_overdue_eta():
    panel = DummyFleetPanel()
    fleet = create_fleet("Beta", 800.0)
    result = panel._generate_fleet_details(fleet, current_time=1000.0)
    assert "ETA: 0.0s" in result


def test_planet_select_dialog_callback():
    selected: list[str] = []
    planet_a = Planet(
        name="A",
        planet_type=PlanetType.TERRESTRIAL,
        mass=1.0,
        radius=1.0,
        surface_temperature=288.0,
        orbital_distance=1.0,
        orbital_period=1.0,
        position=Vector3D(x=1000, y=0, z=0),
    )
    planet_b = Planet(
        name="B",
        planet_type=PlanetType.TERRESTRIAL,
        mass=1.0,
        radius=1.0,
        surface_temperature=288.0,
        orbital_distance=1.5,
        orbital_period=2.0,
        position=Vector3D(x=2000, y=0, z=0),
    )
    dialog = PlanetSelectDialog([planet_a, planet_b], lambda pid: selected.append(pid))
    dialog.remove = lambda: None  # Avoid NoActiveAppError during tests
    option = Option(planet_b.name, id=planet_b.id)
    event = OptionList.OptionSelected(OptionList(), option, 1)
    dialog.on_option_list_option_selected(event)
    assert selected == [planet_b.id]


class DummyApp:
    def __init__(self, simulation):
        self.simulation = simulation


class TestMoveFleet:
    def test_apply_move_selection_updates_fleet(self):
        panel = DummyFleetPanel()
        panel.posted = None
        def post_message(event):
            panel.posted = event
        panel.post_message_no_wait = post_message  # type: ignore

        planet_a = Planet(
            name="A",
            planet_type=PlanetType.TERRESTRIAL,
            mass=1.0,
            radius=1.0,
            surface_temperature=288.0,
            orbital_distance=1.0,
            orbital_period=1.0,
            position=Vector3D(x=1000, y=0, z=0),
        )
        planet_b = Planet(
            name="B",
            planet_type=PlanetType.TERRESTRIAL,
            mass=1.0,
            radius=1.0,
            surface_temperature=288.0,
            orbital_distance=1.5,
            orbital_period=2.0,
            position=Vector3D(x=2000, y=0, z=0),
        )
        system = StarSystem(
            name="Sys",
            star_type=StarType.G_DWARF,
            star_mass=1.0,
            star_luminosity=1.0,
            planets=[planet_a, planet_b],
        )
        fleet = Fleet(
            name="Fleet",
            empire_id="emp",
            system_id=system.id,
            position=planet_a.position.copy(),
        )
        simulation = type(
            "Sim",
            (),
            {
                "star_systems": {system.id: system},
                "orbital_mechanics": OrbitalMechanics(),
                "current_time": 0.0,
            },
        )()

        panel._apply_move_selection(fleet, planet_b, system, simulation)

        assert fleet.destination == planet_b.position
        assert fleet.estimated_arrival and fleet.estimated_arrival > 0
        assert fleet.current_orders and "Transfer to" in fleet.current_orders[-1]
        assert fleet.status == FleetStatus.IN_TRANSIT
        assert isinstance(panel.posted, FleetCommandEvent)
        assert panel.posted.command == "move"
        assert panel.posted.fleet_id == fleet.id

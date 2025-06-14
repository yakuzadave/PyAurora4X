from pyaurora4x.ui.widgets.fleet_panel import FleetPanel
from pyaurora4x.core.models import Fleet, Vector3D
from pyaurora4x.core.enums import FleetStatus
from pyaurora4x.core.utils import format_time


class DummyFleetPanel(FleetPanel):
    """FleetPanel with a flexible refresh signature for testing."""

    def refresh(self, *args, **kwargs):  # type: ignore[override]
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

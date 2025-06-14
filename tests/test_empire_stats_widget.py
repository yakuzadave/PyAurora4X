import types
from pyaurora4x.ui.widgets.empire_stats import EmpireStatsWidget
from pyaurora4x.core.models import Empire
from pyaurora4x.core.utils import format_time


def test_empire_age_calculation(monkeypatch):
    widget = EmpireStatsWidget()
    empire = Empire(
        name="Test", home_system_id="sys", home_planet_id="planet", established_date=100.0
    )
    widget.current_empire = empire
    widget.current_time = 200.0

    captured = {}

    class Dummy:
        def update(self, text: str) -> None:
            captured["text"] = text

    monkeypatch.setattr(widget, "query_one", lambda *args, **kwargs: Dummy())

    widget._update_basic_info()

    expected_age = format_time(100.0)
    assert f"Age: {expected_age}" in captured.get("text", "")

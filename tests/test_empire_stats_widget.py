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


def test_military_section_shows_recent_events(monkeypatch):
    from pyaurora4x.core.events import EventManager, EventPriority, EventCategory, GameEvent, EventHandler

    class DummyHandler(EventHandler):
        def handle(self, event: GameEvent) -> bool:  # pragma: no cover - simple
            return True

    manager = EventManager()
    manager.register_handler(DummyHandler(), EventCategory.FLEET)

    empire = Empire(name="Test", home_system_id="sys", home_planet_id="planet")

    manager.post_event(
        GameEvent(
            id="",
            category=EventCategory.FLEET,
            priority=EventPriority.NORMAL,
            timestamp=1.0,
            title="First Battle",
            description="",
            empire_id=empire.id,
        )
    )
    manager.process_events()

    widget = EmpireStatsWidget(event_manager=manager)
    widget.current_empire = empire

    captured = {}

    class Dummy:
        def update(self, text: str) -> None:
            captured["text"] = text

    monkeypatch.setattr(widget, "query_one", lambda *args, **kwargs: Dummy())

    widget._update_military()

    assert "First Battle" in captured.get("text", "")

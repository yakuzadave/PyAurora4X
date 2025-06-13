import pytest
from pyaurora4x.engine.scheduler import GameScheduler


class TestGameScheduler:
    """Tests for the GameScheduler class."""

    def test_schedule_event_triggers_once(self):
        scheduler = GameScheduler()
        log = []
        scheduler.schedule_event("e1", 10.0, lambda: log.append("e1"))

        triggered = scheduler.process_events(0.0, 15.0)

        assert log == ["e1"]
        assert triggered == ["e1"]
        assert scheduler.get_pending_events_count() == 0
        assert scheduler.last_processed_time == 15.0

    def test_recurring_event_reschedules(self):
        scheduler = GameScheduler()
        log = []
        scheduler.schedule_recurring_event("tick", 5.0, lambda: log.append("t"))

        triggered = scheduler.process_events(0.0, 16.0)

        assert log == ["t", "t", "t"]
        assert triggered == ["tick", "tick", "tick"]
        assert pytest.approx(scheduler.get_next_event_time()) == 20.0

    def test_cancel_recurring_event(self):
        scheduler = GameScheduler()
        log = []
        scheduler.schedule_recurring_event("repeat", 5.0, lambda: log.append("r"))
        scheduler.cancel_event("repeat")

        triggered = scheduler.process_events(0.0, 10.0)

        assert log == []
        assert triggered == []
        assert scheduler.get_pending_events_count() == 0

    def test_process_events_range(self):
        scheduler = GameScheduler()
        log = []
        scheduler.schedule_event("first", 10.0, lambda: log.append("first"))
        scheduler.schedule_event("second", 20.0, lambda: log.append("second"))

        triggered = scheduler.process_events(0.0, 15.0)

        assert log == ["first"]
        assert triggered == ["first"]
        assert scheduler.get_next_event_time() == pytest.approx(20.0)
        assert scheduler.last_processed_time == 15.0

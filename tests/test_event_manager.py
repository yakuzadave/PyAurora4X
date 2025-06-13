"""Tests for the EventManager system."""

from pyaurora4x.core.events import (
    EventManager,
    EventPriority,
    EventCategory,
    GameEvent,
    EventHandler,
)


class RecordingHandler(EventHandler):
    """Simple handler that records handled events."""

    def __init__(self, log):
        self.log = log

    def handle(self, event: GameEvent) -> bool:  # pragma: no cover - trivial
        self.log.append(event.title)
        return True


def test_post_event_sorting():
    manager = EventManager()

    e_low = GameEvent(
        id="",
        category=EventCategory.SYSTEM,
        priority=EventPriority.LOW,
        timestamp=1,
        title="low",
        description="",
    )
    e_high = GameEvent(
        id="",
        category=EventCategory.FLEET,
        priority=EventPriority.HIGH,
        timestamp=2,
        title="high",
        description="",
    )
    e_normal_old = GameEvent(
        id="",
        category=EventCategory.RESEARCH,
        priority=EventPriority.NORMAL,
        timestamp=1,
        title="normal_old",
        description="",
    )
    e_normal_new = GameEvent(
        id="",
        category=EventCategory.RESEARCH,
        priority=EventPriority.NORMAL,
        timestamp=3,
        title="normal_new",
        description="",
    )

    manager.post_event(e_low)
    manager.post_event(e_high)
    manager.post_event(e_normal_old)
    manager.post_event(e_normal_new)

    titles = [e.title for e in manager.event_queue]
    assert titles == ["high", "normal_new", "normal_old", "low"]


def test_create_and_post_event():
    manager = EventManager()
    event = manager.create_and_post_event(
        category=EventCategory.FLEET,
        priority=EventPriority.NORMAL,
        title="created",
        description="desc",
        timestamp=123.0,
        empire_id="emp",
    )

    assert len(manager.event_queue) == 1
    queued = manager.event_queue[0]
    assert queued.id
    assert queued.title == "created"
    assert queued.empire_id == "emp"
    assert event is queued


def test_handler_registration_and_processing():
    manager = EventManager()
    fleet_log = []
    global_log = []

    fleet_handler = RecordingHandler(fleet_log)
    global_handler = RecordingHandler(global_log)

    manager.register_handler(fleet_handler, EventCategory.FLEET)
    manager.register_handler(global_handler)

    fleet_event = GameEvent(
        id="",
        category=EventCategory.FLEET,
        priority=EventPriority.NORMAL,
        timestamp=1,
        title="fleet_event",
        description="",
    )
    research_event = GameEvent(
        id="",
        category=EventCategory.RESEARCH,
        priority=EventPriority.NORMAL,
        timestamp=2,
        title="research_event",
        description="",
    )

    manager.post_event(fleet_event)
    manager.post_event(research_event)
    manager.process_events()

    assert fleet_log == ["fleet_event"]
    assert global_log == ["research_event"]
    assert all(e.is_processed for e in manager.processed_events)


def test_event_processing_order_and_priorities():
    manager = EventManager()
    log = []

    manager.register_handler(RecordingHandler(log), EventCategory.FLEET)
    manager.register_handler(RecordingHandler(log), EventCategory.RESEARCH)

    e1 = GameEvent(
        id="",
        category=EventCategory.RESEARCH,
        priority=EventPriority.NORMAL,
        timestamp=1,
        title="research1",
        description="",
    )
    e2 = GameEvent(
        id="",
        category=EventCategory.FLEET,
        priority=EventPriority.HIGH,
        timestamp=5,
        title="fleet_high",
        description="",
    )
    e3 = GameEvent(
        id="",
        category=EventCategory.FLEET,
        priority=EventPriority.NORMAL,
        timestamp=3,
        title="fleet_normal",
        description="",
    )
    e4 = GameEvent(
        id="",
        category=EventCategory.RESEARCH,
        priority=EventPriority.LOW,
        timestamp=4,
        title="research_low",
        description="",
    )

    manager.post_event(e1)
    manager.post_event(e2)
    manager.post_event(e3)
    manager.post_event(e4)

    manager.process_events()

    assert log == ["fleet_high", "fleet_normal", "research1", "research_low"]
    processed_titles = [e.title for e in manager.processed_events]
    assert processed_titles == log


def test_unregister_handler_stops_processing():
    manager = EventManager()
    log = []

    handler = RecordingHandler(log)
    manager.register_handler(handler, EventCategory.FLEET)
    manager.unregister_handler(handler, EventCategory.FLEET)

    manager.post_event(
        GameEvent(
            id="",
            category=EventCategory.FLEET,
            priority=EventPriority.NORMAL,
            timestamp=1,
            title="unhandled",
            description="",
        )
    )

    manager.process_events()

    assert log == []
    assert len(manager.processed_events) == 0
    assert len(manager.event_queue) == 1


def test_event_expiration():
    manager = EventManager()
    log = []

    manager.register_handler(RecordingHandler(log), EventCategory.FLEET)

    manager.post_event(
        GameEvent(
            id="",
            category=EventCategory.FLEET,
            priority=EventPriority.NORMAL,
            timestamp=1,
            title="expired",
            description="",
            expiry_time=5.0,
        )
    )

    manager.process_events(current_time=10.0)

    assert log == []
    assert len(manager.processed_events) == 0
    assert len(manager.event_queue) == 0

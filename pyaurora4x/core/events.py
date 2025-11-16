"""
Event system for PyAurora 4X

Manages game events, notifications, and event-driven gameplay mechanics.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Priority levels for events."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class EventCategory(Enum):
    """Categories of game events."""
    SYSTEM = "system"
    FLEET = "fleet"
    RESEARCH = "research"
    DIPLOMACY = "diplomacy"
    COMBAT = "combat"
    EXPLORATION = "exploration"
    ECONOMY = "economy"
    INDUSTRY = "industry"
    NOTIFICATION = "notification"
    VICTORY = "victory"
    ACHIEVEMENT = "achievement"
    UI = "ui"
    GAME = "game"


@dataclass
class GameEvent:
    """
    Represents a game event that can be processed by the event system.
    """
    id: str
    category: EventCategory
    priority: EventPriority
    timestamp: float
    title: str
    description: str
    data: Dict[str, Any] = field(default_factory=dict)
    empire_id: Optional[str] = None
    system_id: Optional[str] = None
    fleet_id: Optional[str] = None
    requires_attention: bool = False
    is_processed: bool = False
    expiry_time: Optional[float] = None
    
    def __post_init__(self):
        """Validate event after creation."""
        if not self.id:
            import uuid
            self.id = str(uuid.uuid4())


class EventHandler:
    """Base class for event handlers."""
    
    def can_handle(self, event: GameEvent) -> bool:
        """Check if this handler can process the given event."""
        return True
    
    def handle(self, event: GameEvent) -> bool:
        """
        Handle the event.
        
        Args:
            event: Event to handle
            
        Returns:
            True if event was handled successfully
        """
        raise NotImplementedError("Subclasses must implement handle()")


class EventManager:
    """
    Manages the game's event system.
    
    Handles event queuing, processing, and distribution to handlers.
    """
    
    def __init__(self):
        """Initialize the event manager."""
        self.event_queue: List[GameEvent] = []
        self.processed_events: List[GameEvent] = []
        self.handlers: Dict[EventCategory, List[EventHandler]] = {}
        self.global_handlers: List[EventHandler] = []
        
        # Event statistics
        self.events_processed: int = 0
        self.events_failed: int = 0
        
        logger.debug("Event manager initialized")
    
    def register_handler(
        self, 
        handler: EventHandler, 
        category: Optional[EventCategory] = None
    ) -> None:
        """
        Register an event handler.
        
        Args:
            handler: Handler to register
            category: Category to handle (None for global handler)
        """
        if category is None:
            self.global_handlers.append(handler)
            logger.debug(f"Registered global event handler: {type(handler).__name__}")
        else:
            if category not in self.handlers:
                self.handlers[category] = []
            self.handlers[category].append(handler)
            logger.debug(f"Registered handler for {category}: {type(handler).__name__}")
    
    def unregister_handler(
        self, 
        handler: EventHandler, 
        category: Optional[EventCategory] = None
    ) -> None:
        """
        Unregister an event handler.
        
        Args:
            handler: Handler to unregister
            category: Category (None for global handler)
        """
        if category is None:
            if handler in self.global_handlers:
                self.global_handlers.remove(handler)
        else:
            if category in self.handlers and handler in self.handlers[category]:
                self.handlers[category].remove(handler)
    
    def post_event(self, event: GameEvent) -> None:
        """
        Post an event to the queue.
        
        Args:
            event: Event to post
        """
        self.event_queue.append(event)
        
        # Sort by priority and timestamp
        self.event_queue.sort(
            key=lambda e: (e.priority.value, e.timestamp), 
            reverse=True
        )
        
        logger.debug(f"Posted event: {event.title} (Priority: {event.priority.name})")
    
    def create_and_post_event(
        self,
        category: EventCategory,
        priority: EventPriority,
        title: str,
        description: str,
        timestamp: float,
        **kwargs
    ) -> GameEvent:
        """
        Create and post an event in one step.
        
        Args:
            category: Event category
            priority: Event priority
            title: Event title
            description: Event description
            timestamp: Event timestamp
            **kwargs: Additional event data
            
        Returns:
            Created event
        """
        event = GameEvent(
            id="",  # Will be auto-generated
            category=category,
            priority=priority,
            title=title,
            description=description,
            timestamp=timestamp,
            **kwargs
        )
        
        self.post_event(event)
        return event
    
    def process_events(self, current_time: Optional[float] = None) -> int:
        """
        Process all queued events.
        
        Args:
            current_time: Current game time for expiry checking
            
        Returns:
            Number of events processed
        """
        processed_count = 0
        failed_events = []
        
        while self.event_queue:
            event = self.event_queue.pop(0)
            
            # Check if event has expired
            if current_time is not None and event.expiry_time is not None:
                if current_time > event.expiry_time:
                    logger.debug(f"Event expired: {event.title}")
                    continue
            
            try:
                if self._process_single_event(event):
                    event.is_processed = True
                    self.processed_events.append(event)
                    processed_count += 1
                    self.events_processed += 1
                else:
                    failed_events.append(event)
                    self.events_failed += 1
                    
            except Exception as e:
                logger.error(f"Error processing event {event.id}: {e}")
                failed_events.append(event)
                self.events_failed += 1
        
        # Re-queue failed events (they might succeed later)
        for event in failed_events:
            if event.priority == EventPriority.CRITICAL:
                self.event_queue.insert(0, event)
            else:
                self.event_queue.append(event)
        
        if processed_count > 0:
            logger.debug(f"Processed {processed_count} events")
        
        return processed_count
    
    def _process_single_event(self, event: GameEvent) -> bool:
        """
        Process a single event.
        
        Args:
            event: Event to process
            
        Returns:
            True if event was handled successfully
        """
        handled = False
        
        # Try category-specific handlers first
        if event.category in self.handlers:
            for handler in self.handlers[event.category]:
                if handler.can_handle(event):
                    try:
                        if handler.handle(event):
                            handled = True
                            break
                    except Exception as e:
                        logger.error(f"Handler {type(handler).__name__} failed: {e}")
        
        # Try global handlers if not handled
        if not handled:
            for handler in self.global_handlers:
                if handler.can_handle(event):
                    try:
                        if handler.handle(event):
                            handled = True
                            break
                    except Exception as e:
                        logger.error(f"Global handler {type(handler).__name__} failed: {e}")
        
        if not handled:
            logger.warning(f"No handler found for event: {event.title}")
        
        return handled
    
    def get_events_for_empire(
        self, 
        empire_id: str, 
        include_processed: bool = False
    ) -> List[GameEvent]:
        """
        Get events relevant to a specific empire.
        
        Args:
            empire_id: ID of the empire
            include_processed: Whether to include processed events
            
        Returns:
            List of relevant events
        """
        events = []
        
        # Check queued events
        for event in self.event_queue:
            if event.empire_id == empire_id or event.empire_id is None:
                events.append(event)
        
        # Check processed events if requested
        if include_processed:
            for event in self.processed_events:
                if event.empire_id == empire_id or event.empire_id is None:
                    events.append(event)
        
        return events
    
    def get_pending_notifications(self, empire_id: str) -> List[GameEvent]:
        """
        Get pending notifications for an empire.
        
        Args:
            empire_id: ID of the empire
            
        Returns:
            List of pending notifications
        """
        notifications = []

        for event in self.event_queue:
            if (event.category == EventCategory.NOTIFICATION and
                event.requires_attention and
                (event.empire_id == empire_id or event.empire_id is None)):
                notifications.append(event)

        return notifications

    def get_recent_events(
        self,
        empire_id: str,
        category: EventCategory,
        limit: int = 5,
    ) -> List[GameEvent]:
        """Get the most recent processed events for an empire and category."""

        events = [
            e
            for e in self.processed_events
            if e.category == category and (e.empire_id == empire_id or e.empire_id is None)
        ]
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]
    
    def clear_processed_events(self, older_than: Optional[float] = None) -> int:
        """
        Clear processed events to free memory.
        
        Args:
            older_than: Clear events older than this timestamp
            
        Returns:
            Number of events cleared
        """
        if older_than is None:
            cleared_count = len(self.processed_events)
            self.processed_events.clear()
        else:
            initial_count = len(self.processed_events)
            self.processed_events = [
                e for e in self.processed_events 
                if e.timestamp > older_than
            ]
            cleared_count = initial_count - len(self.processed_events)
        
        if cleared_count > 0:
            logger.debug(f"Cleared {cleared_count} processed events")
        
        return cleared_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get event system statistics.
        
        Returns:
            Dictionary of statistics
        """
        return {
            "queued_events": len(self.event_queue),
            "processed_events": len(self.processed_events),
            "total_processed": self.events_processed,
            "total_failed": self.events_failed,
            "registered_handlers": sum(len(handlers) for handlers in self.handlers.values()),
            "global_handlers": len(self.global_handlers),
        }


# Convenience functions for common event types

def create_fleet_event(
    priority: EventPriority,
    title: str,
    description: str,
    timestamp: float,
    fleet_id: str,
    empire_id: str,
    **kwargs
) -> GameEvent:
    """Create a fleet-related event."""
    return GameEvent(
        id="",
        category=EventCategory.FLEET,
        priority=priority,
        title=title,
        description=description,
        timestamp=timestamp,
        fleet_id=fleet_id,
        empire_id=empire_id,
        **kwargs
    )


def create_research_event(
    priority: EventPriority,
    title: str,
    description: str,
    timestamp: float,
    empire_id: str,
    tech_id: Optional[str] = None,
    **kwargs
) -> GameEvent:
    """Create a research-related event."""
    data = kwargs.get('data', {})
    if tech_id:
        data['tech_id'] = tech_id
    
    return GameEvent(
        id="",
        category=EventCategory.RESEARCH,
        priority=priority,
        title=title,
        description=description,
        timestamp=timestamp,
        empire_id=empire_id,
        data=data,
        **kwargs
    )


def create_notification(
    title: str,
    description: str,
    timestamp: float,
    empire_id: Optional[str] = None,
    requires_attention: bool = True,
    **kwargs
) -> GameEvent:
    """Create a notification event."""
    return GameEvent(
        id="",
        category=EventCategory.NOTIFICATION,
        priority=EventPriority.NORMAL,
        title=title,
        description=description,
        timestamp=timestamp,
        empire_id=empire_id,
        requires_attention=requires_attention,
        **kwargs
    )

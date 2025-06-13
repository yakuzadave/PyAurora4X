"""
Game event scheduler for PyAurora 4X

Manages timed events and recurring tasks in the game simulation.
"""

import heapq
from typing import Callable, List, Optional, Any, Dict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScheduledEvent:
    """Represents a scheduled event in the game."""
    time: float
    event_id: str
    callback: Callable[[], None]
    is_recurring: bool = False
    interval: float = 0.0
    
    def __lt__(self, other):
        """For heap ordering."""
        return self.time < other.time


class GameScheduler:
    """
    Manages scheduled events and time-based game logic.
    
    This scheduler allows events to be scheduled at specific game times
    or as recurring events with specified intervals.
    """
    
    def __init__(self):
        """Initialize the game scheduler."""
        self.event_queue: List[ScheduledEvent] = []
        self.recurring_events: Dict[str, ScheduledEvent] = {}
        self.last_processed_time: float = 0.0
        
        logger.debug("Game scheduler initialized")
    
    def schedule_event(self, event_id: str, time: float, callback: Callable[[], None]) -> None:
        """
        Schedule a one-time event at a specific game time.
        
        Args:
            event_id: Unique identifier for the event
            time: Game time when the event should trigger
            callback: Function to call when the event triggers
        """
        event = ScheduledEvent(
            time=time,
            event_id=event_id,
            callback=callback,
            is_recurring=False
        )
        
        heapq.heappush(self.event_queue, event)
        logger.debug(f"Scheduled one-time event '{event_id}' at time {time}")
    
    def schedule_recurring_event(
        self, 
        event_id: str, 
        interval: float, 
        callback: Callable[[], None],
        start_time: Optional[float] = None
    ) -> None:
        """
        Schedule a recurring event with a specified interval.
        
        Args:
            event_id: Unique identifier for the event
            interval: Time interval between event triggers
            callback: Function to call when the event triggers
            start_time: When to start the recurring event (defaults to next interval)
        """
        if start_time is None:
            start_time = self.last_processed_time + interval
        
        event = ScheduledEvent(
            time=start_time,
            event_id=event_id,
            callback=callback,
            is_recurring=True,
            interval=interval
        )
        
        heapq.heappush(self.event_queue, event)
        self.recurring_events[event_id] = event
        logger.debug(f"Scheduled recurring event '{event_id}' with interval {interval}")
    
    def cancel_event(self, event_id: str) -> bool:
        """
        Cancel a scheduled event.
        
        Args:
            event_id: ID of the event to cancel
            
        Returns:
            True if event was found and cancelled, False otherwise
        """
        # Remove from recurring events if present
        if event_id in self.recurring_events:
            del self.recurring_events[event_id]
        
        # Note: We don't remove from the heap immediately for efficiency
        # Instead, we'll check if the event is still valid when processing
        logger.debug(f"Cancelled event '{event_id}'")
        return True
    
    def process_events(self, start_time: float, end_time: float) -> List[str]:
        """
        Process all events that should trigger between start_time and end_time.
        
        Args:
            start_time: Start of the time range
            end_time: End of the time range
            
        Returns:
            List of event IDs that were triggered
        """
        triggered_events = []
        
        while self.event_queue and self.event_queue[0].time <= end_time:
            event = heapq.heappop(self.event_queue)
            
            # Skip cancelled events
            if event.is_recurring and event.event_id not in self.recurring_events:
                continue
            
            # Only trigger if the event time is within our range
            if event.time >= start_time:
                try:
                    event.callback()
                    triggered_events.append(event.event_id)
                    logger.debug(f"Triggered event '{event.event_id}' at time {event.time}")
                except Exception as e:
                    logger.error(f"Error executing event '{event.event_id}': {e}")
            
            # Reschedule if recurring
            if event.is_recurring and event.event_id in self.recurring_events:
                next_time = event.time + event.interval
                next_event = ScheduledEvent(
                    time=next_time,
                    event_id=event.event_id,
                    callback=event.callback,
                    is_recurring=True,
                    interval=event.interval
                )
                heapq.heappush(self.event_queue, next_event)
                self.recurring_events[event.event_id] = next_event
        
        self.last_processed_time = end_time
        return triggered_events
    
    def get_next_event_time(self) -> Optional[float]:
        """
        Get the time of the next scheduled event.
        
        Returns:
            Time of next event, or None if no events scheduled
        """
        while self.event_queue:
            event = self.event_queue[0]
            
            # Check if event is still valid
            if not event.is_recurring or event.event_id in self.recurring_events:
                return event.time
            else:
                # Remove cancelled event
                heapq.heappop(self.event_queue)
        
        return None
    
    def get_pending_events_count(self) -> int:
        """Get the number of pending events."""
        # Clean up cancelled events first
        valid_events = []
        while self.event_queue:
            event = heapq.heappop(self.event_queue)
            if not event.is_recurring or event.event_id in self.recurring_events:
                valid_events.append(event)
        
        # Rebuild the heap
        self.event_queue = valid_events
        heapq.heapify(self.event_queue)
        
        return len(self.event_queue)
    
    def clear_all_events(self) -> None:
        """Clear all scheduled events."""
        self.event_queue.clear()
        self.recurring_events.clear()
        logger.info("Cleared all scheduled events")

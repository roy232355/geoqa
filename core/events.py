# -*- coding: utf-8 -*-
"""Event bus implementation for decoupling plugin components."""

from typing import Callable, Dict, List


class EventBus:
    """A lightweight publisher-subscriber event bus for broadcasting validation checkpoints."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        """Registers a callback function to listen for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        """Removes a registered callback from listening to an event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass

    def publish(self, event_type: str, *args, **kwargs):
        """Triggers all callback functions subscribed to the event type."""
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    # Prevent callback failures from crashing core flow
                    from .logger import log_error
                    log_error(f"Error executing callback for event '{event_type}': {str(e)}")

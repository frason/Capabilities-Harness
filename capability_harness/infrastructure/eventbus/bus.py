"""In-process event bus for decoupling subsystems via domain events."""
from __future__ import annotations

import threading
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from capability_harness.domain.events import DomainEvent


class EventBus:
    """Protocol for the internal event bus."""

    def publish(self, event: DomainEvent) -> None: ...
    def subscribe(self, event_type: type[DomainEvent], handler: Callable[[Any], None]) -> None: ...
    def unsubscribe(self, event_type: type[DomainEvent], handler: Callable[[Any], None]) -> None: ...


class InProcessEventBus:
    """Synchronous in-process pub/sub event bus.

    Subscribers are called synchronously in the publishing thread.
    Replace with an async or broker-backed implementation without
    changing any application-layer code.
    """

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[Callable[[Any], None]]] = defaultdict(list)
        self._lock = threading.Lock()

    def publish(self, event: DomainEvent) -> None:
        """Deliver event to all registered handlers for its type."""
        event_type = type(event)
        with self._lock:
            handlers = list(self._handlers.get(event_type, []))
        for handler in handlers:
            handler(event)

    def subscribe(self, event_type: type[DomainEvent], handler: Callable[[Any], None]) -> None:
        """Register a handler for a specific event type."""
        with self._lock:
            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: type[DomainEvent], handler: Callable[[Any], None]) -> None:
        """Remove a handler for a specific event type."""
        with self._lock:
            handlers = self._handlers.get(event_type, [])
            if handler in handlers:
                handlers.remove(handler)

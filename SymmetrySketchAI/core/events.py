"""Lightweight, thread-safe application event system.

Design rationale:
    Future subsystems (vision tracker, gesture engine, stroke engine,
    renderer, timeline, ui, ai, plugins) need to communicate without
    importing one another directly -- that would violate the layering
    described in ``docs/ARCHITECTURE.md`` and invite circular imports.
    A single, dependency-free publish/subscribe bus lets any module
    publish an :class:`Event` and any other module subscribe to it by
    type, without either side knowing the other exists.

    This module intentionally contains NO business logic. It does not
    know what a "stroke" or a "gesture" is; subsystem-specific event
    subclasses and payloads are defined by their owning subsystem and
    simply passed through here.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

from core.exceptions import SymmetrySketchError

EventListener = Callable[["Event"], None]
TEvent = TypeVar("TEvent", bound="Event")


class EventError(SymmetrySketchError):
    """Base class for errors originating in the event subsystem."""


class ListenerNotRegisteredError(EventError):
    """Raised when attempting to remove a listener that isn't registered."""


@dataclass(frozen=True, slots=True)
class Event:
    """Base class for all application events.

    Subsystems define concrete events by subclassing this, e.g.::

        @dataclass(frozen=True, slots=True)
        class StrokeCompleted(Event):
            stroke_id: StrokeId

    Attributes:
        event_id: Globally-unique identifier for this specific event
            occurrence, useful for logging/tracing.
        timestamp: Wall-clock time (seconds since epoch) the event was
            constructed.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()), kw_only=True)
    timestamp: float = field(default_factory=time.time, kw_only=True)


@dataclass(frozen=True, slots=True)
class _Subscription:
    """Internal record binding a listener to a subscription id."""

    subscription_id: str
    listener: EventListener


class EventBus:
    """Thread-safe publish/subscribe dispatcher for :class:`Event` objects.

    Listeners are registered per concrete event type (by class, not by
    string name, so typos can't silently create a dead subscription).
    Dispatch is synchronous: ``publish`` calls each matching listener in
    registration order on the calling thread. A snapshot of listeners is
    taken before dispatch so a listener may safely subscribe/unsubscribe
    during its own invocation without deadlocking or mutating the list
    being iterated.
    """

    def __init__(self) -> None:
        self._listeners: dict[type[Event], list[_Subscription]] = {}
        self._lock = threading.RLock()

    def subscribe(
        self, event_type: type[TEvent], listener: Callable[[TEvent], None]
    ) -> str:
        """Register ``listener`` to be called whenever ``event_type`` is
        published.

        Args:
            event_type: The exact :class:`Event` subclass to listen for.
                Subscriptions are NOT polymorphic -- subscribing to
                ``Event`` does not receive subclass events.
            listener: A callable accepting a single event instance.

        Returns:
            A subscription id that can be passed to :meth:`unsubscribe`.
        """
        subscription_id = str(uuid.uuid4())
        with self._lock:
            self._listeners.setdefault(event_type, []).append(
                _Subscription(subscription_id=subscription_id, listener=listener)  # type: ignore[arg-type]
            )
        return subscription_id

    def unsubscribe(self, event_type: type[Event], subscription_id: str) -> None:
        """Remove a previously registered listener.

        Args:
            event_type: The event type originally passed to
                :meth:`subscribe`.
            subscription_id: The id returned by :meth:`subscribe`.

        Raises:
            ListenerNotRegisteredError: If no such subscription exists.
        """
        with self._lock:
            subscriptions = self._listeners.get(event_type)
            if not subscriptions:
                raise ListenerNotRegisteredError(
                    f"No listeners registered for {event_type.__name__!r}."
                )
            for index, subscription in enumerate(subscriptions):
                if subscription.subscription_id == subscription_id:
                    del subscriptions[index]
                    if not subscriptions:
                        del self._listeners[event_type]
                    return
            raise ListenerNotRegisteredError(
                f"Subscription {subscription_id!r} not found for "
                f"{event_type.__name__!r}."
            )

    def unsubscribe_all(self, event_type: type[Event] | None = None) -> None:
        """Remove all listeners, optionally scoped to a single event type.

        Args:
            event_type: If given, only listeners for this type are
                removed. If omitted, every listener for every event type
                is removed.
        """
        with self._lock:
            if event_type is None:
                self._listeners.clear()
            else:
                self._listeners.pop(event_type, None)

    def publish(self, event: Event) -> None:
        """Synchronously dispatch ``event`` to all matching listeners.

        Listeners for ``type(event)`` exactly (not superclasses or
        subclasses) are invoked in registration order. If no listeners
        are registered, this is a no-op.
        """
        with self._lock:
            subscriptions = list(self._listeners.get(type(event), ()))
        for subscription in subscriptions:
            subscription.listener(event)

    def listener_count(self, event_type: type[Event]) -> int:
        """Return the number of listeners currently registered for
        ``event_type``.
        """
        with self._lock:
            return len(self._listeners.get(event_type, ()))

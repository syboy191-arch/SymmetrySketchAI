"""Unit tests for core.events."""

from __future__ import annotations

import threading
from dataclasses import dataclass

import pytest

from core.events import Event, EventBus, ListenerNotRegisteredError


@dataclass(frozen=True, slots=True)
class SampleEventA(Event):
    payload: str = ""


@dataclass(frozen=True, slots=True)
class SampleEventB(Event):
    payload: int = 0


class TestEvent:
    def test_has_unique_event_id(self) -> None:
        a = SampleEventA()
        b = SampleEventA()
        assert a.event_id != b.event_id

    def test_has_timestamp(self) -> None:
        event = SampleEventA()
        assert event.timestamp > 0

    def test_is_immutable(self) -> None:
        event = SampleEventA(payload="x")
        with pytest.raises(Exception):
            event.payload = "y"  # type: ignore[misc]


class TestEventBusPublishSubscribe:
    def test_publish_calls_subscribed_listener(self) -> None:
        bus = EventBus()
        received: list[Event] = []
        bus.subscribe(SampleEventA, received.append)

        event = SampleEventA(payload="hello")
        bus.publish(event)

        assert received == [event]

    def test_publish_with_no_listeners_is_noop(self) -> None:
        bus = EventBus()
        bus.publish(SampleEventA(payload="hello"))  # should not raise

    def test_publish_only_notifies_exact_type_listeners(self) -> None:
        bus = EventBus()
        received_a: list[Event] = []
        received_b: list[Event] = []
        bus.subscribe(SampleEventA, received_a.append)
        bus.subscribe(SampleEventB, received_b.append)

        bus.publish(SampleEventA(payload="a"))

        assert len(received_a) == 1
        assert len(received_b) == 0

    def test_multiple_listeners_all_receive_event(self) -> None:
        bus = EventBus()
        calls: list[str] = []
        bus.subscribe(SampleEventA, lambda e: calls.append("first"))
        bus.subscribe(SampleEventA, lambda e: calls.append("second"))

        bus.publish(SampleEventA(payload="x"))

        assert calls == ["first", "second"]

    def test_listeners_called_in_registration_order(self) -> None:
        bus = EventBus()
        order: list[int] = []
        for i in range(5):
            bus.subscribe(SampleEventA, lambda e, i=i: order.append(i))

        bus.publish(SampleEventA())

        assert order == [0, 1, 2, 3, 4]

    def test_subscribe_returns_unique_subscription_ids(self) -> None:
        bus = EventBus()
        id1 = bus.subscribe(SampleEventA, lambda e: None)
        id2 = bus.subscribe(SampleEventA, lambda e: None)
        assert id1 != id2


class TestEventBusUnsubscribe:
    def test_unsubscribe_stops_further_notifications(self) -> None:
        bus = EventBus()
        received: list[Event] = []
        subscription_id = bus.subscribe(SampleEventA, received.append)

        bus.unsubscribe(SampleEventA, subscription_id)
        bus.publish(SampleEventA())

        assert received == []

    def test_unsubscribe_unknown_id_raises(self) -> None:
        bus = EventBus()
        bus.subscribe(SampleEventA, lambda e: None)
        with pytest.raises(ListenerNotRegisteredError):
            bus.unsubscribe(SampleEventA, "not-a-real-id")

    def test_unsubscribe_from_type_with_no_listeners_raises(self) -> None:
        bus = EventBus()
        with pytest.raises(ListenerNotRegisteredError):
            bus.unsubscribe(SampleEventA, "anything")

    def test_unsubscribe_only_removes_targeted_listener(self) -> None:
        bus = EventBus()
        received: list[str] = []
        id1 = bus.subscribe(SampleEventA, lambda e: received.append("one"))
        bus.subscribe(SampleEventA, lambda e: received.append("two"))

        bus.unsubscribe(SampleEventA, id1)
        bus.publish(SampleEventA())

        assert received == ["two"]

    def test_unsubscribe_all_for_type(self) -> None:
        bus = EventBus()
        received: list[Event] = []
        bus.subscribe(SampleEventA, received.append)
        bus.subscribe(SampleEventA, received.append)

        bus.unsubscribe_all(SampleEventA)
        bus.publish(SampleEventA())

        assert received == []

    def test_unsubscribe_all_without_type_clears_everything(self) -> None:
        bus = EventBus()
        received_a: list[Event] = []
        received_b: list[Event] = []
        bus.subscribe(SampleEventA, received_a.append)
        bus.subscribe(SampleEventB, received_b.append)

        bus.unsubscribe_all()
        bus.publish(SampleEventA())
        bus.publish(SampleEventB())

        assert received_a == []
        assert received_b == []


class TestEventBusListenerCount:
    def test_listener_count_reflects_subscriptions(self) -> None:
        bus = EventBus()
        assert bus.listener_count(SampleEventA) == 0

        bus.subscribe(SampleEventA, lambda e: None)
        bus.subscribe(SampleEventA, lambda e: None)

        assert bus.listener_count(SampleEventA) == 2

    def test_listener_count_for_unregistered_type_is_zero(self) -> None:
        bus = EventBus()
        assert bus.listener_count(SampleEventB) == 0


class TestEventBusEdgeCases:
    def test_listener_can_unsubscribe_itself_during_dispatch(self) -> None:
        bus = EventBus()
        received: list[Event] = []
        subscription_id: list[str] = []

        def handler(event: Event) -> None:
            received.append(event)
            bus.unsubscribe(SampleEventA, subscription_id[0])

        subscription_id.append(bus.subscribe(SampleEventA, handler))

        bus.publish(SampleEventA())
        bus.publish(SampleEventA())

        assert len(received) == 1

    def test_listener_can_subscribe_new_listener_during_dispatch(self) -> None:
        bus = EventBus()
        received: list[str] = []

        def first_handler(event: Event) -> None:
            received.append("first")
            bus.subscribe(SampleEventA, lambda e: received.append("second"))

        bus.subscribe(SampleEventA, first_handler)

        bus.publish(SampleEventA())
        assert received == ["first"]

        bus.publish(SampleEventA())
        assert received == ["first", "first", "second"]

    def test_thread_safe_concurrent_publish(self) -> None:
        bus = EventBus()
        counter = {"count": 0}
        lock = threading.Lock()

        def handler(event: Event) -> None:
            with lock:
                counter["count"] += 1

        bus.subscribe(SampleEventA, handler)

        def publish_many() -> None:
            for _ in range(100):
                bus.publish(SampleEventA())

        threads = [threading.Thread(target=publish_many) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert counter["count"] == 400

"""Unit tests for core.dependency_container."""

from __future__ import annotations

import pytest

from core.dependency_container import (
    DependencyContainer,
    ServiceAlreadyRegisteredError,
    ServiceNotRegisteredError,
)


class ServiceA:
    def __init__(self) -> None:
        self.value = "a"


class ServiceB:
    def __init__(self) -> None:
        self.value = "b"


class TestSingletonRegistration:
    def test_resolve_returns_instance(self) -> None:
        container = DependencyContainer()
        container.register_singleton(ServiceA, ServiceA)
        assert isinstance(container.resolve(ServiceA), ServiceA)

    def test_resolve_returns_same_instance_across_calls(self) -> None:
        container = DependencyContainer()
        container.register_singleton(ServiceA, ServiceA)
        first = container.resolve(ServiceA)
        second = container.resolve(ServiceA)
        assert first is second

    def test_factory_not_invoked_until_first_resolve(self) -> None:
        container = DependencyContainer()
        calls = {"count": 0}

        def factory() -> ServiceA:
            calls["count"] += 1
            return ServiceA()

        container.register_singleton(ServiceA, factory)
        assert calls["count"] == 0

        container.resolve(ServiceA)
        assert calls["count"] == 1

        container.resolve(ServiceA)
        assert calls["count"] == 1

    def test_duplicate_registration_raises(self) -> None:
        container = DependencyContainer()
        container.register_singleton(ServiceA, ServiceA)
        with pytest.raises(ServiceAlreadyRegisteredError):
            container.register_singleton(ServiceA, ServiceA)


class TestFactoryRegistration:
    def test_resolve_returns_new_instance_each_call(self) -> None:
        container = DependencyContainer()
        container.register_factory(ServiceA, ServiceA)
        first = container.resolve(ServiceA)
        second = container.resolve(ServiceA)
        assert first is not second
        assert isinstance(first, ServiceA)
        assert isinstance(second, ServiceA)

    def test_duplicate_registration_raises(self) -> None:
        container = DependencyContainer()
        container.register_factory(ServiceA, ServiceA)
        with pytest.raises(ServiceAlreadyRegisteredError):
            container.register_factory(ServiceA, ServiceA)


class TestInstanceRegistration:
    def test_resolve_returns_the_exact_instance(self) -> None:
        container = DependencyContainer()
        instance = ServiceA()
        container.register_instance(ServiceA, instance)
        assert container.resolve(ServiceA) is instance

    def test_duplicate_registration_raises(self) -> None:
        container = DependencyContainer()
        container.register_instance(ServiceA, ServiceA())
        with pytest.raises(ServiceAlreadyRegisteredError):
            container.register_instance(ServiceA, ServiceA())


class TestResolutionFailures:
    def test_resolve_unregistered_type_raises(self) -> None:
        container = DependencyContainer()
        with pytest.raises(ServiceNotRegisteredError):
            container.resolve(ServiceA)

    def test_resolving_one_type_does_not_affect_another(self) -> None:
        container = DependencyContainer()
        container.register_singleton(ServiceA, ServiceA)
        with pytest.raises(ServiceNotRegisteredError):
            container.resolve(ServiceB)


class TestIsRegistered:
    def test_true_after_registration(self) -> None:
        container = DependencyContainer()
        container.register_singleton(ServiceA, ServiceA)
        assert container.is_registered(ServiceA) is True

    def test_false_when_never_registered(self) -> None:
        container = DependencyContainer()
        assert container.is_registered(ServiceA) is False


class TestUnregisterAndClear:
    def test_unregister_removes_registration(self) -> None:
        container = DependencyContainer()
        container.register_singleton(ServiceA, ServiceA)
        container.unregister(ServiceA)
        assert container.is_registered(ServiceA) is False
        with pytest.raises(ServiceNotRegisteredError):
            container.resolve(ServiceA)

    def test_unregister_allows_re_registration(self) -> None:
        container = DependencyContainer()
        container.register_singleton(ServiceA, ServiceA)
        container.unregister(ServiceA)
        container.register_factory(ServiceA, ServiceA)  # should not raise
        assert container.is_registered(ServiceA) is True

    def test_unregister_unknown_type_is_noop(self) -> None:
        container = DependencyContainer()
        container.unregister(ServiceA)  # should not raise

    def test_clear_removes_all_registrations(self) -> None:
        container = DependencyContainer()
        container.register_singleton(ServiceA, ServiceA)
        container.register_singleton(ServiceB, ServiceB)

        container.clear()

        assert container.is_registered(ServiceA) is False
        assert container.is_registered(ServiceB) is False

    def test_clear_resets_cached_singleton_instances(self) -> None:
        container = DependencyContainer()
        container.register_singleton(ServiceA, ServiceA)
        first = container.resolve(ServiceA)

        container.clear()
        container.register_singleton(ServiceA, ServiceA)
        second = container.resolve(ServiceA)

        assert first is not second

"""Minimal dependency-injection container.

Design rationale:
    As the application grows (vision, drawing, timeline, ui, ai, export,
    persistence), modules need access to shared services (config
    objects, the event bus, future engines) without importing concrete
    implementations from unrelated packages. A small service locator /
    DI container lets each subsystem register how to build its
    services once, at startup, and lets every other subsystem resolve
    them by type without knowing construction details.

    This container deliberately does NOT eagerly construct anything
    that isn't yet implemented. Factories are only invoked when
    ``resolve`` is actually called for that type, so registering a
    factory for a not-yet-built module is safe as long as nothing
    resolves it before it exists.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TypeVar

from core.exceptions import SymmetrySketchError

T = TypeVar("T")
Factory = Callable[[], T]


class DependencyContainerError(SymmetrySketchError):
    """Base class for errors originating in the dependency container."""


class ServiceAlreadyRegisteredError(DependencyContainerError):
    """Raised when registering a service type that is already registered."""


class ServiceNotRegisteredError(DependencyContainerError):
    """Raised when resolving a service type that has no registration."""


class DependencyContainer:
    """A minimal, type-keyed service locator with lazy singletons.

    Two registration modes are supported:

    * :meth:`register_singleton` -- the factory is invoked at most once;
      the first resolved instance is cached and reused for the lifetime
      of the container.
    * :meth:`register_factory` -- the factory is invoked on every
      :meth:`resolve` call, producing a new instance each time.

    Example:
        >>> container = DependencyContainer()
        >>> container.register_singleton(EventBus, EventBus)
        >>> bus = container.resolve(EventBus)
    """

    def __init__(self) -> None:
        self._factories: dict[type, Factory] = {}
        self._singletons: dict[type, bool] = {}
        self._instances: dict[type, object] = {}
        self._lock = threading.RLock()

    def register_singleton(
        self, service_type: type[T], factory: Factory[T]
    ) -> None:
        """Register ``factory`` to lazily build a single shared instance
        of ``service_type``.

        The factory is not called immediately -- construction is
        deferred until the first :meth:`resolve` call, so services
        whose dependencies aren't ready yet can still be registered
        upfront during application bootstrap.

        Args:
            service_type: The type other code will use to look up this
                service.
            factory: A zero-argument callable that constructs the
                instance.

        Raises:
            ServiceAlreadyRegisteredError: If ``service_type`` is
                already registered.
        """
        with self._lock:
            self._raise_if_registered(service_type)
            self._factories[service_type] = factory
            self._singletons[service_type] = True

    def register_factory(self, service_type: type[T], factory: Factory[T]) -> None:
        """Register ``factory`` to build a fresh instance of
        ``service_type`` on every :meth:`resolve` call.

        Args:
            service_type: The type other code will use to look up this
                service.
            factory: A zero-argument callable that constructs an
                instance.

        Raises:
            ServiceAlreadyRegisteredError: If ``service_type`` is
                already registered.
        """
        with self._lock:
            self._raise_if_registered(service_type)
            self._factories[service_type] = factory
            self._singletons[service_type] = False

    def register_instance(self, service_type: type[T], instance: T) -> None:
        """Register an already-constructed ``instance`` directly.

        Equivalent to a singleton whose factory simply returns
        ``instance``, without deferring construction.

        Args:
            service_type: The type other code will use to look up this
                service.
            instance: The pre-built instance to store.

        Raises:
            ServiceAlreadyRegisteredError: If ``service_type`` is
                already registered.
        """
        with self._lock:
            self._raise_if_registered(service_type)
            self._factories[service_type] = lambda: instance
            self._singletons[service_type] = True
            self._instances[service_type] = instance

    def resolve(self, service_type: type[T]) -> T:
        """Return an instance of ``service_type``.

        For singleton registrations, the same instance is returned on
        every call after the first. For factory registrations, a new
        instance is constructed and returned each call.

        Args:
            service_type: The type to resolve.

        Returns:
            An instance of ``service_type``.

        Raises:
            ServiceNotRegisteredError: If ``service_type`` has no
                registration.
        """
        with self._lock:
            if service_type not in self._factories:
                raise ServiceNotRegisteredError(
                    f"No registration found for {service_type.__name__!r}. "
                    "Did you forget to register it during bootstrap?"
                )

            if self._singletons[service_type]:
                if service_type not in self._instances:
                    self._instances[service_type] = self._factories[service_type]()
                return self._instances[service_type]  # type: ignore[return-value]

            return self._factories[service_type]()  # type: ignore[return-value]

    def is_registered(self, service_type: type) -> bool:
        """Return whether ``service_type`` has any registration."""
        with self._lock:
            return service_type in self._factories

    def unregister(self, service_type: type) -> None:
        """Remove a registration (and any cached singleton instance).

        Primarily intended for test isolation. No-op if ``service_type``
        was never registered.
        """
        with self._lock:
            self._factories.pop(service_type, None)
            self._singletons.pop(service_type, None)
            self._instances.pop(service_type, None)

    def clear(self) -> None:
        """Remove all registrations and cached instances.

        Primarily intended for test isolation between test modules that
        each build their own container configuration.
        """
        with self._lock:
            self._factories.clear()
            self._singletons.clear()
            self._instances.clear()

    def _raise_if_registered(self, service_type: type) -> None:
        if service_type in self._factories:
            raise ServiceAlreadyRegisteredError(
                f"{service_type.__name__!r} is already registered."
            )

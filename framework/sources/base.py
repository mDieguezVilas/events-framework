from abc import ABC, abstractmethod
from typing import Any
from framework.models import EventPayload


_REGISTRY: dict[str, type] = {}


def event_source(source_id: str, enabled: bool = True):
    """Decorador que registra una clase EventSource automáticamente."""
    def decorator(cls):
        cls.source_id = source_id
        cls.enabled = enabled
        _REGISTRY[source_id] = cls
        return cls
    return decorator


def get_registered_sources() -> dict[str, type]:
    return dict(_REGISTRY)


class EventSource(ABC):

    source_id: str
    enabled: bool = True

    @abstractmethod
    def fetch(self) -> Any:
        """Descarga los datos crudos de la fuente."""
        ...

    @abstractmethod
    def parse(self, raw: Any) -> list[EventPayload]:
        """Convierte los datos crudos en lista de EventPayload."""
        ...
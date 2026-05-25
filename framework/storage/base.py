from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from framework.models import Event, EventPayload


class StorageAdapter(ABC):

    @abstractmethod
    def init(self) -> None:
        """Inicializa el storage (crea tablas, ficheros, etc.)"""
        ...

    @abstractmethod
    def save_event(self, payload: EventPayload) -> Event:
        """Guarda un evento y devuelve el Event con id asignado."""
        ...

    @abstractmethod
    def bulk_save(self, payloads: list[EventPayload]) -> list[Event]:
        """Guarda múltiples eventos. Implementación por defecto: itera save_event."""
        ...

    @abstractmethod
    def query(self, filter_spec: dict[str, Any] | None = None) -> list[Event]:
        """Devuelve eventos que coincidan con filter_spec."""
        ...

    @abstractmethod
    def exists_fingerprint(self, fingerprint: str) -> bool:
        """Comprueba si ya existe un evento con este fingerprint (dedup)."""
        ...

    @abstractmethod
    def capabilities(self) -> set[str]:
        """Informa de las capacidades del adaptador."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Cierra conexiones o ficheros abiertos."""
        ...
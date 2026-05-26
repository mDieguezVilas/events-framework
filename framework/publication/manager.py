from typing import Optional
from framework.models import Event
from framework.publication.base import NotificationAdapter


class PublicationManager:

    def __init__(self, adapters: Optional[list[NotificationAdapter]] = None):
        self._adapters = adapters or []

    def add_adapter(self, adapter: NotificationAdapter) -> None:
        self._adapters.append(adapter)

    def publish(self, events: list[Event]) -> None:
        for adapter in self._adapters:
            adapter.send(events)
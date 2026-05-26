from abc import ABC, abstractmethod
from framework.models import Event


class NotificationAdapter(ABC):

    @abstractmethod
    def send(self, events: list[Event]) -> None:
        ...
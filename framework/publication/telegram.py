import httpx
import logging
from framework.models import Event
from framework.publication.base import NotificationAdapter

logger = logging.getLogger(__name__)


class TelegramAdapter(NotificationAdapter):

    def __init__(self, token: str, chat_id: str):
        self._token = token
        self._chat_id = chat_id

    def send(self, events: list[Event]) -> None:
        for event in events:
            message = self._format(event)
            self._send_message(message)

    def _format(self, event: Event) -> str:
        lines = [f"*{event.name}*"]
        if event.event_date:
            lines.append(f"📅 {event.event_date}")
        if event.data.get("location"):
            lines.append(f"📍 {event.data['location']}")
        lines.append(f"🔗 {event.url}")
        return "\n".join(lines)

    def _send_message(self, text: str) -> None:
        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        try:
            response = httpx.post(url, json={
                "chat_id": self._chat_id,
                "text": text,
                "parse_mode": "Markdown",
            })
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Error enviando mensaje Telegram: {e}")
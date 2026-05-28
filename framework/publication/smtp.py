import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from framework.models import Event
from framework.publication.base import NotificationAdapter

logger = logging.getLogger(__name__)


class SMTPAdapter(NotificationAdapter):

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        from_addr: str,
        to_addr: str,
        summary: bool = False,
    ):
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._from_addr = from_addr
        self._to_addr = to_addr
        self._summary = summary

    def send(self, events: list[Event]) -> None:
        if not events:
            return
        if self._summary:
            self._send_summary(events)
        else:
            for event in events:
                self._send_single(event)

    def _send_single(self, event: Event) -> None:
        subject = f"Nuevo evento: {event.name}"
        body = self._format_single(event)
        self._send_email(subject, body)

    def _send_summary(self, events: list[Event]) -> None:
        subject = f"Resumen: {len(events)} evento(s) nuevo(s)"
        lines = [f"Se han encontrado {len(events)} evento(s) nuevo(s):\n"]
        for event in events:
            lines.append(self._format_single(event))
            lines.append("-" * 40)
        body = "\n".join(lines)
        self._send_email(subject, body)

    def _format_single(self, event: Event) -> str:
        lines = [
            f"Nombre: {event.name}",
            f"Fuente: {event.source}",
        ]
        if event.event_date:
            lines.append(f"Fecha: {event.event_date}")
        if event.data.get("location"):
            lines.append(f"Lugar: {event.data['location']}")
        if event.data.get("distance"):
            lines.append(f"Distancia: {event.data['distance']}")
        lines.append(f"URL: {event.url}")
        return "\n".join(lines)

    def _send_email(self, subject: str, body: str) -> None:
        msg = MIMEMultipart()
        msg["From"] = self._from_addr
        msg["To"] = self._to_addr
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        try:
            with smtplib.SMTP(self._host, self._port) as server:
                server.ehlo()
                server.starttls()
                server.login(self._user, self._password)
                server.sendmail(self._from_addr, self._to_addr, msg.as_string())
            logger.info(f"Email enviado: {subject}")
        except Exception as e:
            logger.error(f"Error enviando email: {e}")
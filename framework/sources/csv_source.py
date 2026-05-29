import csv
import logging
from pathlib import Path
from typing import Any
from datetime import datetime
from framework.models import EventPayload
from framework.sources.base import EventSource, event_source

logger = logging.getLogger(__name__)


@event_source(source_id="csv_manual", enabled=True)
class CSVSource(EventSource):

    def __init__(self, csv_path: str = "data/sample_events.csv"):
        self._csv_path = Path(csv_path)

    def fetch(self) -> list[dict[str, Any]]:
        if not self._csv_path.exists():
            logger.warning(f"Fichero CSV no encontrado: {self._csv_path}")
            return []

        with open(self._csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        logger.info(f"csv_manual: {len(rows)} filas leídas de {self._csv_path}")
        return rows

    def parse(self, raw: list[dict[str, Any]]) -> list[EventPayload]:
        payloads = []
        for row in raw:
            try:
                if not row.get("name") or not row.get("url"):
                    logger.warning(f"csv_manual: fila ignorada — name o url vacíos")
                    continue
                event_date = None
                if row.get("event_date"):
                    event_date = datetime.fromisoformat(row["event_date"])

                payload = EventPayload(
                    type_="race",
                    name=row["name"],
                    url=row["url"],
                    source=self.source_id,
                    event_date=event_date,
                    data={
                        "location": row.get("location", ""),
                        "distance": row.get("distance", ""),
                    },
                )
                payloads.append(payload)
            except Exception as e:
                logger.warning(f"csv_manual: fila ignorada — {e} — {row}")

        return payloads
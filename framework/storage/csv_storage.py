from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Any
from framework.models import Event, EventPayload
from framework.storage.base import StorageAdapter
import logging

logger = logging.getLogger(__name__)

class CSVStorage(StorageAdapter):

    def __init__(self, data_dir: str | Path = "data"):
        self._dir = Path(data_dir)
        self._events_path = self._dir / "events.csv"
        self._fp_path = self._dir / "fingerprints.csv"
        self._next_id = 1
        self._fingerprints: set[str] = set()

    def init(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)

        if not self._events_path.exists():
            with open(self._events_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self._fieldnames())
                writer.writeheader()
        else:
            with open(self._events_path, encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            if rows:
                self._next_id = max(int(r["id"]) for r in rows) + 1

        if self._fp_path.exists():
            with open(self._fp_path, encoding="utf-8") as f:
                self._fingerprints = {line.strip() for line in f if line.strip()}

    def _fieldnames(self) -> list[str]:
        return ["id", "type_", "name", "url", "source", "event_date", "data"]

    def save_event(self, payload: EventPayload) -> Event:
        event = payload.to_event()
        event = event.model_copy(update={"id": self._next_id})
        self._next_id += 1

        with open(self._events_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self._fieldnames())
            row = event.model_dump()
            row["data"] = json.dumps(row.get("data", {}))
            writer.writerow(row)

        return event

    def bulk_save(self, payloads: list[EventPayload]) -> list[Event]:
        return [self.save_event(p) for p in payloads]

    def query(self, filter_spec: dict[str, Any] | None = None) -> list[Event]:
        if not self._events_path.exists():
            return []

        with open(self._events_path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        events = []
        for row in rows:
            row["data"] = json.loads(row.get("data") or "{}")
            if not row.get("event_date"):
                row["event_date"] = None
            e = Event.model_validate(row)
            events.append(e)

        if not filter_spec:
            return events

        result = []
        for e in events:
            match = True
            for key, val in filter_spec.items():
                if key == "id" and e.id != val:
                    match = False
                elif key == "source" and e.source != val:
                    match = False
                elif key == "type_" and e.type_ != val:
                    match = False
                elif key == "date_from" and (e.event_date is None or e.event_date < val):
                    match = False
                elif key == "date_to" and (e.event_date is None or e.event_date > val):
                    match = False
            if match:
                result.append(e)
        return result

    def exists_fingerprint(self, fingerprint: str) -> bool:
        return fingerprint in self._fingerprints

    def save_fingerprint(self, fingerprint: str) -> None:
        self._fingerprints.add(fingerprint)
        with open(self._fp_path, "a", encoding="utf-8") as f:
            f.write(fingerprint + "\n")

    def capabilities(self) -> set[str]:
        return {"export", "import"}

    def close(self) -> None:
        pass

    def get_promoted_fields(self) -> list[str]:
        return []

    def promote_field(self, type_id: str, field: str) -> None:
        logger.warning("CSVStorage no soporta promoción de campos")
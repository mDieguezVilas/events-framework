from __future__ import annotations
import json
from pathlib import Path
from framework.models import EventType


class Registry:
    """
    Guarda definiciones de EventType.
    
    """

    def __init__(self, path: str | Path = "data/registry.json"):
        self._path = Path(path)
        self._types: dict[str, EventType] = {}

    def init(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if self._path.exists():
            with open(self._path, encoding="utf-8") as f:
                raw = json.load(f)
            for item in raw:
                et = EventType(**item)
                self._types[et.type_id] = et

    def register(self, event_type: EventType) -> None:
        self._types[event_type.type_id] = event_type
        self._persist()

    def get(self, type_id: str) -> EventType | None:
        return self._types.get(type_id)

    def all(self) -> list[EventType]:
        return list(self._types.values())

    def _persist(self) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump([et.model_dump() for et in self._types.values()], f, indent=2)
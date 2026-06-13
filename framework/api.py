import logging
from typing import Optional
from datetime import date
from fastapi import FastAPI, HTTPException, Query
from framework.models import Event
from framework.storage.base import StorageAdapter
from framework.registry import Registry

logger = logging.getLogger(__name__)

app = FastAPI(title="Events Framework API", version="0.1.0")


_storage: Optional[StorageAdapter] = None
_registry: Optional[Registry] = None
_known_sources: Optional[set[str]] = None


def setup(storage: StorageAdapter, registry: Registry, known_sources: Optional[set[str]] = None) -> None:
    global _storage, _registry, _known_sources
    _storage = storage
    _registry = registry
    _known_sources = known_sources

@app.get("/events/", response_model=list[Event])
def list_events(
    source: Optional[str] = Query(None),
    type_: Optional[str] = Query(None, alias="type"),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    if _storage is None:
        raise HTTPException(status_code=503, detail="Storage no inicializado")

    if source and _known_sources is not None and source not in _known_sources:
        raise HTTPException(status_code=404, detail=f"Fonte '{source}' non existe")

    filter_spec = {}
    if source:
        filter_spec["source"] = source
    if type_:
        filter_spec["type_"] = type_
    if date_from:
        filter_spec["date_from"] = date_from
    if date_to:
        filter_spec["date_to"] = date_to

    results = _storage.query(filter_spec or None)
    return results[offset: offset + limit]


@app.get("/events/{event_id}", response_model=Event)
def get_event(event_id: int):
    if _storage is None:
        raise HTTPException(status_code=503, detail="Storage no inicializado")

    results = _storage.query({"id": event_id})
    if not results:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return results[0]


@app.get("/events/schema/{type_id}")
def get_schema(type_id: str):
    if _registry is None:
        raise HTTPException(status_code=503, detail="Registry no inicializado")

    event_type = _registry.get(type_id)
    if event_type is None:
        raise HTTPException(status_code=404, detail=f"EventType '{type_id}' no encontrado")
    return event_type.json_schema
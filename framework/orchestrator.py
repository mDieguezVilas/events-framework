import logging
from typing import Any
from framework.models import EventPayload
from framework.storage.base import StorageAdapter
from framework.registry import Registry
from framework.source_manager import SourceManager
from framework.dedup import compute_fingerprint
from framework.publication.manager import PublicationManager

logger = logging.getLogger(__name__)


class Orchestrator:

    def __init__(
        self,
        storage: StorageAdapter,
        registry: Registry,
        source_manager: SourceManager,
        publication_manager: PublicationManager = None,
        sources_package: str = None,
    ):
        self._storage = storage
        self._registry = registry
        self._source_manager = source_manager
        self._pub_manager = publication_manager
        self._sources_package = sources_package

    def update(self) -> dict[str, Any]:
        """Ejecuta el ciclo completo: fetch → parse → validate → dedup → store → notify."""
        sources = self._source_manager.discover()
        if not sources:
            logger.warning("No se encontraron fuentes registradas")
            return {"total": 0, "saved": 0, "skipped": 0}

        all_payloads = self._source_manager.run_all(sources)

        total = 0
        saved = 0
        skipped = 0
        new_events = []

        for source_id, payloads in all_payloads.items():
            for payload in payloads:
                total += 1

                # Validar contra JSON Schema si existe el EventType
                if not self._validate(payload):
                    skipped += 1
                    continue

                # Calcular fingerprint y comprobar duplicado
                location = payload.data.get("location", "")
                event_date = str(payload.event_date) if payload.event_date else ""
                fp = compute_fingerprint(payload.name, payload.source, event_date, location)

                if self._storage.exists_fingerprint(fp):
                    logger.debug(f"Duplicado ignorado: {payload.name} ({source_id})")
                    skipped += 1
                    continue

                # Guardar evento y fingerprint
                event = self._storage.save_event(payload)
                self._storage.save_fingerprint(fp)
                new_events.append(event)
                saved += 1
                logger.info(f"Guardado: {payload.name} ({source_id})")

        # Publicar notificaciones si hay eventos nuevos
        if new_events and self._pub_manager:
            self._pub_manager.publish(new_events)

        return {"total": total, "saved": saved, "skipped": skipped}

    def _validate(self, payload: EventPayload) -> bool:
        """Valida payload contra el JSON Schema del EventType si existe."""
        event_type = self._registry.get(payload.type_)
        if event_type is None or not event_type.json_schema:
            return True

        try:
            import jsonschema
            jsonschema.validate(instance=payload.data, schema=event_type.json_schema)
            return True
        except jsonschema.ValidationError as e:
            logger.warning(f"Validación fallida para {payload.name}: {e.message}")
            return False
        except Exception as e:
            logger.warning(f"Error validando {payload.name}: {e}")
            return False

    def list_sources(self) -> list[str]:
        sources = self._source_manager.discover()
        return list(sources.keys())
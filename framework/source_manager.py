import importlib
import pkgutil
import time
import logging
from typing import Optional
from framework.models import EventPayload
from framework.sources.base import get_registered_sources, EventSource

logger = logging.getLogger(__name__)


class SourceManager:

    def __init__(self, sources_package: Optional[str] = None):
        self._sources_package = sources_package

    def discover(self) -> dict[str, EventSource]:
        if self._sources_package:
            try:
                pkg = importlib.import_module(self._sources_package)
                if hasattr(pkg, "__path__"):
                    for _, name, ispkg in pkgutil.iter_modules(pkg.__path__):
                        full_name = f"{self._sources_package}.{name}"
                        try:
                            importlib.import_module(full_name)
                            logger.debug(f"Importado: {full_name}")
                        except Exception as e:
                            logger.warning(f"Error importando {full_name}: {e}")
            except ModuleNotFoundError as e:
                logger.warning(f"No se pudo importar el paquete de fuentes: {e}")

        registered = get_registered_sources()
        logger.debug(f"Fuentes registradas: {list(registered.keys())}")

        instances = {}
        for source_id, cls in registered.items():
            if cls.enabled:
                instances[source_id] = cls()
        return instances

    def run_source(self, source: EventSource, retries: int = 3, delay: float = 2.0) -> list[EventPayload]:
        for attempt in range(1, retries + 1):
            try:
                raw = source.fetch()
                payloads = source.parse(raw)
                logger.info(f"{source.source_id}: {len(payloads)} eventos obtenidos")
                return payloads
            except Exception as e:
                logger.warning(f"{source.source_id}: intento {attempt}/{retries} fallido — {e}")
                if attempt < retries:
                    time.sleep(delay)
        logger.error(f"{source.source_id}: todos los intentos fallaron")
        return []

    def run_all(self, sources: dict[str, EventSource]) -> dict[str, list[EventPayload]]:
        results = {}
        for source_id, source in sources.items():
            results[source_id] = self.run_source(source)
        return results
# tests/test_orchestrator.py
import pytest
from framework.models import EventPayload, EventType
from framework.storage.csv_storage import CSVStorage
from framework.registry import Registry
from framework.source_manager import SourceManager
from framework.orchestrator import Orchestrator
from framework.sources.base import EventSource, event_source, _REGISTRY


@pytest.fixture(autouse=True)
def limpiar_registry():
    """Limpia el registro de fuentes entre tests."""
    _REGISTRY.clear()
    yield
    _REGISTRY.clear()


@pytest.fixture
def orchestrator(tmp_path):
    storage = CSVStorage(data_dir=tmp_path)
    storage.init()
    registry = Registry(path=tmp_path / "registry.json")
    registry.init()
    source_manager = SourceManager()
    return Orchestrator(storage, registry, source_manager)


def make_source(source_id: str, payloads: list[EventPayload]):
    @event_source(source_id=source_id, enabled=True)
    class TestSource(EventSource):
        def fetch(self): return []
        def parse(self, raw): return payloads
    return TestSource


def test_update_guarda_eventos(orchestrator):
    make_source("test", [
        EventPayload(type_="race", name="10K", url="u", source="test")
    ])
    result = orchestrator.update()
    assert result["saved"] == 1
    assert result["skipped"] == 0


def test_update_deduplica_misma_fuente(orchestrator):
    payload = EventPayload(type_="race", name="10K", url="u", source="test")
    make_source("test", [payload, payload])
    result = orchestrator.update()
    assert result["saved"] == 1
    assert result["skipped"] == 1


def test_update_sin_fuentes(orchestrator):
    result = orchestrator.update()
    assert result["total"] == 0


def test_list_sources(orchestrator):
    make_source("fga", [])
    sources = orchestrator.list_sources()
    assert "fga" in sources
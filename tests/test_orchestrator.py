# tests/test_orchestrator.py
import pytest
from framework.models import EventPayload, EventType
from framework.storage.csv_storage import CSVStorage
from framework.registry import Registry
from framework.source_manager import SourceManager
from framework.orchestrator import Orchestrator
from framework.sources.base import EventSource, event_source, _REGISTRY
from unittest.mock import MagicMock
from framework.publication.base import NotificationAdapter


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
    

def test_update_no_deduplica_cross_source(orchestrator):
    """Eventos con el mismo nombre de fuentes distintas NO se deduplicán entre sí."""
    payload_fga = EventPayload(type_="race", name="10K Santiago", url="u", source="fga")
    payload_kro = EventPayload(type_="race", name="10K Santiago", url="u", source="kronotime")

    make_source("fga", [payload_fga])
    make_source("kronotime", [payload_kro])

    result = orchestrator.update()
    assert result["saved"] == 2
    assert result["skipped"] == 0

def test_publication_manager_llama_a_adapters(orchestrator):
    """Verifica que el PublicationManager llama a send() de cada adapter."""
    mock_adapter = MagicMock(spec=NotificationAdapter)

    from framework.publication.manager import PublicationManager
    pub_manager = PublicationManager(adapters=[mock_adapter])

    from framework.storage.csv_storage import CSVStorage
    from framework.registry import Registry
    import tempfile, os
    tmp = tempfile.mkdtemp()

    storage = CSVStorage(data_dir=tmp)
    storage.init()
    registry = Registry(path=os.path.join(tmp, "registry.json"))
    registry.init()

    from framework.source_manager import SourceManager
    from framework.orchestrator import Orchestrator
    source_manager = SourceManager()

    orch = Orchestrator(storage, registry, source_manager, pub_manager)
    make_source("notify_test", [
        EventPayload(type_="race", name="Test Event", url="u", source="notify_test")
    ])

    orch.update()
    mock_adapter.send.assert_called_once()


def test_publication_manager_no_llama_si_no_hay_eventos(orchestrator):
    """Si no hay eventos nuevos no se llaman los adapters."""
    mock_adapter = MagicMock(spec=NotificationAdapter)

    from framework.publication.manager import PublicationManager
    pub_manager = PublicationManager(adapters=[mock_adapter])

    from framework.storage.csv_storage import CSVStorage
    from framework.registry import Registry
    import tempfile, os
    tmp = tempfile.mkdtemp()

    storage = CSVStorage(data_dir=tmp)
    storage.init()
    registry = Registry(path=os.path.join(tmp, "registry.json"))
    registry.init()

    from framework.source_manager import SourceManager
    from framework.orchestrator import Orchestrator
    source_manager = SourceManager()

    orch = Orchestrator(storage, registry, source_manager, pub_manager)
    # No registramos ninguna fuente → no hay eventos
    result = orch.update()
    assert result["saved"] == 0
    mock_adapter.send.assert_not_called()
import pytest
from framework.models import EventPayload
from framework.sources.base import EventSource, event_source, _REGISTRY
from framework.source_manager import SourceManager


@pytest.fixture(autouse=True)
def limpiar_registry():
    _REGISTRY.clear()
    yield
    _REGISTRY.clear()


def make_source(source_id: str, payloads: list[EventPayload], enabled: bool = True):
    @event_source(source_id=source_id, enabled=enabled)
    class TestSource(EventSource):
        def fetch(self): return []
        def parse(self, raw): return payloads
    return TestSource


def test_discover_devuelve_fuentes_registradas():
    make_source("fga", [])
    sm = SourceManager()
    sources = sm.discover()
    assert "fga" in sources


def test_discover_ignora_fuentes_deshabilitadas():
    make_source("fga", [], enabled=False)
    sm = SourceManager()
    sources = sm.discover()
    assert "fga" not in sources


def test_discover_multiples_fuentes():
    make_source("fga", [])
    make_source("kronotime", [])
    sm = SourceManager()
    sources = sm.discover()
    assert "fga" in sources
    assert "kronotime" in sources
    assert len(sources) == 2


def test_run_source_devuelve_payloads():
    payload = EventPayload(type_="race", name="10K", url="u", source="fga")
    make_source("fga", [payload])
    sm = SourceManager()
    sources = sm.discover()
    result = sm.run_source(sources["fga"])
    assert len(result) == 1
    assert result[0].name == "10K"


def test_run_source_reintenta_si_falla():
    call_count = {"n": 0}

    @event_source(source_id="failing", enabled=True)
    class FailingSource(EventSource):
        def fetch(self):
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise Exception("Error simulado")
            return []
        def parse(self, raw): return []

    sm = SourceManager()
    sources = sm.discover()
    result = sm.run_source(sources["failing"], retries=3, delay=0)
    assert call_count["n"] == 3
    assert result == []


def test_run_source_devuelve_vacio_si_todos_fallan():
    @event_source(source_id="always_fails", enabled=True)
    class AlwaysFailsSource(EventSource):
        def fetch(self): raise Exception("Siempre falla")
        def parse(self, raw): return []

    sm = SourceManager()
    sources = sm.discover()
    result = sm.run_source(sources["always_fails"], retries=2, delay=0)
    assert result == []


def test_run_all_ejecuta_todas_las_fuentes():
    make_source("fga", [EventPayload(type_="race", name="A", url="u", source="fga")])
    make_source("kronotime", [EventPayload(type_="race", name="B", url="u", source="kronotime")])
    sm = SourceManager()
    sources = sm.discover()
    results = sm.run_all(sources)
    assert "fga" in results
    assert "kronotime" in results
    assert len(results["fga"]) == 1
    assert len(results["kronotime"]) == 1
import pytest
from fastapi.testclient import TestClient
from framework.api import app, setup
from framework.models import EventPayload
from framework.storage.csv_storage import CSVStorage
from framework.registry import Registry


@pytest.fixture
def client(tmp_path):
    storage = CSVStorage(data_dir=tmp_path)
    storage.init()
    registry = Registry(path=tmp_path / "registry.json")
    registry.init()
    setup(storage, registry)
    return TestClient(app)


@pytest.fixture
def client_con_eventos(tmp_path):
    storage = CSVStorage(data_dir=tmp_path)
    storage.init()
    registry = Registry(path=tmp_path / "registry.json")
    registry.init()
    setup(storage, registry)

    storage.save_event(EventPayload(type_="race", name="10K Vigo", url="https://ex.gal", source="fga"))
    storage.save_event(EventPayload(type_="race", name="5K Baiona", url="https://ex.gal", source="kronotime"))
    storage.save_event(EventPayload(type_="conference", name="PyConES", url="https://ex.gal", source="manual"))

    return TestClient(app)


def test_list_events_vacio(client):
    response = client.get("/events/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_events_devuelve_eventos(client_con_eventos):
    response = client_con_eventos.get("/events/")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_list_events_filtro_source(client_con_eventos):
    response = client_con_eventos.get("/events/?source=fga")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "10K Vigo"


def test_list_events_filtro_type(client_con_eventos):
    response = client_con_eventos.get("/events/?type=race")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_list_events_paginacion(client_con_eventos):
    response = client_con_eventos.get("/events/?limit=2&offset=0")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_events_paginacion_offset(client_con_eventos):
    response = client_con_eventos.get("/events/?limit=2&offset=2")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_event_por_id(client_con_eventos):
    response = client_con_eventos.get("/events/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["name"] == "10K Vigo"


def test_get_event_no_existe(client_con_eventos):
    response = client_con_eventos.get("/events/999")
    assert response.status_code == 404


def test_get_schema_no_existe(client):
    response = client.get("/events/schema/noexiste")
    assert response.status_code == 404


def test_get_schema_existente(tmp_path):
    from framework.models import EventType
    from framework.api import setup

    storage = CSVStorage(data_dir=tmp_path)
    storage.init()
    registry = Registry(path=tmp_path / "registry.json")
    registry.init()

    et = EventType(
        type_id="race",
        json_schema={"type": "object", "properties": {"location": {"type": "string"}}}
    )
    registry.register(et)
    setup(storage, registry)

    client = TestClient(app)
    response = client.get("/events/schema/race")
    assert response.status_code == 200
    assert "properties" in response.json()
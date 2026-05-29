import pytest
from datetime import datetime
from framework.models import EventPayload
from framework.storage.csv_storage import CSVStorage


@pytest.fixture
def storage(tmp_path):
    s = CSVStorage(data_dir=tmp_path)
    s.init()
    return s


def test_init_crea_fichero(tmp_path):
    s = CSVStorage(data_dir=tmp_path)
    s.init()
    assert (tmp_path / "events.csv").exists()


def test_save_event_asigna_id(storage):
    p = EventPayload(type_="race", name="10K Santiago", url="https://ex.gal",
                     source="fga", event_date=datetime.now())
    event = storage.save_event(p)
    assert event.id == 1


def test_save_event_incrementa_id(storage):
    p1 = EventPayload(type_="race", name="10K", url="https://ex.gal", source="fga")
    p2 = EventPayload(type_="race", name="5K", url="https://ex.gal", source="fga")
    e1 = storage.save_event(p1)
    e2 = storage.save_event(p2)
    assert e1.id == 1
    assert e2.id == 2


def test_query_devuelve_eventos_guardados(storage):
    p = EventPayload(type_="race", name="10K Santiago", url="https://ex.gal",
                     source="fga", event_date=datetime.now(),
                     data={"location": "Santiago"})
    storage.save_event(p)
    results = storage.query()
    assert len(results) == 1
    assert results[0].name == "10K Santiago"
    assert results[0].data["location"] == "Santiago"


def test_query_sin_filtro_devuelve_todos(storage):
    for i in range(3):
        storage.save_event(EventPayload(type_="race", name=f"Carreira {i}",
                                        url="https://ex.gal", source="fga"))
    assert len(storage.query()) == 3


def test_query_filtro_source(storage):
    storage.save_event(EventPayload(type_="race", name="A", url="u", source="fga"))
    storage.save_event(EventPayload(type_="race", name="B", url="u", source="kronotime"))
    results = storage.query({"source": "fga"})
    assert len(results) == 1
    assert results[0].name == "A"


def test_query_filtro_type(storage):
    storage.save_event(EventPayload(type_="race", name="A", url="u", source="fga"))
    storage.save_event(EventPayload(type_="conference", name="B", url="u", source="fga"))
    results = storage.query({"type_": "race"})
    assert len(results) == 1
    assert results[0].type_ == "race"


def test_fingerprint_no_existe(storage):
    assert not storage.exists_fingerprint("abc123")


def test_fingerprint_guardado(storage):
    storage.save_fingerprint("abc123")
    assert storage.exists_fingerprint("abc123")


def test_fingerprint_persiste_entre_instancias(tmp_path):
    s1 = CSVStorage(data_dir=tmp_path)
    s1.init()
    s1.save_fingerprint("abc123")

    s2 = CSVStorage(data_dir=tmp_path)
    s2.init()
    assert s2.exists_fingerprint("abc123")


def test_capabilities(storage):
    caps = storage.capabilities()
    assert "export" in caps
    assert "import" in caps


def test_get_promoted_fields_devuelve_lista_vacia(storage):
    result = storage.get_promoted_fields()
    assert result == []


def test_promote_field_no_hace_nada(storage):
    storage.promote_field("race", "location")
    assert storage.get_promoted_fields() == []
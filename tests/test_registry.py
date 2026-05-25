# tests/test_registry.py
import pytest
from framework.models import EventType
from framework.registry import Registry


@pytest.fixture
def registry(tmp_path):
    reg = Registry(path=tmp_path / "registry.json")
    reg.init()
    return reg


@pytest.fixture
def race_type():
    return EventType(
        type_id="race",
        description="Carreira popular",
        json_schema={
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "distance": {"type": "string"},
            },
            "required": ["location"],
        }
    )


def test_register_y_get(registry, race_type):
    registry.register(race_type)
    result = registry.get("race")
    assert result is not None
    assert result.type_id == "race"


def test_get_no_existente_devuelve_none(registry):
    assert registry.get("noexiste") is None


def test_all_devuelve_lista(registry, race_type):
    registry.register(race_type)
    all_types = registry.all()
    assert len(all_types) == 1
    assert all_types[0].type_id == "race"


def test_register_multiples(registry):
    registry.register(EventType(type_id="race", json_schema={}))
    registry.register(EventType(type_id="conference", json_schema={}))
    assert len(registry.all()) == 2


def test_persiste_en_disco(tmp_path, race_type):
    path = tmp_path / "registry.json"
    reg = Registry(path=path)
    reg.init()
    reg.register(race_type)
    assert path.exists()


def test_recarga_desde_disco(tmp_path, race_type):
    path = tmp_path / "registry.json"
    reg1 = Registry(path=path)
    reg1.init()
    reg1.register(race_type)

    reg2 = Registry(path=path)
    reg2.init()
    result = reg2.get("race")
    assert result is not None
    assert result.type_id == "race"
    assert "location" in result.json_schema["properties"]


def test_sobreescribe_tipo_existente(registry, race_type):
    registry.register(race_type)
    updated = EventType(type_id="race", description="actualizado", json_schema={})
    registry.register(updated)
    assert registry.get("race").description == "actualizado"
    assert len(registry.all()) == 1
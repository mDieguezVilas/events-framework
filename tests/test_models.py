# tests/test_models.py
from datetime import date
from framework.models import Event, EventPayload, EventType


def test_event_fields():
    e = Event(type_="race", name="10K Santiago", url="https://ex.gal", source="fga")
    assert e.type_ == "race"
    assert e.id is None


def test_event_with_data():
    e = Event(type_="race", name="10K Santiago", url="https://ex.gal", source="fga",
              event_date=date(2025, 3, 10), data={"location": "Santiago", "distance": "10K"})
    assert e.data["location"] == "Santiago"
    assert e.event_date == date(2025, 3, 10)


def test_event_payload_to_event():
    p = EventPayload(type_="race", name="10K", url="https://ex.gal", source="fga",
                     event_date=date(2025, 3, 10), data={"location": "Santiago"})
    e = p.to_event()
    assert isinstance(e, Event)
    assert e.id is None
    assert e.type_ == "race"
    assert e.data["location"] == "Santiago"


def test_event_payload_to_event_preserves_all_fields():
    p = EventPayload(type_="race", name="10K", url="https://ex.gal", source="fga",
                     event_date=date(2025, 3, 10), data={"location": "Santiago"})
    e = p.to_event()
    assert e.name == p.name
    assert e.url == p.url
    assert e.source == p.source
    assert e.event_date == p.event_date
    assert e.data == p.data


def test_event_type():
    et = EventType(
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
    assert et.type_id == "race"
    assert "location" in et.json_schema["properties"]


def test_event_type_is_frozen():
    et = EventType(type_id="race", json_schema={})
    try:
        et.type_id = "conference"
        assert False, "debería haber lanzado error"
    except Exception:
        pass
import pytest
import csv
from pathlib import Path
from datetime import date
from framework.sources.csv_source import CSVSource
from framework.sources.base import _REGISTRY


@pytest.fixture(autouse=True)
def limpiar_registry():
    _REGISTRY.clear()
    yield
    _REGISTRY.clear()


@pytest.fixture
def csv_path(tmp_path):
    path = tmp_path / "events.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "url", "location", "distance", "event_date"])
        writer.writeheader()
        writer.writerow({
            "name": "10K Vigo",
            "url": "https://ex.gal/10k",
            "location": "Vigo",
            "distance": "10K",
            "event_date": "2025-05-10",
        })
        writer.writerow({
            "name": "5K Baiona",
            "url": "https://ex.gal/5k",
            "location": "Baiona",
            "distance": "5K",
            "event_date": "2025-06-01",
        })
    return path


@pytest.fixture
def source(csv_path):
    return CSVSource(csv_path=str(csv_path))


def test_fetch_devuelve_filas(source):
    raw = source.fetch()
    assert len(raw) == 2


def test_fetch_fichero_no_existe():
    source = CSVSource(csv_path="data/no_existe.csv")
    raw = source.fetch()
    assert raw == []


def test_parse_devuelve_payloads(source):
    raw = source.fetch()
    payloads = source.parse(raw)
    assert len(payloads) == 2


def test_parse_campos_correctos(source):
    raw = source.fetch()
    payloads = source.parse(raw)
    p = payloads[0]
    assert p.name == "10K Vigo"
    assert p.source == "csv_manual"
    assert p.type_ == "race"
    assert p.event_date.date() == date(2025, 5, 10)  # ← .date() para comparar solo la fecha
    assert p.data["location"] == "Vigo"
    assert p.data["distance"] == "10K"


def test_parse_sin_fecha(tmp_path):
    path = tmp_path / "sin_fecha.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "url", "location", "distance", "event_date"])
        writer.writeheader()
        writer.writerow({
            "name": "Carreira Sen Data",
            "url": "https://ex.gal",
            "location": "Vigo",
            "distance": "5K",
            "event_date": "",
        })
    source = CSVSource(csv_path=str(path))
    payloads = source.parse(source.fetch())
    assert len(payloads) == 1
    assert payloads[0].event_date is None


def test_parse_ignora_filas_invalidas(tmp_path):
    path = tmp_path / "invalido.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "url", "location", "distance", "event_date"])
        writer.writeheader()
        # Fila sin name ni url — debe ignorarse
        writer.writerow({
            "name": "",
            "url": "",
            "location": "Vigo",
            "distance": "5K",
            "event_date": "2025-05-10",
        })
    source = CSVSource(csv_path=str(path))
    payloads = source.parse(source.fetch())
    assert len(payloads) == 0
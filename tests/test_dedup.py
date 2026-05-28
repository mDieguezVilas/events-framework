# tests/test_dedup.py
from framework.dedup import normalize, compute_fingerprint


def test_normalize_minusculas():
    assert normalize("SANTIAGO") == "santiago"


def test_normalize_acentos():
    assert normalize("Coruña") == "coruna"


def test_normalize_espacios():
    assert normalize("  10K  ") == "10k"


def test_normalize_vacio():
    assert normalize("") == ""
    assert normalize(None) == "" # type: ignore


def test_fingerprint_mismo_evento():
    fp1 = compute_fingerprint("10K Santiago", "fga", "2025-03-10", "Santiago")
    fp2 = compute_fingerprint("10K Santiago", "fga", "2025-03-10", "Santiago")
    assert fp1 == fp2


def test_fingerprint_diferente_source():
    fp1 = compute_fingerprint("10K Santiago", "fga", "2025-03-10", "Santiago")
    fp2 = compute_fingerprint("10K Santiago", "kronotime", "2025-03-10", "Santiago")
    assert fp1 != fp2


def test_fingerprint_normaliza_acentos():
    fp1 = compute_fingerprint("10K Coruña", "fga", "", "")
    fp2 = compute_fingerprint("10K Coruna", "fga", "", "")
    assert fp1 == fp2
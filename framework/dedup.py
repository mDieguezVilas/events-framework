import hashlib
import unicodedata
from typing import Optional


def normalize(text: Optional[str]) -> str:
    if not text:
        return ""
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode()
        .lower()
        .strip()
    )


def compute_fingerprint(name: str, source: str, event_date: str = "", location: str = "") -> str:
    raw = f"{normalize(name)}|{source}|{normalize(event_date)}|{normalize(location)}"
    return hashlib.sha256(raw.encode()).hexdigest()
import json
import logging
from datetime import date
from typing import Any, Optional

from sqlalchemy import create_engine, text, Column, Integer, String, Date, Text
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.dialects.postgresql import JSONB

from framework.models import Event, EventPayload
from framework.storage.base import StorageAdapter

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class EventRow(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_ = Column("type_", String, nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    source = Column(String, nullable=False)
    event_date = Column(Date, nullable=True)
    data = Column(JSONB, nullable=False, default=dict)


class FingerprintRow(Base):
    __tablename__ = "fingerprints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fingerprint = Column(String, nullable=False, unique=True)


class SQLStorage(StorageAdapter):

    def __init__(self, database_url: str):
        self._database_url = database_url
        self._engine = None

    def init(self) -> None:
        self._engine = create_engine(self._database_url)
        Base.metadata.create_all(self._engine)
        logger.info("SQLStorage inicializado y tablas creadas")

    def save_event(self, payload: EventPayload) -> Event:
        with Session(self._engine) as session:
            row = EventRow(
                type_=payload.type_,
                name=payload.name,
                url=payload.url,
                source=payload.source,
                event_date=payload.event_date,
                data=payload.data,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return self._row_to_event(row)

    def bulk_save(self, payloads: list[EventPayload]) -> list[Event]:
        return [self.save_event(p) for p in payloads]

    def query(self, filter_spec: Optional[dict[str, Any]] = None) -> list[Event]:
        with Session(self._engine) as session:
            stmt = "SELECT id, type_, name, url, source, event_date, data FROM events WHERE 1=1"
            params: dict[str, Any] = {}

            if filter_spec:
                if "id" in filter_spec:
                    stmt += " AND id = :id"
                    params["id"] = filter_spec["id"]
                if "source" in filter_spec:
                    stmt += " AND source = :source"
                    params["source"] = filter_spec["source"]
                if "type_" in filter_spec:
                    stmt += " AND type_ = :type_"
                    params["type_"] = filter_spec["type_"]
                if "date_from" in filter_spec:
                    stmt += " AND event_date >= :date_from"
                    params["date_from"] = filter_spec["date_from"]
                if "date_to" in filter_spec:
                    stmt += " AND event_date <= :date_to"
                    params["date_to"] = filter_spec["date_to"]

            rows = session.execute(text(stmt), params).fetchall()
            return [self._row_to_event(r) for r in rows]

    def exists_fingerprint(self, fingerprint: str) -> bool:
        with Session(self._engine) as session:
            result = session.execute(
                text("SELECT 1 FROM fingerprints WHERE fingerprint = :fp"),
                {"fp": fingerprint}
            ).fetchone()
            return result is not None

    def save_fingerprint(self, fingerprint: str) -> None:
        with Session(self._engine) as session:
            session.add(FingerprintRow(fingerprint=fingerprint))
            session.commit()

    def capabilities(self) -> set[str]:
        return {"promotion", "transactions", "query_pushdown"}

    def close(self) -> None:
        if self._engine:
            self._engine.dispose()

    def _row_to_event(self, row) -> Event:
        return Event(
            id=row.id,
            type_=row.type_,
            name=row.name,
            url=row.url,
            source=row.source,
            event_date=row.event_date,
            data=row.data or {},
        )


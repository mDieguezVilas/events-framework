from datetime import date
from typing import Any, Optional
from pydantic import BaseModel, Field


class EventType(BaseModel):
    type_id: str
    description: str = ""
    json_schema: dict[str, Any]

    model_config = {"frozen": True}


class Event(BaseModel):
    id: Optional[int] = None
    type_: str
    name: str
    url: str
    source: str
    event_date: Optional[date] = None
    data: dict[str, Any] = Field(default_factory=dict)


class EventPayload(BaseModel):
    type_: str
    name: str
    url: str
    source: str
    event_date: Optional[date] = None
    data: dict[str, Any] = Field(default_factory=dict)

    def to_event(self) -> Event:
        return Event(**self.model_dump())
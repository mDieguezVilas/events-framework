from framework.models import EventPayload
from framework.sources.base import EventSource, event_source
from datetime import datetime


@event_source(source_id="example", enabled=True)
class ExampleSource(EventSource):

    def fetch(self):
        return [
            {"name": "10K Santiago", "url": "https://ex.gal/10k", "location": "Santiago", "date": "2025-03-10"},
            {"name": "Trail Arousa", "url": "https://ex.gal/trail", "location": "Arousa", "date": "2025-04-20"},
        ]

    def parse(self, raw):
        payloads = []
        for item in raw:
            payloads.append(EventPayload(
                type_="race",
                name=item["name"],
                url=item["url"],
                source=self.source_id,
                event_date=datetime.fromisoformat(item["date"]),
                data={"location": item["location"]},
            ))
        return payloads
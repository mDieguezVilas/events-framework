# events-framework

Framework en Python para a recompilación, normalización e centralización
de eventos procedentes de fontes heteroxéneas (scraping, APIs, CSV).

Desenvolvido como Traballo de Fin de Grao (TFG) de Enxeñaría Informática.

## Características

- Extracción automatizada desde múltiples fontes (scraping, API REST, CSV)
- Validación con JSON Schema por tipo de evento
- Deduplicación por fingerprint SHA-256 (dentro da mesma fonte)
- Almacenamento intercambiable: CSVStorage e SQLStorage (Postgres + JSONB)
- Publicación de notificacións: Telegram e SMTP con modo resumo
- API REST con FastAPI: filtros, paginación e documentación automática
- Promoción de campos JSONB a columnas físicas con índice (promote-field)
- CLI con Typer: update, list-sources, serve-api, promote-field

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Configuración

Crea un ficheiro `config.yaml` na raíz do proxecto:

```yaml
storage:
  type: csv        # ou 'sql' para Postgres
  data_dir: data

sources:
  miña_fonte:
    enabled: true
    schedule: "0 9 * * *"

notifications:
  telegram:
    enabled: false
    token_env: TELEGRAM_TOKEN
    chat_id_env: TELEGRAM_CHAT_ID
  smtp:
    enabled: false
    summary: false

sources_package: sources
```

Crea un ficheiro `.env` con las credenciales:

```.env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost/mi_db
TELEGRAM_TOKEN=
TELEGRAM_CHAT_ID=
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
SMTP_FROM=
SMTP_TO=
```

## Uso

```bash
# Executar o ciclo completo
framework update

# Ver as fontes rexistradas
framework list-sources

# Arrancar a API REST
framework serve-api

# Promover un campo a columna física (só SQLStorage)
framework promote-field race location
```

## Rexistrar unha fonte nova

```python
from framework.models import EventPayload
from framework.sources.base import EventSource, event_source
from datetime import datetime

@event_source(source_id="miña_fonte", enabled=True)
class MiñaFonte(EventSource):

    def fetch(self):
        # Descarga os datos (HTML, JSON, CSV...)
        return []

    def parse(self, raw):
        return [
            EventPayload(
                type_="race",
                name=item["name"],
                url=item["url"],
                source=self.source_id,
                event_date=datetime.now(),
                data={"location": item["location"]},
            )
            for item in raw
        ]
```

## Modelo de evento

| Campo       | Tipo     | Descripción                             |
|-------------|----------|-----------------------------------------|
| id          | int      | Asignado polo Storage                   |
| type_       | str      | Tipo de evento (ex: race)               |
| name        | str      | Nome do evento                          |
| url         | str      | URL de referencia                       |
| source      | str      | Identificador da fonte                  |
| event_date  | datetime | Data e hora da búsqueda (auto)          |
| data        | dict     | Campos específicos do EventType         |

## Estrutura do proxecto

framework/
├── models.py           # Event, EventType, EventPayload
├── registry.py         # Rexistro de EventTypes
├── orchestrator.py     # Coordina o ciclo completo
├── dedup.py            # Fingerprint SHA-256
├── source_manager.py   # Descubrimento e execución de fontes
├── config.py           # Lectura de config.yaml
├── cli.py              # Comandos CLI
├── api.py              # API REST con FastAPI
├── sources/            # EventSource base e decorador
├── storage/            # CSVStorage e SQLStorage
└── publication/        # Telegram, SMTP, PublicationManager


## Tests

```bash
pytest tests/ -v --cov=framework --cov-report=term-missing
```

## Stack tecnolóxico

- Python 3.11+
- Pydantic v2, Typer, FastAPI, SQLAlchemy 2.0
- Postgres + JSONB, httpx, pytest


## Licenza

MIT
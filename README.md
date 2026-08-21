# Events Framework

Framework en Python para construir pipelines de recolección, deduplicación, almacenamiento, exposición y notificación de eventos a partir de fuentes externas heterogéneas (scrapers, APIs, ficheros CSV, etc.).

Está pensado como una base extensible: se definen **fuentes** (`EventSource`) que producen eventos, un **orquestador** que las ejecuta, valida y deduplica los resultados, un **almacenamiento** intercambiable (CSV o SQL/Postgres) y **adaptadores de publicación** (Telegram, email) que notifican cuando aparecen eventos nuevos. Todo el pipeline se controla desde una CLI (`framework`) y los datos guardados se pueden consultar a través de una API REST (FastAPI).

## Índice

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Crear una fuente propia](#crear-una-fuente-propia)
- [Almacenamiento](#almacenamiento)
- [Notificaciones](#notificaciones)
- [API REST](#api-rest)
- [Testing](#testing)
- [Estructura del proyecto](#estructura-del-proyecto)

## Características

- **Fuentes conectables (plug-in)**: cualquier módulo dentro de un paquete configurable se descubre e importa automáticamente mediante un decorador de registro (`@event_source`).
- **Deduplicación por huella (fingerprint)**: cada evento se identifica mediante un hash SHA-256 calculado a partir de nombre, fuente, fecha y ubicación normalizados (sin tildes, minúsculas), evitando duplicados entre ejecuciones.
- **Validación por esquema**: los eventos se validan contra un `json_schema` asociado a su `EventType`, gestionado por un `Registry` persistido en disco.
- **Almacenamiento intercambiable**: adaptador CSV (sin dependencias externas, ideal para desarrollo) o SQL sobre PostgreSQL (con soporte de JSONB) mediante SQLAlchemy.
- **Promoción de campos**: en el backend SQL, cualquier campo dentro del JSONB `data` puede "promoverse" a columna física indexada mediante `ALTER TABLE` + backfill por lotes, sin downtime del resto del pipeline.
- **Notificaciones desacopladas**: un `PublicationManager` distribuye los eventos nuevos a cualquier número de adaptadores (Telegram, SMTP) configurables de forma independiente.
- **API REST**: consulta de eventos con filtros por fuente, tipo y rango de fechas, paginación, y consulta de esquemas de tipos de evento.
- **CLI unificada**: un único comando `framework` para ejecutar el pipeline, listar fuentes, levantar la API y promover campos.
- **Reintentos automáticos**: cada fuente se ejecuta con reintentos configurables y backoff fijo ante fallos de red o parseo.

## Arquitectura

El flujo de una ejecución completa (`framework update`) es el siguiente:

1. **`SourceManager.discover()`** importa dinámicamente el paquete de fuentes configurado (`sources_package`) e instancia todas las clases registradas con `@event_source` que estén marcadas como `enabled`.
2. **`SourceManager.run_all()`** ejecuta `fetch()` + `parse()` de cada fuente, con reintentos ante excepciones, devolviendo una lista de `EventPayload`.
3. **`Orchestrator.update()`**:
   - Valida cada `EventPayload` contra el `json_schema` de su `EventType` en el `Registry` (si existe).
   - Calcula el `fingerprint` (nombre + fuente + fecha + ubicación normalizados) y descarta los eventos ya vistos.
   - Persiste los eventos nuevos y sus fingerprints en el `StorageAdapter` configurado.
   - Publica los eventos nuevos a través del `PublicationManager` (Telegram / SMTP).
4. **`framework serve-api`** expone los eventos almacenados vía FastAPI, reutilizando el mismo `StorageAdapter` y `Registry`.

```
                ┌────────────────┐
                │  config.yaml   │
                └───────┬────────┘
                        │
                ┌───────▼────────┐
 sources_pkg →  │  SourceManager │  descubre y ejecuta fuentes (@event_source)
                └───────┬────────┘
                        │ list[EventPayload]
                ┌───────▼────────┐
                │  Orchestrator  │  valida (Registry) + deduplica (dedup.py)
                └───────┬────────┘
             ┌──────────┴───────────┐
     ┌───────▼────────┐    ┌────────▼─────────┐
     │ StorageAdapter │    │ PublicationManager│
     │  CSV / SQL     │    │  Telegram / SMTP  │
     └───────┬────────┘    └──────────────────┘
             │
     ┌───────▼────────┐
     │   FastAPI app  │  GET /events, /events/{id}, /events/schema/{type}
     └────────────────┘
```

## Instalación

Requiere **Python 3.11+**.

```bash
git clone <url-del-repositorio>
cd events-framework
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -e .
```

Para desarrollo (tests, cobertura):

```bash
pip install -e ".[dev]"
```

Esto expone el comando `framework` en el entorno virtual (definido como script en `pyproject.toml`).

## Configuración

### `config.yaml`

El framework lee por defecto un fichero `config.yaml` en el directorio de trabajo:

```yaml
storage:
  type: sql            # "csv" o "sql"
  data_dir: data        # usado solo si type = csv

sources:
  example:
    enabled: true
    schedule: "0 9 * * *"    # informativo; el scheduling real lo gestiona algo externo (cron, etc.)
  csv_manual:
    enabled: true
    schedule: "0 10 * * *"

notifications:
  telegram:
    enabled: false
    token_env: TELEGRAM_TOKEN
    chat_id_env: TELEGRAM_CHAT_ID
  smtp:
    enabled: false
    summary: false      # true = un único email resumen; false = un email por evento

sources_package: framework.sources   # paquete Python donde se buscan las fuentes
```

> La lista `sources` es informativa/documental: qué fuentes están habilitadas se decide realmente por el atributo `enabled` del decorador `@event_source` en cada clase. `schedule` no lo interpreta el framework — está pensado para integrarse con un cron o un scheduler externo.

### Variables de entorno (`.env`)

El framework carga automáticamente un fichero `.env` (vía `python-dotenv`). Variables relevantes:

| Variable | Uso |
|---|---|
| `DATABASE_URL` | Cadena de conexión SQLAlchemy para `SQLStorage` (obligatoria si `storage.type: sql`), p. ej. `postgresql+psycopg://usuario:pass@host:5432/bd` |
| `TELEGRAM_TOKEN` | Token del bot de Telegram (nombre configurable vía `token_env`) |
| `TELEGRAM_CHAT_ID` | ID del chat/canal destino (nombre configurable vía `chat_id_env`) |
| `SMTP_HOST` | Host del servidor SMTP |
| `SMTP_PORT` | Puerto SMTP (por defecto `587`) |
| `SMTP_USER` | Usuario de autenticación SMTP |
| `SMTP_PASS` | Contraseña SMTP |
| `SMTP_FROM` | Dirección remitente |
| `SMTP_TO` | Dirección destinataria |

Las notificaciones de Telegram y SMTP solo se activan si, además de `enabled: true` en `config.yaml`, **todas** las variables de entorno necesarias están presentes; en caso contrario el adaptador correspondiente simplemente no se añade.

## Uso

Todos los comandos se ejecutan a través de la CLI `framework`.

### Ejecutar el pipeline completo

```bash
framework update
```

Descubre las fuentes habilitadas, las ejecuta, valida y deduplica los eventos, los guarda en el storage configurado y notifica los eventos nuevos. Devuelve un resumen:

```
Total: 12 | Guardados: 3 | Omitidos: 9
```

Se puede sobrescribir el paquete de fuentes sin tocar `config.yaml`:

```bash
framework update --sources-package mi_paquete.fuentes
```

### Listar fuentes registradas

```bash
framework list-sources
```

### Levantar la API REST

```bash
framework serve-api --host 0.0.0.0 --port 8000
```

### Promover un campo del JSONB a columna física (solo backend SQL)

```bash
framework promote-field race location
```

Pide confirmación interactiva antes de ejecutar el `ALTER TABLE`, ya que la operación no se puede deshacer automáticamente.

## Crear una fuente propia

Una fuente es una clase que hereda de `EventSource` e implementa `fetch()` (obtención de datos crudos) y `parse()` (conversión a `EventPayload`). Se registra con el decorador `@event_source`:

```python
# framework/sources/mi_fuente.py
from datetime import datetime
from framework.models import EventPayload
from framework.sources.base import EventSource, event_source


@event_source(source_id="mi_fuente", enabled=True)
class MiFuente(EventSource):

    def fetch(self):
        # Llamada HTTP, scraping, lectura de fichero, etc.
        return [{"nombre": "Carrera X", "url": "https://ejemplo.com/x", "fecha": "2026-05-01"}]

    def parse(self, raw):
        return [
            EventPayload(
                type_="race",
                name=item["nombre"],
                url=item["url"],
                source=self.source_id,
                event_date=datetime.fromisoformat(item["fecha"]),
                data={"location": "Vigo"},
            )
            for item in raw
        ]
```

Basta con que el módulo viva dentro del paquete indicado en `sources_package` (por defecto `framework.sources`): el `SourceManager` lo importará automáticamente y quedará disponible para `framework update`.

Si `fetch()` o `parse()` lanzan una excepción, la fuente se reintenta (por defecto 3 intentos con 2 segundos de espera) antes de descartarse para esa ejecución, sin afectar al resto de fuentes.

### Fuentes incluidas de ejemplo

- **`example`**: fuente de demostración con datos embebidos en el propio código.
- **`csv_manual`**: lee eventos desde un CSV local (`data/sample_events.csv` por defecto) con columnas `name`, `url`, `location`, `distance`, `event_date`.

## Almacenamiento

El framework abstrae el almacenamiento tras la interfaz `StorageAdapter`, con dos implementaciones:

### `CSVStorage`

- Sin dependencias externas; ideal para desarrollo local o volúmenes pequeños.
- Persiste eventos en `data/events.csv` y fingerprints en `data/fingerprints.csv`.
- No soporta promoción de campos ni consultas complejas (filtrado en memoria).

### `SQLStorage`

- Basado en SQLAlchemy sobre PostgreSQL (usa el tipo `JSONB` para el campo `data`).
- Requiere `DATABASE_URL` en el entorno.
- Soporta filtrado por `source`, `type_` y rango de fechas directamente en SQL.
- Soporta **promoción de campos**: cualquier clave del JSONB `data` puede convertirse en columna física indexada (`promote_field`), con backfill por lotes de 100 filas para no bloquear la tabla en datasets grandes.

El tipo de storage se selecciona en `config.yaml` (`storage.type: csv|sql`).

## Notificaciones

Cuando `Orchestrator.update()` detecta eventos nuevos, los pasa a un `PublicationManager`, que reenvía la lista a cada adaptador activo:

- **`TelegramAdapter`**: envía un mensaje formateado en Markdown por evento nuevo a un chat/canal de Telegram.
- **`SMTPAdapter`**: envía un correo por cada evento nuevo, o un único correo resumen si `notifications.smtp.summary: true`.

Ambos adaptadores son independientes entre sí y se pueden activar simultáneamente. Para añadir un canal de notificación propio, basta con implementar `NotificationAdapter` (método `send(events: list[Event])`) y registrarlo en `PublicationManager`.

## API REST

Con la API en marcha (`framework serve-api`), los endpoints disponibles son:

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/events/` | Lista eventos. Filtros opcionales: `source`, `type`, `date_from`, `date_to`. Paginación con `limit` (1-100, por defecto 20) y `offset`. |
| `GET` | `/events/{event_id}` | Devuelve un evento por su id. `404` si no existe. |
| `GET` | `/events/schema/{type_id}` | Devuelve el `json_schema` registrado para un tipo de evento. `404` si el tipo no existe. |

La documentación interactiva (Swagger UI) queda disponible automáticamente en `/docs` gracias a FastAPI.

## Testing

```bash
pytest
```

Con cobertura:

```bash
pytest --cov=framework
```

Los tests cubren modelos, deduplicación, registro de tipos, gestión de fuentes, orquestador, storage CSV, adaptador SMTP y la API.

## Estructura del proyecto

```
events-framework/
├── config.yaml                    # configuración por defecto
├── pyproject.toml                 # dependencias y entrypoint de la CLI
├── framework/
│   ├── api.py                     # API REST (FastAPI)
│   ├── cli.py                     # CLI (Typer): update, list-sources, serve-api, promote-field
│   ├── config.py                  # carga y helpers de config.yaml / .env
│   ├── dedup.py                   # normalización y cálculo de fingerprint
│   ├── models.py                  # modelos Pydantic: Event, EventPayload, EventType
│   ├── orchestrator.py            # ciclo completo: fetch → validar → deduplicar → guardar → notificar
│   ├── registry.py                # persistencia de EventType / json_schema
│   ├── source_manager.py          # descubrimiento y ejecución de fuentes con reintentos
│   ├── publication/
│   │   ├── base.py                # interfaz NotificationAdapter
│   │   ├── manager.py             # PublicationManager (fan-out a adaptadores)
│   │   ├── smtp.py                # adaptador de email
│   │   └── telegram.py            # adaptador de Telegram
│   ├── sources/
│   │   ├── base.py                # interfaz EventSource + decorador @event_source
│   │   ├── csv_source.py          # fuente de ejemplo: lectura de CSV
│   │   └── example_source.py      # fuente de ejemplo: datos embebidos
│   └── storage/
│       ├── base.py                # interfaz StorageAdapter
│       ├── csv_storage.py         # almacenamiento en ficheros CSV
│       └── sql_storage.py         # almacenamiento en PostgreSQL (SQLAlchemy + JSONB)
└── tests/                         # suite de pruebas (pytest)
```
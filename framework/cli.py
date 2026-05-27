import logging
import typer
import uvicorn
from framework.api import app as fastapi_app, setup as api_setup
from typing import Optional
from dotenv import load_dotenv
from framework.config import load_config, get_sources_package, get_storage_config, get_telegram_config
from framework.registry import Registry
from framework.storage.csv_storage import CSVStorage
from framework.storage.sql_storage import SQLStorage
from framework.config import get_database_url
from framework.source_manager import SourceManager
from framework.publication.manager import PublicationManager
from framework.publication.telegram import TelegramAdapter
from framework.orchestrator import Orchestrator

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

app = typer.Typer()


def _build_orchestrator(sources_package: Optional[str] = None) -> Orchestrator:
    config = load_config()
    pkg = sources_package or get_sources_package(config)

    storage_cfg = get_storage_config(config)
    storage_type = storage_cfg.get("type", "csv")

    if storage_type == "sql":
        db_url = get_database_url(config)
        if not db_url:
            typer.echo("ERROR: DATABASE_URL no está definido en el .env")
            raise typer.Exit(1)
        storage = SQLStorage(database_url=db_url)
    else:
        storage = CSVStorage(data_dir=storage_cfg.get("data_dir", "data"))

    storage.init()
    registry = Registry()
    registry.init()
    source_manager = SourceManager(sources_package=pkg or None)
    pub_manager = PublicationManager()
    tg_cfg = get_telegram_config(config)
    if tg_cfg:
        pub_manager.add_adapter(TelegramAdapter(
            token=tg_cfg["token"],
            chat_id=tg_cfg["chat_id"],
        ))
    return Orchestrator(storage, registry, source_manager, pub_manager)


@app.command()
def update(sources_package: Optional[str] = typer.Option(None, help="Paquete Python con las fuentes")):
    """Ejecuta el ciclo completo: fetch, dedup, store, notify."""
    orchestrator = _build_orchestrator(sources_package)
    result = orchestrator.update()
    typer.echo(f"Total: {result['total']} | Guardados: {result['saved']} | Omitidos: {result['skipped']}")


@app.command(name="list-sources")
def list_sources(sources_package: Optional[str] = typer.Option(None, help="Paquete Python con las fuentes")):
    """Lista las fuentes registradas."""
    orchestrator = _build_orchestrator(sources_package)
    sources = orchestrator.list_sources()
    if not sources:
        typer.echo("No se encontraron fuentes registradas")
        return
    for s in sources:
        typer.echo(f"  - {s}")

@app.command(name="serve-api")
def serve_api(
    host: str = typer.Option("0.0.0.0", help="Host donde escucha la API"),
    port: int = typer.Option(8000, help="Puerto donde escucha la API"),
):
    config = load_config()
    storage_cfg = get_storage_config(config)
    storage_type = storage_cfg.get("type", "csv")

    if storage_type == "sql":
        db_url = get_database_url(config)
        if not db_url:
            typer.echo("ERROR: DATABASE_URL no está definido en el .env")
            raise typer.Exit(1)
        storage = SQLStorage(database_url=db_url)
    else:
        storage = CSVStorage(data_dir=storage_cfg.get("data_dir", "data"))

    storage.init()
    registry = Registry()
    registry.init()
    api_setup(storage, registry)
    typer.echo(f"Arrancando API en http://{host}:{port}")
    uvicorn.run(fastapi_app, host=host, port=port)

def main():
    app()
from typing import Optional
import typer
import logging
from framework.registry import Registry
from framework.storage.csv_storage import CSVStorage
from framework.source_manager import SourceManager
from framework.publication.manager import PublicationManager
from framework.orchestrator import Orchestrator

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

app = typer.Typer()


def _build_orchestrator(sources_package: Optional[str] = None) -> Orchestrator:
    storage = CSVStorage()
    storage.init()
    registry = Registry()
    registry.init()
    source_manager = SourceManager(sources_package=sources_package)
    pub_manager = PublicationManager()
    return Orchestrator(storage, registry, source_manager, pub_manager)


@app.command()
def update(sources_package: str = typer.Option(None, help="Paquete Python con las fuentes")):
    """Ejecuta el ciclo completo: fetch, dedup, store, notify."""
    orchestrator = _build_orchestrator(sources_package)
    result = orchestrator.update()
    typer.echo(f"Total: {result['total']} | Guardados: {result['saved']} | Omitidos: {result['skipped']}")


@app.command(name="list-sources")
def list_sources(sources_package: str = typer.Option(None, help="Paquete Python con las fuentes")):
    """Lista las fuentes registradas."""
    orchestrator = _build_orchestrator(sources_package)
    sources = orchestrator.list_sources()
    if not sources:
        typer.echo("No se encontraron fuentes registradas")
        return
    for s in sources:
        typer.echo(f"  - {s}")


def main():
    app()
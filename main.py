#!/usr/bin/env python3
"""
encontreras — CLI para extraer y enriquecer datos de negocios desde Google Maps.

Uso:
    python main.py --query "restaurantes" --location "CDMX"
    python main.py --query "dentistas" --location "Monterrey" --max-results 10 --format json
"""

from __future__ import annotations

import asyncio
from enum import Enum

import typer
from rich.console import Console

from src.core.config import DEFAULT_MAX_RESULTS, DEFAULT_OUTPUT_DIR

app = typer.Typer(
    name="encontreras",
    help="🔍 Extrae negocios de Google Maps, enriquece con datos web/social y exporta a CSV/JSON.",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()


class OutputFormat(str, Enum):
    csv = "csv"
    json = "json"
    both = "both"


@app.command()
def run(
    query: str = typer.Option(
        ...,
        "--query", "-q",
        help="Tipo de negocio a buscar (e.g. 'restaurantes', 'dentistas')",
    ),
    location: str = typer.Option(
        ...,
        "--location", "-l",
        help="Ciudad o zona geográfica (e.g. 'CDMX', 'Monterrey')",
    ),
    max_results: int = typer.Option(
        DEFAULT_MAX_RESULTS,
        "--max-results", "-n",
        help="Número máximo de negocios a extraer",
        min=1,
        max=100,
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.both,
        "--format", "-f",
        help="Formato de exportación: csv, json, o both",
    ),
    output_dir: str = typer.Option(
        DEFAULT_OUTPUT_DIR,
        "--output", "-o",
        help="Directorio de salida para los archivos",
    ),
    headless: bool = typer.Option(
        True,
        "--headless/--no-headless",
        help="Ejecutar el navegador en modo headless (sin ventana)",
    ),
) -> None:
    """
    🔍 Extrae negocios de Google Maps y enriquece con datos web y sociales.
    """
    from src.pipeline import run_pipeline

    try:
        asyncio.run(
            run_pipeline(
                query=query,
                location=location,
                max_results=max_results,
                output_format=output_format.value,
                output_dir=output_dir,
                headless=headless,
            )
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Interrumpido por el usuario.[/yellow]")
        raise typer.Exit(code=1)
    except Exception as exc:
        console.print(f"\n[red]✗ Error: {exc}[/red]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

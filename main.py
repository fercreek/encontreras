#!/usr/bin/env python3
"""
encontreras — CLI para extraer y enriquecer datos de negocios desde Google Maps.

Uso:
    python main.py run --query "restaurantes" --location "CDMX"
    python main.py serve                           # Abre dashboard web
    python main.py serve --port 3000 --output ./mis_datos
"""

from __future__ import annotations

import asyncio
from enum import Enum

import typer
from rich.console import Console
from dotenv import load_dotenv

from src.core.config import DEFAULT_MAX_RESULTS, DEFAULT_OUTPUT_DIR

load_dotenv()

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


@app.command()
def serve(
    output_dir: str = typer.Option(
        DEFAULT_OUTPUT_DIR,
        "--output", "-o",
        help="Directorio con los archivos de base de datos o resultados",
    ),
    port: int = typer.Option(
        8888,
        "--port", "-p",
        help="Puerto del servidor web",
    ),
    reload: bool = typer.Option(
        False,
        "--reload", "-r",
        help="Habilitar reinicio automático al guardar cambios en el código",
    ),
) -> None:
    """
    🖥  Abre el dashboard web para visualizar los resultados extraídos.
    """
    if reload:
        import hupper
        # Inicia el supervisor de hupper, usando el entry point principal
        # para que Typer vuelva a leer los argumentos de sys.argv
        reloader = hupper.start_reloader('main.app_entry')
        
    from web.server import start_server
    start_server(output_dir=output_dir, port=port)


@app.command()
def synthesize(
    db_path: str = typer.Option(
        "./output/encontreras.db",
        "--db",
        help="Ruta a la base de datos SQLite",
    ),
    min_score: int = typer.Option(
        3,
        "--min-score", "-s",
        help="Puntaje mínimo para analizar",
    ),
    limit: int = typer.Option(
        10,
        "--limit", "-n",
        help="Límite máximo de registros a analizar a la vez",
    ),
) -> None:
    """
    🧠 Ejecuta la IA (Gemini) sobre los prospectos calificados (Score >= 3)
    para generar 'Why they matter', 'Context' e 'Icebreaker'.
    """
    from src.core.ai_synthesis import synthesize_business
    from src.core.models import Business
    import sqlite3
    import os

    if not os.getenv("GEMINI_API_KEY"):
        console.print("[red]❌ GEMINI_API_KEY no encontrada en .env[/red]")
        raise typer.Exit(1)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('''
            SELECT * FROM businesses 
            WHERE score >= ? 
              AND context IS NULL
            LIMIT ?
        ''', (min_score, limit))
        rows = c.fetchall()
        
        if not rows:
            console.print("[green]✔ No hay prospectos pendientes por analizar con ese criterio.[/green]")
            return
            
        console.print(f"[blue]Analizando {len(rows)} prospectos con IA...[/blue]")
        
        updates = 0
        for row in rows:
            biz_dict = dict(row)
            
            if biz_dict.get("emails"):
                biz_dict["emails"] = biz_dict["emails"].split(",")
            else:
                biz_dict["emails"] = []
                
            if biz_dict.get("site_issues"):
                biz_dict["site_issues"] = biz_dict["site_issues"].split(",")
            else:
                biz_dict["site_issues"] = []
                
            biz_id = biz_dict.pop('id')
            biz_dict.pop('inserted_at', None)
            biz_dict.pop('updated_at', None)
                
            b = Business(**biz_dict)
            console.print(f"Analizando: [cyan]{b.name}[/cyan]...")
            
            result = synthesize_business(b)
            if result:
                context = result.get('context')
                why = result.get('why_they_matter')
                ice = result.get('icebreaker')
                
                c.execute('''
                    UPDATE businesses 
                    SET context = ?, why_they_matter = ?, icebreaker = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (context, why, ice, biz_id))
                conn.commit()
                updates += 1
                console.print(f"  [green]✔ Guardado.[/green]")
            else:
                console.print(f"  [red]✗ Falló el análisis.[/red]")
                
        conn.close()
        console.print(f"\n[bold green]Sintetizados {updates}/{len(rows)} prospectos exitosamente.[/bold green]")
    except Exception as exc:
        console.print(f"\n[red]✗ Error en síntesis: {exc}[/red]")
        raise typer.Exit(code=1)


@app.command(name="notion-sync")
def notion_sync_cmd(
    db_path: str = typer.Option(
        "./output/encontreras.db",
        "--db",
        help="Ruta a la base de datos SQLite",
    ),
    limit: int = typer.Option(
        10,
        "--limit", "-n",
        help="Límite máximo de prospectos a sincronizar por lote",
    ),
) -> None:
    """
    📤 Sincroniza los prospectos calificados y analizados con IA hacia tu base de datos de Notion.
    """
    from src.core.notion_sync import sync_leads_to_notion
    try:
        sync_leads_to_notion(db_path=db_path, limit=limit)
    except Exception as exc:
        console.print(f"\n[red]✗ Error en sincronización: {exc}[/red]")
        raise typer.Exit(code=1)


def app_entry():
    """Entry point for hupper reloader."""
    app()


if __name__ == "__main__":
    app_entry()

"""
Pipeline — orchestrates the full scrape → enrich → resolve → export flow.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright
from rich.console import Console
from rich.table import Table

from src.core.entity_resolution import resolve_entities
from src.core.exporter import to_csv, to_json
from src.core.lead_scorer import calculate_lead_score
from src.core.models import Business
from src.extractors.google_maps import GoogleMapsExtractor
from src.extractors.social import SocialEnricher
from src.extractors.website import WebsiteEnricher

console = Console()


async def run_pipeline(
    query: str,
    location: str,
    max_results: int = 20,
    output_format: str = "both",
    output_dir: str = "./output",
    headless: bool = True,
) -> None:
    """
    Full pipeline:
      1. Extract businesses from Google Maps
      2. Enrich with website data (emails, social links)
      3. Enrich with social media data (follower counts)
      4. Apply entity resolution
      5. Export results
    """
    console.rule("[bold cyan]encontreras[/bold cyan]  ·  Fase 1")
    console.print()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        context = await browser.new_context(
            locale="es-MX",
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        )

        page = await context.new_page()

        # ── Step 1: Google Maps extraction ────────────────────────────────
        console.rule("[bold]Paso 1 · Extracción de Google Maps[/bold]")
        maps_extractor = GoogleMapsExtractor(page)
        businesses = await maps_extractor.extract(query, location, max_results)

        if not businesses:
            console.print("[red]✗ No se encontraron negocios. Abortando.[/red]")
            await browser.close()
            return

        console.print(f"\n[green]✔ {len(businesses)} negocios extraídos de Google Maps[/green]\n")

        # ── Step 2: Website enrichment ────────────────────────────────────
        console.rule("[bold]Paso 2 · Enriquecimiento Web[/bold]")
        enrichment_page = await context.new_page()
        web_enricher = WebsiteEnricher(enrichment_page)

        enriched_count = 0
        for i, biz in enumerate(businesses, 1):
            if biz.website:
                console.print(f"  [{i}/{len(businesses)}] Enriqueciendo {biz.domain}…")
                await web_enricher.enrich(biz)
                enriched_count += 1

        console.print(f"\n[green]✔ {enriched_count} sitios web analizados[/green]\n")

        # ── Step 3: Social enrichment ─────────────────────────────────────
        console.rule("[bold]Paso 3 · Enriquecimiento Social[/bold]")
        social_enricher = SocialEnricher(enrichment_page)

        social_count = 0
        for i, biz in enumerate(businesses, 1):
            has_social = biz.instagram or biz.tiktok or biz.facebook
            if has_social:
                console.print(f"  [{i}/{len(businesses)}] Extrayendo seguidores de {biz.name}…")
                await social_enricher.enrich(biz)
                social_count += 1

        console.print(f"\n[green]✔ {social_count} perfiles sociales analizados[/green]\n")

        await enrichment_page.close()
        await browser.close()

    # ── Step 3.5: Lead Scoring ──────────────────────────────────────────
    console.rule("[bold]Paso 3.5 · Lead Scoring[/bold]")
    for biz in businesses:
        score, label = calculate_lead_score(biz.to_dict(), query)
        biz.score = score
        biz.quality_label = label

    score_dist = {}
    for biz in businesses:
        score_dist[biz.quality_label] = score_dist.get(biz.quality_label, 0) + 1
    dist_str = "  ".join(f"{label}: {count}" for label, count in sorted(score_dist.items()))
    console.print(f"[green]✔ Distribución de calidad → {dist_str}[/green]\n")

    # ── Step 4: Entity Resolution ─────────────────────────────────────────
    console.rule("[bold]Paso 4 · Entity Resolution[/bold]")
    df = resolve_entities(businesses)
    console.print(
        f"[green]✔ {len(businesses)} registros → {len(df)} entidades únicas[/green]\n"
    )

    # ── Step 5: Export ────────────────────────────────────────────────────
    console.rule("[bold]Paso 5 · Exportación[/bold]")
    
    from src.core.database import save_to_db
    db_path = str(Path(output_dir) / "encontreras.db")
    save_to_db(df, db_path)
    console.print(f"[green]✔ Base de datos actualizada (SQLite Upsert → {db_path})[/green]")

    if output_format in ("csv", "both"):
        to_csv(df, output_dir)
    if output_format in ("json", "both"):
        to_json(df, output_dir)

    # ── Summary table ────────────────────────────────────────────────────
    console.print()
    console.rule("[bold cyan]Resumen[/bold cyan]")
    _print_summary(df)


def _print_summary(df) -> None:
    """Print a concise summary table of results."""
    # Score → color mapping
    score_styles = {5: "bold green", 4: "green", 3: "yellow", 2: "dim", 1: "dim red", 0: "red"}

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column("Nombre", min_width=20)
    table.add_column("Teléfono", min_width=14)
    table.add_column("Web", min_width=15)
    table.add_column("Emails", min_width=15)
    table.add_column("Redes", min_width=10)
    table.add_column("Score", justify="center", width=7)
    table.add_column("Calidad", min_width=12)

    for idx, row in df.iterrows():
        socials: list[str] = []
        if row.get("instagram"):
            socials.append("IG")
        if row.get("tiktok"):
            socials.append("TK")
        if row.get("facebook"):
            socials.append("FB")

        score = row.get("score")
        score_str = str(int(score)) if score is not None else "—"
        style = score_styles.get(int(score), "dim") if score is not None else "dim"

        table.add_row(
            str(idx + 1),
            str(row.get("name", "—"))[:30],
            str(row.get("phone", "—") or "—"),
            str(row.get("domain", "—") or "—")[:20],
            str(row.get("emails", "—") or "—")[:25],
            ", ".join(socials) or "—",
            f"[{style}]{score_str}[/{style}]",
            str(row.get("quality_label", "—") or "—"),
        )

    console.print(table)
    console.print()

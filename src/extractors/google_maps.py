"""
Google Maps extractor — uses Playwright to scrape business listings.
"""

from __future__ import annotations

import asyncio
import re
from urllib.parse import quote_plus

from playwright.async_api import Page, TimeoutError as PwTimeout
from rich.console import Console

from src.core.config import (
    ELEMENT_TIMEOUT,
    MAPS_SEARCH_URL,
    MAPS_SELECTORS,
    NAVIGATION_TIMEOUT,
    PAGE_TIMEOUT,
    SCROLL_PAUSE,
)
from src.core.models import Business

console = Console()


class GoogleMapsExtractor:
    """Scrape business listings from Google Maps search results."""

    def __init__(self, page: Page) -> None:
        self.page = page

    async def extract(
        self,
        query: str,
        location: str,
        max_results: int = 20,
    ) -> list[Business]:
        """
        Search Google Maps for `query` in `location` and return a list of
        Business objects with basic info (name, phone, website, address, etc.).
        """
        search_term = f"{query} en {location}"
        url = MAPS_SEARCH_URL.format(query=quote_plus(search_term))

        console.print(f"[cyan]🔍 Buscando:[/cyan] {search_term}")
        await self.page.goto(url, timeout=PAGE_TIMEOUT, wait_until="domcontentloaded")

        # Wait for the results feed to render
        try:
            await self.page.wait_for_selector(
                MAPS_SELECTORS["results_container"],
                timeout=NAVIGATION_TIMEOUT,
            )
        except PwTimeout:
            console.print("[yellow]⚠ No se encontró feed de resultados. Verifica la búsqueda.[/yellow]")
            return []

        # ── Scroll to load more results ──────────────────────────────────
        feed = await self.page.query_selector(MAPS_SELECTORS["results_container"])
        if not feed:
            return []

        links_seen: set[str] = set()
        scroll_attempts = 0
        max_scroll_attempts = max_results * 2  # generous upper bound

        while len(links_seen) < max_results and scroll_attempts < max_scroll_attempts:
            # Collect current visible place links
            link_els = await self.page.query_selector_all(
                MAPS_SELECTORS["result_link"]
            )
            for el in link_els:
                href = await el.get_attribute("href")
                if href:
                    links_seen.add(href)

            if len(links_seen) >= max_results:
                break

            # Scroll the feed container
            await feed.evaluate("el => el.scrollTop = el.scrollHeight")
            await self.page.wait_for_timeout(SCROLL_PAUSE)
            scroll_attempts += 1

            # Check for end-of-list marker
            end_marker = await self.page.query_selector(
                "p.fontBodyMedium span:has-text('end of list'), "
                "p.fontBodyMedium span:has-text('final de la lista'), "
                "span.HlvSq"
            )
            if end_marker:
                console.print("[dim]Reached end of results list.[/dim]")
                break

        console.print(f"[cyan]📋 {len(links_seen)} resultados encontrados, extrayendo hasta {max_results}…[/cyan]")

        # ── Visit each place and extract data ────────────────────────────
        businesses: list[Business] = []
        for idx, href in enumerate(list(links_seen)[:max_results], 1):
            try:
                biz = await self._extract_place(href, idx, max_results)
                if biz:
                    businesses.append(biz)
            except Exception as exc:
                console.print(f"[yellow]⚠ Error en resultado {idx}: {exc}[/yellow]")

        return businesses

    async def _extract_place(self, href: str, idx: int, total: int) -> Business | None:
        """Navigate to a place page and extract structured data."""
        await self.page.goto(href, timeout=PAGE_TIMEOUT, wait_until="domcontentloaded")

        # Wait for the place name to appear
        try:
            await self.page.wait_for_selector(
                MAPS_SELECTORS["place_name"],
                timeout=ELEMENT_TIMEOUT,
            )
        except PwTimeout:
            return None

        name = await self._text(MAPS_SELECTORS["place_name"])
        if not name:
            return None

        phone = await self._text(MAPS_SELECTORS["place_phone"])
        website = await self._attr(MAPS_SELECTORS["place_website"], "href")
        address = await self._text(MAPS_SELECTORS["place_address"])
        rating_text = await self._text(MAPS_SELECTORS["place_rating"])
        reviews_text = await self._text(MAPS_SELECTORS["place_reviews"])

        rating = self._parse_float(rating_text)
        reviews_count = self._parse_int(reviews_text)

        biz = Business(
            name=name,
            phone=phone,
            website=website,
            address=address,
            rating=rating,
            reviews_count=reviews_count,
        )

        status = "✔" if biz.website else "–"
        console.print(
            f"  [{idx}/{total}] {status} [bold]{name}[/bold]"
            f"  📞 {phone or '—'}  🌐 {biz.domain or '—'}"
        )

        return biz

    # ── DOM helpers ───────────────────────────────────────────────────────

    async def _text(self, selector: str) -> str | None:
        """Get text content of the first matching element."""
        try:
            el = await self.page.wait_for_selector(selector, timeout=3_000)
            if el:
                return (await el.text_content() or "").strip() or None
        except (PwTimeout, Exception):
            pass
        return None

    async def _attr(self, selector: str, attribute: str) -> str | None:
        """Get an attribute from the first matching element."""
        try:
            el = await self.page.wait_for_selector(selector, timeout=3_000)
            if el:
                return await el.get_attribute(attribute)
        except (PwTimeout, Exception):
            pass
        return None

    # ── Parsing helpers ──────────────────────────────────────────────────

    @staticmethod
    def _parse_float(text: str | None) -> float | None:
        if not text:
            return None
        try:
            return float(text.replace(",", "."))
        except ValueError:
            return None

    @staticmethod
    def _parse_int(text: str | None) -> int | None:
        if not text:
            return None
        digits = re.sub(r"[^\d]", "", text)
        return int(digits) if digits else None

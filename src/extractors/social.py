"""
Social media enricher — visit social profiles and extract follower counts.
"""

from __future__ import annotations

import re

from playwright.async_api import Page, TimeoutError as PwTimeout
from rich.console import Console

from src.core.config import NAVIGATION_TIMEOUT
from src.core.models import Business

console = Console()


class SocialEnricher:
    """Visit Instagram / TikTok / Facebook profiles to extract follower counts."""

    def __init__(self, page: Page) -> None:
        self.page = page

    async def enrich(self, business: Business) -> Business:
        """
        Best-effort extraction of follower counts from each social profile.
        Falls back to None silently on any failure.
        """
        if business.instagram and not business.ig_followers:
            business.ig_followers = await self._get_instagram_followers(
                business.instagram
            )

        if business.tiktok and not business.tiktok_followers:
            business.tiktok_followers = await self._get_tiktok_followers(
                business.tiktok
            )

        if business.facebook and not business.fb_followers:
            business.fb_followers = await self._get_facebook_followers(
                business.facebook
            )

        parts: list[str] = []
        if business.ig_followers:
            parts.append(f"IG:{business.ig_followers}")
        if business.tiktok_followers:
            parts.append(f"TK:{business.tiktok_followers}")
        if business.fb_followers:
            parts.append(f"FB:{business.fb_followers}")

        if parts:
            console.print(f"    📊 {business.name} → {', '.join(parts)}")

        return business

    # ── Instagram ────────────────────────────────────────────────────────

    async def _get_instagram_followers(self, url: str) -> str | None:
        """Extract follower count from Instagram profile page."""
        try:
            await self.page.goto(url, timeout=NAVIGATION_TIMEOUT, wait_until="domcontentloaded")
            await self.page.wait_for_timeout(2_000)

            # Method 1: meta tag content, e.g. "123K Followers"
            meta = await self.page.query_selector('meta[property="og:description"]')
            if meta:
                content = await meta.get_attribute("content")
                if content:
                    follower_match = re.search(
                        r"([\d,.]+[KkMm]?)\s*Followers", content, re.IGNORECASE
                    )
                    if follower_match:
                        return follower_match.group(1)

            # Method 2: look in page title
            title = await self.page.title()
            if title:
                match = re.search(
                    r"([\d,.]+[KkMm]?)\s*Followers", title, re.IGNORECASE
                )
                if match:
                    return match.group(1)

            # Method 3: span or link text that contains "followers"
            html = await self.page.content()
            match = re.search(
                r'"edge_followed_by":\{"count":(\d+)\}', html
            )
            if match:
                return self._format_count(int(match.group(1)))

        except (PwTimeout, Exception):
            pass
        return None

    # ── TikTok ───────────────────────────────────────────────────────────

    async def _get_tiktok_followers(self, url: str) -> str | None:
        """Extract follower count from TikTok profile page."""
        try:
            await self.page.goto(url, timeout=NAVIGATION_TIMEOUT, wait_until="domcontentloaded")
            await self.page.wait_for_timeout(3_000)

            # Method 1: data attribute
            follower_el = await self.page.query_selector(
                '[data-e2e="followers-count"]'
            )
            if follower_el:
                text = await follower_el.text_content()
                if text:
                    return text.strip()

            # Method 2: meta description
            meta = await self.page.query_selector('meta[name="description"]')
            if meta:
                content = await meta.get_attribute("content")
                if content:
                    match = re.search(
                        r"([\d,.]+[KkMm]?)\s*Followers", content, re.IGNORECASE
                    )
                    if match:
                        return match.group(1)

            # Method 3: strong element with follower count
            strong_elements = await self.page.query_selector_all("strong[title]")
            for el in strong_elements:
                title = await el.get_attribute("title")
                text = await el.text_content()
                if title and text:
                    return text.strip()

        except (PwTimeout, Exception):
            pass
        return None

    # ── Facebook ─────────────────────────────────────────────────────────

    async def _get_facebook_followers(self, url: str) -> str | None:
        """Extract follower/like count from Facebook page."""
        try:
            await self.page.goto(url, timeout=NAVIGATION_TIMEOUT, wait_until="domcontentloaded")
            await self.page.wait_for_timeout(3_000)

            html = await self.page.content()

            # Look for common patterns in FB page HTML
            patterns = [
                r"([\d,.\s]+)\s*(?:followers|seguidores)",
                r"([\d,.\s]+)\s*(?:people\s+like|personas.*les\s+gusta)",
                r"([\d,.\s]+)\s*(?:likes|Me gusta)",
            ]
            for pat in patterns:
                match = re.search(pat, html, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

        except (PwTimeout, Exception):
            pass
        return None

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _format_count(n: int) -> str:
        """Format a number into a human-readable short form."""
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.1f}K"
        return str(n)

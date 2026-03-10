"""
Website enricher — crawl a business website to extract emails and social links.
"""

from __future__ import annotations

from playwright.async_api import Page, TimeoutError as PwTimeout
from rich.console import Console

from src.core.config import (
    EMAIL_BLACKLIST_DOMAINS,
    EMAIL_PATTERN,
    NAVIGATION_TIMEOUT,
    SOCIAL_BLACKLIST_HANDLES,
    SOCIAL_PATTERNS,
)
from src.core.models import Business

console = Console()


class WebsiteEnricher:
    """Visit a business website and extract emails + social media links."""

    def __init__(self, page: Page) -> None:
        self.page = page

    async def enrich(self, business: Business) -> Business:
        """
        Navigate to the business website and scrape:
        - Email addresses (from visible text + mailto: links)
        - Instagram, TikTok, Facebook profile URLs
        """
        if not business.website:
            return business

        try:
            response = await self.page.goto(
                business.website,
                timeout=NAVIGATION_TIMEOUT,
                wait_until="domcontentloaded",
            )
            # Give JS a moment to render
            await self.page.wait_for_timeout(2_000)
            
            if response:
                if response.status >= 400:
                    business.site_status = f"ERROR_{response.status}"
                    business.site_issues.append(f"HTTP {response.status}")
                else:
                    business.site_status = "OK"
            else:
                business.site_status = "UNKNOWN"
                
        except (PwTimeout, Exception) as exc:
            console.print(f"  [yellow]⚠ No se pudo cargar {business.domain}: {exc}[/yellow]")
            business.site_status = "DOWN"
            business.site_issues.append("Timeout o error de conexión")
            return business

        # ── Evaluate Website Health ───────────────────────────────────────
        if business.site_status == "OK":
            try:
                issues = await self.page.evaluate('''() => {
                    const issues = [];
                    if (!document.querySelector("meta[name='viewport'][content*='width=device-width']")) {
                        issues.push("Sin optimización móvil (viewport)");
                    }
                    if (!document.querySelector("h1")) {
                        issues.push("Falta etiqueta H1 principal");
                    }
                    if (!document.title || document.title.length < 5) {
                        issues.push("Título corto o ausente");
                    }
                    return issues;
                }''')
                if issues:
                    business.site_issues.extend(issues)
            except Exception:
                pass

        try:
            html = await self.page.content()
        except Exception:
            return business

        # ── Extract emails ────────────────────────────────────────────────
        emails = self._extract_emails(html)
        if emails:
            business.emails = list(set(business.emails + emails))

        # ── Extract social links ──────────────────────────────────────────
        socials = self._extract_socials(html)
        if socials.get("instagram") and not business.instagram:
            business.instagram = socials["instagram"]
        if socials.get("tiktok") and not business.tiktok:
            business.tiktok = socials["tiktok"]
        if socials.get("facebook") and not business.facebook:
            business.facebook = socials["facebook"]

        # Also scan for social links in <a> hrefs explicitly
        await self._extract_socials_from_links(business)

        found_parts: list[str] = []
        if business.emails:
            found_parts.append(f"📧{len(business.emails)}")
        if business.instagram:
            found_parts.append("IG")
        if business.tiktok:
            found_parts.append("TK")
        if business.facebook:
            found_parts.append("FB")

        if found_parts:
            console.print(f"    🌐 {business.domain} → {', '.join(found_parts)}")

        return business

    # ── Email extraction ─────────────────────────────────────────────────

    @staticmethod
    def _extract_emails(html: str) -> list[str]:
        """Find valid email addresses in the page HTML."""
        raw_matches = EMAIL_PATTERN.findall(html)
        clean: list[str] = []
        for email in raw_matches:
            email = email.lower().strip()
            domain = email.split("@")[1] if "@" in email else ""
            if domain in EMAIL_BLACKLIST_DOMAINS:
                continue
            # Skip likely file extensions mistaken as emails
            if domain.endswith((".png", ".jpg", ".gif", ".svg", ".webp")):
                continue
            clean.append(email)
        return list(set(clean))

    # ── Social extraction ────────────────────────────────────────────────

    @staticmethod
    def _extract_socials(html: str) -> dict[str, str | None]:
        """Extract social profile URLs from page HTML via regex."""
        result: dict[str, str | None] = {
            "instagram": None,
            "tiktok": None,
            "facebook": None,
        }
        for platform, pattern in SOCIAL_PATTERNS.items():
            match = pattern.search(html)
            if match:
                handle = match.group(1).lower().strip("/")
                if handle not in SOCIAL_BLACKLIST_HANDLES:
                    result[platform] = match.group(0).split("?")[0].rstrip("/")
        return result

    async def _extract_socials_from_links(self, business: Business) -> None:
        """Scan <a> hrefs explicitly for social links not caught by regex."""
        try:
            links = await self.page.query_selector_all("a[href]")
            for link in links:
                href = await link.get_attribute("href")
                if not href:
                    continue
                href = href.lower()

                if "instagram.com/" in href and not business.instagram:
                    match = SOCIAL_PATTERNS["instagram"].search(href)
                    if match and match.group(1) not in SOCIAL_BLACKLIST_HANDLES:
                        business.instagram = href.split("?")[0].rstrip("/")

                elif "tiktok.com/@" in href and not business.tiktok:
                    match = SOCIAL_PATTERNS["tiktok"].search(href)
                    if match and match.group(1) not in SOCIAL_BLACKLIST_HANDLES:
                        business.tiktok = href.split("?")[0].rstrip("/")

                elif "facebook.com/" in href and not business.facebook:
                    match = SOCIAL_PATTERNS["facebook"].search(href)
                    if match and match.group(1) not in SOCIAL_BLACKLIST_HANDLES:
                        business.facebook = href.split("?")[0].rstrip("/")
        except Exception:
            pass

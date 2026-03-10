"""
Data models for the encontreras pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass
class Business:
    """Represents a single business entity across all data sources."""

    # ── Google Maps fields ────────────────────────────────────────────────
    name: str
    phone: str | None = None
    website: str | None = None
    address: str | None = None
    rating: float | None = None
    reviews_count: int | None = None

    # ── Derived ───────────────────────────────────────────────────────────
    domain: str | None = None

    # ── Enrichment: website crawling ──────────────────────────────────────
    emails: list[str] = field(default_factory=list)
    instagram: str | None = None
    tiktok: str | None = None
    facebook: str | None = None

    # ── Lead scoring ──────────────────────────────────────────────────────────
    score: int = -1               # 0–5; -1 means not yet scored
    quality_label: str = "—"     # Excelente / Bueno / Rescatado / Débil / Spam\Vacío

    # ── Enrichment: social media ──────────────────────────────────────────
    ig_followers: str | None = None
    tiktok_followers: str | None = None
    fb_followers: str | None = None

    def __post_init__(self) -> None:
        """Derive domain from website URL if not explicitly provided."""
        if self.website and not self.domain:
            try:
                parsed = urlparse(self.website)
                host = parsed.netloc or parsed.path
                self.domain = (
                    host.lower()
                    .removeprefix("www.")
                    .removeprefix("m.")
                    .strip("/")
                )
            except Exception:
                self.domain = None

        # Normalize phone to digits-only for matching
        if self.phone:
            self.phone = self._normalize_phone(self.phone)

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Keep only digits. Strips leading '+' so +52... == 52... for matching."""
        return "".join(c for c in phone if c.isdigit())

    def to_dict(self) -> dict:
        """Serialize to a flat dictionary suitable for DataFrame conversion."""
        return {
            "name": self.name,
            "phone": self.phone,
            "website": self.website,
            "domain": self.domain,
            "address": self.address,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "emails": ", ".join(self.emails) if self.emails else None,
            "instagram": self.instagram,
            "tiktok": self.tiktok,
            "facebook": self.facebook,
            "ig_followers": self.ig_followers,
            "tiktok_followers": self.tiktok_followers,
            "fb_followers": self.fb_followers,
            "score": self.score if self.score >= 0 else None,
            "quality_label": self.quality_label,
        }

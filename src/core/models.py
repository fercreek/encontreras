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
    category: str | None = None
    hours: str | None = None
    description: str | None = None
    price_level: str | None = None
    maps_url: str | None = None
    plus_code: str | None = None

    # ── Derived ───────────────────────────────────────────────────────────
    domain: str | None = None

    # ── Enrichment: website crawling ──────────────────────────────────────
    emails: list[str] = field(default_factory=list)
    instagram: str | None = None
    tiktok: str | None = None
    facebook: str | None = None
    site_status: str | None = None       # e.g., "OK", "DOWN", "ERROR"
    site_issues: list[str] = field(default_factory=list) # e.g., ["Missing H1", "No mobile viewport"]

    # ── Lead scoring ──────────────────────────────────────────────────────────
    score: int = -1               # 0–5; -1 means not yet scored
    quality_label: str = "—"     # Excelente / Bueno / Rescatado / Débil / Spam\Vacío

    # ── Enrichment: social media ──────────────────────────────────────────
    ig_followers: str | None = None
    tiktok_followers: int | None = None
    
    # LLM Synthesis
    context: str | None = None
    why_they_matter: str | None = None
    icebreaker: str | None = None
    
    # Integration
    notion_url: str | None = None
    fb_followers: str | None = None

    # ── Phase 2: Semantic Filtering ───────────────────────────────────────
    bio_text: str | None = None
    recent_posts: list[str] = field(default_factory=list)
    is_target_niche: bool | None = None
    inferred_niche: str | None = None
    match_type: str | None = None
    semantic_confidence: int | None = None
    filter_reasoning: str | None = None

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
            "category": self.category,
            "hours": self.hours,
            "description": self.description,
            "price_level": self.price_level,
            "maps_url": self.maps_url,
            "plus_code": self.plus_code,
            "emails": ", ".join(self.emails) if self.emails else None,
            "instagram": self.instagram,
            "tiktok": self.tiktok,
            "facebook": self.facebook,
            "site_status": self.site_status,
            "site_issues": ", ".join(self.site_issues) if self.site_issues else None,
            "ig_followers": self.ig_followers,
            "tiktok_followers": self.tiktok_followers,
            "context": self.context,
            "why_they_matter": self.why_they_matter,
            "icebreaker": self.icebreaker,
            "notion_url": self.notion_url,
            "fb_followers": self.fb_followers,
            "score": self.score if self.score >= 0 else None,
            "quality_label": self.quality_label,
        }

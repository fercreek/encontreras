"""
Lead Scorer — heuristic-based quality scoring for extracted leads.

Scoring scale (0–5):
  5  ─ Name OR bio explicitly matches the query terms
  4  ─ Website/description references the query clearly
  3  ─ Bio is generic/empty but contains SERVICE target keywords (rescued)
  2  ─ Some weak signal (has socials or email, partial keyword match)
  1  ─ Very little usable data, no keyword match
  0  ─ Looks like a personal profile, spam, or completely empty
"""

from __future__ import annotations

import re

# ─── Generic service-business keywords ────────────────────────────────────────
# These signal that a local business sells a service/class even if the bio
# doesn't mention the specific niche (e.g. dancing, fitness, language school).
TARGET_KEYWORDS: list[str] = [
    # Enrollment / schedule
    "clases", "clase", "inscripciones", "inscripción", "inscribete",
    "horarios", "horario", "agenda", "agendar", "reservar", "reserva",
    # Payment / commercial
    "mensualidad", "colegiatura", "pago", "precio", "tarifa", "costo",
    "paquete", "plan", "promoción", "oferta", "descuento",
    # Students / members
    "alumnos", "alumno", "estudiantes", "miembros", "socios",
    # Service delivery
    "entrenamiento", "taller", "curso", "programa", "sesión",
    "servicio", "asesoría", "consulta", "turno", "cita",
    # Contact cues
    "informes", "contáctanos", "llámanos", "whatsapp", "dm", "mensaje",
]

# Spam / personal-profile signals (score penalty)
SPAM_SIGNALS: list[str] = [
    "personal", "privado", "perfil personal", "cuenta personal",
    "follow back", "followback", "dm for promo", "link in bio",
]


def _normalize(text: str) -> str:
    """Lowercase, remove accents for fuzzy matching."""
    text = text.lower()
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ü": "u", "ñ": "n",
    }
    for accented, plain in replacements.items():
        text = text.replace(accented, plain)
    return text


def _contains_any(text: str, keywords: list[str]) -> list[str]:
    """Return which keywords are found in text (normalized)."""
    normed = _normalize(text)
    return [kw for kw in keywords if _normalize(kw) in normed]


def _query_terms(query: str) -> list[str]:
    """Split the user query into individual search terms (min 3 chars)."""
    return [t.strip() for t in re.split(r"[\s,/]+", query) if len(t.strip()) >= 3]


def calculate_lead_score(lead_data: dict, query: str) -> tuple[int, str]:
    """
    Score a lead dict on a 0–5 scale using heuristics only.

    Args:
        lead_data: The business dict (fields from Business.to_dict()).
        query:     The original CLI --query string (e.g. "academia de baile").

    Returns:
        (score: int, quality_label: str)
        quality_label ∈ {"Excelente", "Bueno", "Rescatado", "Débil", "Spam/Vacío"}
    """
    # ── Gather text corpus ─────────────────────────────────────────────────
    text_parts: list[str] = [
        lead_data.get("name") or "",
        lead_data.get("address") or "",
        lead_data.get("description") or "",    # Maps description (future field)
        lead_data.get("ig_bio") or "",          # IG bio (future field)
        lead_data.get("emails") or "",
        lead_data.get("domain") or "",
    ]
    full_text = " ".join(text_parts)

    name_text = lead_data.get("name") or ""

    query_terms = _query_terms(query)

    # ── Spam check ────────────────────────────────────────────────────────
    spam_hits = _contains_any(full_text, SPAM_SIGNALS)
    has_any_data = any([
        lead_data.get("phone"),
        lead_data.get("website"),
        lead_data.get("emails"),
        lead_data.get("instagram"),
        lead_data.get("tiktok"),
        lead_data.get("facebook"),
    ])
    if not has_any_data and not lead_data.get("name"):
        return 0, "Spam/Vacío"

    # ── Score 5: name explicitly matches query ────────────────────────────
    name_hits = _contains_any(name_text, query_terms)
    if name_hits:
        return 5, "Excelente"

    # ── Score 4: website/domain or description matches query ─────────────
    corpus_hits = _contains_any(full_text, query_terms)
    if corpus_hits and (lead_data.get("website") or lead_data.get("emails")):
        return 4, "Bueno"
    if corpus_hits:
        return 3, "Rescatado"

    # ── Score 3: generic service keywords found (rescued lead) ────────────
    service_hits = _contains_any(full_text, TARGET_KEYWORDS)
    if service_hits and has_any_data:
        return 3, "Rescatado"

    # ── Score 2: has some digital presence but no keyword match ──────────
    digital_signals = sum([
        bool(lead_data.get("website")),
        bool(lead_data.get("emails")),
        bool(lead_data.get("instagram")),
        bool(lead_data.get("tiktok")),
        bool(lead_data.get("facebook")),
    ])
    if digital_signals >= 2:
        return 2, "Débil"

    # ── Score 1: has a name and phone but nothing else ────────────────────
    if spam_hits:
        return 0, "Spam/Vacío"
    if lead_data.get("phone") or digital_signals == 1:
        return 1, "Débil"

    return 0, "Spam/Vacío"

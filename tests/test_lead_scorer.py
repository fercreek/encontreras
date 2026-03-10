"""
Unit tests for src/core/lead_scorer.py

Tests cover the full scoring rubric:
  - Score 5: name matches query terms
  - Score 4: website/description matches query + has web or email
  - Score 3: query matched without strong digital presence OR service keywords found
  - Score 2: multiple digital signals but no keyword match
  - Score 1: minimal data (phone or 1 signal only)
  - Score 0: empty / spam signals
"""

import pytest
from src.core.lead_scorer import calculate_lead_score


# ── Helpers ───────────────────────────────────────────────────────────────────

def lead(
    name="Negocio",
    phone=None,
    website=None,
    domain=None,
    address=None,
    emails=None,
    instagram=None,
    tiktok=None,
    facebook=None,
    ig_followers=None,
    tiktok_followers=None,
    fb_followers=None,
    score=None,
    quality_label=None,
    description=None,
    ig_bio=None,
) -> dict:
    """Build a minimal lead dict for testing."""
    return {
        "name": name,
        "phone": phone,
        "website": website,
        "domain": domain,
        "address": address,
        "emails": emails,
        "instagram": instagram,
        "tiktok": tiktok,
        "facebook": facebook,
        "ig_followers": ig_followers,
        "tiktok_followers": tiktok_followers,
        "fb_followers": fb_followers,
        "score": score,
        "quality_label": quality_label,
        "description": description,
        "ig_bio": ig_bio,
    }


# ── Score 5: name explicitly matches query ─────────────────────────────────

class TestScore5:
    def test_name_contains_query_term(self):
        data = lead(name="Academia de Baile Monterrey", phone="5551234567")
        score, label = calculate_lead_score(data, "academia de baile")
        assert score == 5
        assert label == "Excelente"

    def test_name_partial_match(self):
        data = lead(name="Studio Baile GDL")
        score, label = calculate_lead_score(data, "baile")
        assert score == 5

    def test_case_insensitive(self):
        data = lead(name="DENTISTA PÉREZ")
        score, label = calculate_lead_score(data, "dentista")
        assert score == 5

    def test_accented_query_matches_unaccented_name(self):
        """'académia' in query should match 'academia' in name."""
        data = lead(name="Academia de Yoga")
        score, label = calculate_lead_score(data, "académia")
        assert score == 5


# ── Score 4 / 3: query in corpus, not in name ──────────────────────────────

class TestScore4And3:
    def test_query_in_address_with_website(self):
        data = lead(
            name="Servicios Integrales",
            address="Local frente a la academia de baile",
            website="https://example.com",
            domain="example.com",
        )
        score, label = calculate_lead_score(data, "academia de baile")
        assert score == 4
        assert label == "Bueno"

    def test_query_in_corpus_no_website_gives_3(self):
        data = lead(
            name="Clases Express",
            address="Zona de academias de baile",
        )
        score, label = calculate_lead_score(data, "academia de baile")
        assert score == 3


# ── Score 3: service keywords (rescued lead) ───────────────────────────────

class TestScore3Rescued:
    def test_service_keyword_clases(self):
        """Name doesn't match query but 'clases' keyword signals a service biz."""
        data = lead(
            name="Rodrigo M.",
            address="Clases en horario matutino y vespertino",
            phone="5551234567",
            website="https://rodrigo.com",
            domain="rodrigo.com",
        )
        score, label = calculate_lead_score(data, "baile")
        assert score == 3
        assert label == "Rescatado"

    def test_service_keyword_inscripciones(self):
        data = lead(
            name="Centro Deportivo",
            address="Inscripciones abiertas todo el año",
            phone="5559876543",
        )
        score, label = calculate_lead_score(data, "fitness")
        assert score == 3

    def test_service_keyword_mensualidad(self):
        data = lead(
            name="Espacio Creativo",
            address="Mensualidad accesible, pregunta por paquetes",
            instagram="https://instagram.com/espaciocreativo",
        )
        score, label = calculate_lead_score(data, "pintura")
        assert score == 3


# ── Score 2: digital presence but no keywords ──────────────────────────────

class TestScore2:
    def test_multiple_social_channels_no_keywords(self):
        data = lead(
            name="Juan García",
            instagram="https://instagram.com/juangarcia",
            facebook="https://facebook.com/juangarcia",
            website="https://juangarcia.com",
            domain="juangarcia.com",
        )
        score, label = calculate_lead_score(data, "baile")
        assert score == 2
        assert label == "Débil"


# ── Score 1: bare minimum data ─────────────────────────────────────────────

class TestScore1:
    def test_only_phone(self):
        data = lead(name="Sin Web", phone="5550000000")
        score, label = calculate_lead_score(data, "gym")
        assert score == 1
        assert label == "Débil"

    def test_only_one_social(self):
        data = lead(name="Perfil", instagram="https://instagram.com/perfil_sin_mas")
        score, label = calculate_lead_score(data, "yoga")
        assert score == 1


# ── Score 0: spam / empty ──────────────────────────────────────────────────

class TestScore0:
    def test_completely_empty_lead(self):
        data = lead(name=None)
        score, label = calculate_lead_score(data, "dentista")
        assert score == 0
        assert label == "Spam/Vacío"

    def test_spam_signal_in_description(self):
        data = lead(
            name="Random Person",
            address="DM for promo, link in bio",
        )
        score, label = calculate_lead_score(data, "yoga")
        assert score == 0
        assert label == "Spam/Vacío"


# ── Edge cases ─────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_query_string(self):
        """Empty query should not crash; score based on other signals."""
        data = lead(name="Negocio", phone="1234567890", website="https://x.com")
        score, label = calculate_lead_score(data, "")
        assert isinstance(score, int)
        assert 0 <= score <= 5

    def test_single_word_query(self):
        data = lead(name="Gym Monterrey")
        score, label = calculate_lead_score(data, "gym")
        assert score == 5

    def test_multiword_query_partial_match(self):
        """One query term matching name is enough for score 5."""
        data = lead(name="Fitness Studio Monterrey")
        score, label = calculate_lead_score(data, "fitness nutrition gym")
        assert score == 5

"""
Unit tests for src/core/models.py

Tests cover:
- Business instantiation with all field types
- Phone normalization (strips formatting, keeps leading +)
- Domain derivation from website URL (strips www, path, protocol)
- to_dict() serialization (emails as CSV string, score/quality_label included)
"""

import pytest
from src.core.models import Business


class TestBusinessInstantiation:
    def test_minimal_business(self):
        """A Business with only a name should be valid."""
        biz = Business(name="Café Central")
        assert biz.name == "Café Central"
        assert biz.phone is None
        assert biz.website is None
        assert biz.domain is None
        assert biz.emails == []
        assert biz.score == -1
        assert biz.quality_label == "—"

    def test_full_business(self):
        """All fields should be storable."""
        biz = Business(
            name="Studio Dance",
            phone="5551234567",
            website="https://studiodance.mx",
            address="Av. Principal 100, CDMX",
            rating=4.5,
            reviews_count=200,
            emails=["hola@studiodance.mx"],
            instagram="https://instagram.com/studiodance",
            tiktok="https://tiktok.com/@studiodance",
            facebook="https://facebook.com/studiodance",
            ig_followers="12.5K",
            tiktok_followers="8K",
            fb_followers="3,200",
            score=5,
            quality_label="Excelente",
        )
        assert biz.rating == 4.5
        assert biz.reviews_count == 200
        assert biz.ig_followers == "12.5K"


class TestPhoneNormalization:
    def test_strips_spaces_and_dashes(self):
        biz = Business(name="X", phone="55 5123-4567")
        assert biz.phone == "5551234567"

    def test_strips_parentheses(self):
        biz = Business(name="X", phone="(55) 5123 4567")
        assert biz.phone == "5551234567"

    def test_strips_leading_plus(self):
        biz = Business(name="X", phone="+52 (55) 5123-4567")
        assert biz.phone == "525551234567"

    def test_all_digits_unchanged(self):
        biz = Business(name="X", phone="5551234567")
        assert biz.phone == "5551234567"

    def test_none_phone(self):
        biz = Business(name="X", phone=None)
        assert biz.phone is None


class TestDomainDerivation:
    def test_strips_www(self):
        biz = Business(name="X", website="https://www.example.com")
        assert biz.domain == "example.com"

    def test_strips_path(self):
        biz = Business(name="X", website="https://example.com/sobre-nosotros")
        assert biz.domain == "example.com"

    def test_strips_mobile_prefix(self):
        biz = Business(name="X", website="https://m.facebook.com/mybiz")
        assert biz.domain == "facebook.com"

    def test_https_and_http(self):
        biz = Business(name="X", website="http://mitienda.com.mx/")
        assert biz.domain == "mitienda.com.mx"

    def test_none_website(self):
        biz = Business(name="X", website=None)
        assert biz.domain is None

    def test_explicit_domain_not_overwritten(self):
        """If domain is provided explicitly, __post_init__ should not overwrite it."""
        biz = Business(name="X", website="https://www.example.com", domain="custom.com")
        assert biz.domain == "custom.com"


class TestToDict:
    def test_emails_serialized_as_csv_string(self):
        biz = Business(name="X", emails=["a@x.com", "b@x.com"])
        d = biz.to_dict()
        assert "a@x.com" in d["emails"]
        assert "b@x.com" in d["emails"]

    def test_empty_emails_is_none(self):
        biz = Business(name="X")
        d = biz.to_dict()
        assert d["emails"] is None

    def test_unscored_business_has_none_score(self):
        """score == -1 (default) should serialize as None, not -1."""
        biz = Business(name="X")
        d = biz.to_dict()
        assert d["score"] is None

    def test_scored_business_exports_score(self):
        biz = Business(name="X", score=4, quality_label="Bueno")
        d = biz.to_dict()
        assert d["score"] == 4
        assert d["quality_label"] == "Bueno"

    def test_all_expected_keys_present(self):
        biz = Business(name="X")
        d = biz.to_dict()
        expected_keys = {
            "name", "phone", "website", "domain", "address",
            "rating", "reviews_count", "emails",
            "instagram", "tiktok", "facebook",
            "ig_followers", "tiktok_followers", "fb_followers",
            "score", "quality_label",
        }
        assert expected_keys == set(d.keys())

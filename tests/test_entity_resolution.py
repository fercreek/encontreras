"""
Unit tests for src/core/entity_resolution.py

Tests cover:
- Merging duplicates that share the same phone number
- Merging duplicates that share the same domain (no phone)
- Email deduplication and concatenation across merged rows
- Preserving distinct businesses as separate rows
- Handling empty input
- Mixed scenarios (some with phone, some with only domain)
"""

import pytest
from src.core.models import Business
from src.core.entity_resolution import resolve_entities


class TestEmptyInput:
    def test_empty_list_returns_empty_dataframe(self):
        df = resolve_entities([])
        assert df.empty


class TestMergeByPhone:
    def test_same_phone_merges_to_one_row(self):
        b1 = Business(name="Café Alpha", phone="5551234567", website="https://cafealpha.com")
        b2 = Business(name="Cafe Alpha", phone="5551234567", website="https://www.cafealpha.com")
        df = resolve_entities([b1, b2])
        assert len(df) == 1

    def test_phone_formatting_variants_merge(self):
        """'+52 (55) 1234-5678' and '5251234567' should normalize to the same phone."""
        b1 = Business(name="Dentista Pérez", phone="+52 55 1234 5678")
        b2 = Business(name="Dentista Perez", phone="525512345678")
        df = resolve_entities([b1, b2])
        assert len(df) == 1

    def test_emails_combined_from_both_rows(self):
        b1 = Business(name="Studio A", phone="1111111111", emails=["info@studio.com"])
        b2 = Business(name="Studio A", phone="1111111111", emails=["ventas@studio.com"])
        df = resolve_entities([b1, b2])
        assert len(df) == 1
        merged_emails = df.iloc[0]["emails"]
        assert "info@studio.com" in merged_emails
        assert "ventas@studio.com" in merged_emails

    def test_duplicate_emails_not_repeated(self):
        b1 = Business(name="X", phone="1111111111", emails=["a@x.com"])
        b2 = Business(name="X", phone="1111111111", emails=["a@x.com"])
        df = resolve_entities([b1, b2])
        emails = df.iloc[0]["emails"]
        assert emails.count("a@x.com") == 1

    def test_non_null_fields_preserved(self):
        """The richer row's data should survive the merge."""
        b1 = Business(name="Pizza A", phone="2222222222", website=None)
        b2 = Business(name="Pizza A", phone="2222222222", website="https://pizzaa.mx")
        df = resolve_entities([b1, b2])
        assert df.iloc[0]["website"] == "https://pizzaa.mx"


class TestMergeByDomain:
    def test_same_domain_no_phone_merges(self):
        b1 = Business(name="Taco Place", website="https://tacoplace.mx")
        b2 = Business(name="Taco Place CDMX", website="https://www.tacoplace.mx")
        df = resolve_entities([b1, b2])
        assert len(df) == 1

    def test_domain_difference_keeps_separate(self):
        b1 = Business(name="Biz A", website="https://biza.com")
        b2 = Business(name="Biz B", website="https://bizb.com")
        df = resolve_entities([b1, b2])
        assert len(df) == 2


class TestDistinctBusinesses:
    def test_different_phone_stays_separate(self):
        b1 = Business(name="Fast Food A", phone="1111111111")
        b2 = Business(name="Fast Food B", phone="2222222222")
        df = resolve_entities([b1, b2])
        assert len(df) == 2

    def test_three_different_businesses(self):
        businesses = [
            Business(name="A", phone="1111111111", website="https://a.com"),
            Business(name="B", phone="2222222222", website="https://b.com"),
            Business(name="C", phone="3333333333", website="https://c.com"),
        ]
        df = resolve_entities(businesses)
        assert len(df) == 3


class TestMixedScenario:
    def test_some_with_phone_some_with_domain_only(self):
        """
        b1 & b2 share phone → merge to 1.
        b3 & b4 share domain (no phone) → merge to 1.
        b5 is unique.
        Result: 3 rows.
        """
        b1 = Business(name="Gym X", phone="5000000001", website="https://gymx.com")
        b2 = Business(name="Gym X Sucursal", phone="5000000001")
        b3 = Business(name="Yoga Studio", website="https://yogastudio.mx")
        b4 = Business(name="Yoga Studio Sur", website="https://www.yogastudio.mx")
        b5 = Business(name="Pilates Pro", phone="5000000099", website="https://pilates.pro")
        df = resolve_entities([b1, b2, b3, b4, b5])
        assert len(df) == 3

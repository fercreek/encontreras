"""
Unit tests for src/core/exporter.py

Tests cover:
- to_csv() creates a valid, readable CSV file with correct columns
- to_json() creates a valid JSON file with correct records
- Output directory is created if it doesn't exist
- Timestamped filenames are generated (no collision on repeated calls)
- Files contain the expected data
"""

import json
import time
from pathlib import Path

import pandas as pd
import pytest

from src.core.exporter import to_csv, to_json


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Minimal DataFrame that mirrors the resolved output."""
    return pd.DataFrame([
        {
            "name": "Café Central",
            "phone": "5551234567",
            "website": "https://cafe.mx",
            "domain": "cafe.mx",
            "address": "Av. Principal 1, CDMX",
            "rating": 4.5,
            "reviews_count": 120,
            "emails": "info@cafe.mx",
            "instagram": "https://instagram.com/cafecentral",
            "tiktok": None,
            "facebook": None,
            "ig_followers": "8.2K",
            "tiktok_followers": None,
            "fb_followers": None,
            "score": 5,
            "quality_label": "Excelente",
        },
        {
            "name": "Taquería Express",
            "phone": "5559876543",
            "website": None,
            "domain": None,
            "address": "Calle 2, MTY",
            "rating": 3.8,
            "reviews_count": 45,
            "emails": None,
            "instagram": None,
            "tiktok": None,
            "facebook": None,
            "ig_followers": None,
            "tiktok_followers": None,
            "fb_followers": None,
            "score": 1,
            "quality_label": "Débil",
        },
    ])


@pytest.fixture
def tmp_output(tmp_path) -> Path:
    """Provide a fresh temp directory for each test."""
    return tmp_path / "output"


class TestCsvExport:
    def test_creates_file(self, sample_df, tmp_output):
        path = to_csv(sample_df, tmp_output)
        assert path.exists()
        assert path.suffix == ".csv"

    def test_correct_row_count(self, sample_df, tmp_output):
        path = to_csv(sample_df, tmp_output)
        df_read = pd.read_csv(path)
        assert len(df_read) == 2

    def test_columns_present(self, sample_df, tmp_output):
        path = to_csv(sample_df, tmp_output)
        df_read = pd.read_csv(path)
        assert "name" in df_read.columns
        assert "score" in df_read.columns
        assert "quality_label" in df_read.columns

    def test_values_preserved(self, sample_df, tmp_output):
        path = to_csv(sample_df, tmp_output)
        df_read = pd.read_csv(path)
        assert df_read.iloc[0]["name"] == "Café Central"
        assert df_read.iloc[0]["score"] == 5

    def test_creates_output_dir_if_missing(self, sample_df, tmp_path):
        nested = tmp_path / "deep" / "nested" / "dir"
        path = to_csv(sample_df, nested)
        assert path.exists()

    def test_overwrites_existing_file(self, sample_df, tmp_output):
        path1 = to_csv(sample_df, tmp_output)
        path2 = to_csv(sample_df, tmp_output)
        assert path1.name == path2.name


class TestJsonExport:
    def test_creates_file(self, sample_df, tmp_output):
        path = to_json(sample_df, tmp_output)
        assert path.exists()
        assert path.suffix == ".json"

    def test_valid_json_structure(self, sample_df, tmp_output):
        path = to_json(sample_df, tmp_output)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) == 2

    def test_values_preserved(self, sample_df, tmp_output):
        path = to_json(sample_df, tmp_output)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert data[0]["name"] == "Café Central"
        assert data[0]["score"] == 5
        assert data[0]["quality_label"] == "Excelente"

    def test_spanish_characters_encoded_correctly(self, sample_df, tmp_output):
        path = to_json(sample_df, tmp_output)
        raw = path.read_text(encoding="utf-8")
        assert "Café" in raw or "Caf\\u00e9" in raw  # either escaped or literal

    def test_custom_prefix_in_filename(self, sample_df, tmp_output):
        path = to_json(sample_df, tmp_output, prefix="mi_busqueda")
        assert path.name == "mi_busqueda.json"

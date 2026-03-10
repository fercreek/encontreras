"""
Entity Resolution — de-duplicate businesses using phone and domain as keys.
"""

from __future__ import annotations

import pandas as pd

from src.core.models import Business


def _first_non_null(series: pd.Series):
    """Return the first non-null value in a series, or None."""
    non_null = series.dropna()
    return non_null.iloc[0] if len(non_null) > 0 else None


def _merge_emails(series: pd.Series) -> str | None:
    """Concatenate unique emails across duplicate rows."""
    all_emails: set[str] = set()
    for val in series.dropna():
        for email in str(val).split(", "):
            email = email.strip()
            if email:
                all_emails.add(email.lower())
    return ", ".join(sorted(all_emails)) if all_emails else None


def _build_agg_dict(columns: list[str]) -> dict:
    """Build aggregation rules: merge emails, take first non-null for the rest."""
    agg: dict = {}
    for col in columns:
        if col == "emails":
            agg[col] = _merge_emails
        else:
            agg[col] = _first_non_null
    return agg


def resolve_entities(businesses: list[Business]) -> pd.DataFrame:
    """
    De-duplicate a list of Business objects.

    Strategy:
        1. Group by **phone** (priority 1) — merge rows with the same phone.
        2. Group by **domain** (priority 2) — merge remaining rows with the same domain.
        3. Keep unique rows as-is.

    Returns a clean DataFrame with one row per unique business.
    """
    if not businesses:
        return pd.DataFrame()

    df = pd.DataFrame([b.to_dict() for b in businesses])

    # ── Pass 1: merge by phone ────────────────────────────────────────────
    has_phone = df["phone"].notna() & (df["phone"] != "")
    phone_group = df[has_phone]
    no_phone = df[~has_phone]

    value_cols = [c for c in df.columns if c != "phone"]

    if not phone_group.empty:
        phone_merged = (
            phone_group
            .groupby("phone", as_index=False)
            .agg(_build_agg_dict(value_cols))
        )
    else:
        phone_merged = phone_group

    # Combine back
    df = pd.concat([phone_merged, no_phone], ignore_index=True)

    # ── Pass 2: merge by domain ───────────────────────────────────────────
    has_domain = df["domain"].notna() & (df["domain"] != "")
    domain_group = df[has_domain]
    no_domain = df[~has_domain]

    value_cols_d = [c for c in df.columns if c != "domain"]

    if not domain_group.empty:
        domain_merged = (
            domain_group
            .groupby("domain", as_index=False)
            .agg(_build_agg_dict(value_cols_d))
        )
    else:
        domain_merged = domain_group

    df = pd.concat([domain_merged, no_domain], ignore_index=True)

    # ── Clean up ──────────────────────────────────────────────────────────
    df = df.drop_duplicates(subset=["name", "phone", "domain"])
    df = df.reset_index(drop=True)

    return df

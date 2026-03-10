"""
Export resolved data to CSV and/or JSON.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from rich.console import Console

console = Console()


def _ensure_dir(directory: str | Path) -> Path:
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _get_filename(prefix: str, ext: str) -> str:
    return f"{prefix}.{ext}"


def to_csv(df: pd.DataFrame, output_dir: str | Path, prefix: str = "encontreras_demo") -> Path:
    """Save DataFrame to a CSV file."""
    out = _ensure_dir(output_dir)
    filename = _get_filename(prefix, "csv")
    filepath = out / filename
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    console.print(f"[green]✔[/green] CSV saved → [bold]{filepath}[/bold]")
    return filepath


def to_json(df: pd.DataFrame, output_dir: str | Path, prefix: str = "encontreras_demo") -> Path:
    """Save DataFrame to a JSON file."""
    out = _ensure_dir(output_dir)
    filename = _get_filename(prefix, "json")
    filepath = out / filename
    df.to_json(filepath, orient="records", indent=2, force_ascii=False)
    console.print(f"[green]✔[/green] JSON saved → [bold]{filepath}[/bold]")
    return filepath

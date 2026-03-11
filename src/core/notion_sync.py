"""
Module for syncing verified, AI-enriched leads from local SQLite to Notion.
"""

from __future__ import annotations

import os
import re
import sqlite3
from typing import Any

from notion_client import Client
from rich.console import Console

console = Console()

def get_notion_client() -> Client | None:
    token = os.getenv("NOTION_TOKEN")
    if not token:
        return None
    return Client(auth=token)

def format_whatsapp(phone: str | None) -> str | None:
    if not phone:
        return None
    digits = re.sub(r'\D', '', phone)
    if not digits:
        return None
    # Assuming standard Mexico code if not provided, but mostly standard digits
    if len(digits) == 10:
        return f"https://wa.me/52{digits}"
    return f"https://wa.me/{digits}"

def push_to_notion(client: Client, database_id: str, row: sqlite3.Row) -> str | None:
    """Create a page in Notion and return its URL."""
    try:
        # Prepare properties based on Notion schema
        name = row["name"] or "Sin nombre"
        insta = row["instagram"] or ""
        website = row["website"] or row["maps_url"] or ""
        clean_wa = format_whatsapp(row["phone"]) or ""
        
        # Use full address or parse city - using Address for now
        address = row["address"] or ""
        
        context = row["context"] or ""
        why = row["why_they_matter"] or ""
        ice = row["icebreaker"] or ""

        properties: dict[str, Any] = {
            "Name / Company": {
                "title": [{"text": {"content": name}}]
            },
            "Insta": {
                "url": insta if insta else None
            },
            "Profile URL": {
                "url": website if website else None
            },
            "WhatsApp": {
                "url": clean_wa if clean_wa else None
            },
            "Ciudad": {
                "rich_text": [{"text": {"content": address[:100]}}] if address else []
            },
            "Contexto": {
                "rich_text": [{"text": {"content": context[:2000]}}] if context else []
            },
            "Why They Matter": {
                "rich_text": [{"text": {"content": why[:2000]}}] if why else []
            },
            "DM Personalizado": {
                "rich_text": [{"text": {"content": ice[:2000]}}] if ice else []
            }
        }
        
        # Add Select options if they match user's Notion exactly.
        # If Notion options are different, these might throw errors. We'll send them as text or basic select.
        properties["Status"] = {
            "select": {"name": "To Contact"}
        }
        properties["Canal"] = {
            "select": {"name": "WhatsApp"}
        }
        
        # Clean null URLs (Notion rejects empty string URLs)
        for key in ["Insta", "Profile URL", "WhatsApp"]:
            if properties[key].get("url") == "":
                properties[key]["url"] = None
        
        # Create page
        page = client.pages.create(
            parent={"database_id": database_id},
            properties=properties
        )
        return page.get("url")
    except Exception as e:
        console.print(f"[red]Error pushing to Notion para {row['name']}: {e}[/red]")
        return None

def sync_leads_to_notion(db_path: str = "./output/encontreras.db", limit: int = 10) -> None:
    """Read pending leads and sync them."""
    client = get_notion_client()
    database_id = os.getenv("NOTION_DATABASE_ID")
    
    if not client or not database_id:
        console.print("[red]❌ NOTION_TOKEN y NOTION_DATABASE_ID son requeridos en .env[/red]")
        return
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # We only want leads that have been analyzed by AI and haven't been synced to Notion yet
    c.execute('''
        SELECT * FROM businesses
        WHERE context IS NOT NULL 
          AND (notion_url IS NULL OR notion_url = "")
        LIMIT ?
    ''', (limit,))
    
    rows = c.fetchall()
    if not rows:
        console.print("[green]✔ No hay prospectos pendientes estructurados para sincronizar.[/green]")
        conn.close()
        return
        
    console.print(f"[blue]Sincronizando {len(rows)} prospectos a Notion...[/blue]")
    updates = 0
    
    for row in rows:
        console.print(f"Exportando: [cyan]{row['name']}[/cyan]...")
        notion_url = push_to_notion(client, database_id, row)
        
        if notion_url:
            c.execute('''
                UPDATE businesses 
                SET notion_url = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (notion_url, row['id']))
            conn.commit()
            updates += 1
            console.print(f"  [green]✔ Guardado en Notion: {notion_url}[/green]")
            
    conn.close()
    console.print(f"\n[bold green]Sincronización completada: {updates}/{len(rows)}.[/bold green]")

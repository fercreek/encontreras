"""
SQLite Database module for persistent local storage (Upserts and querying).
Prepares the ground for future migration to Supabase (PostgreSQL).
"""

import sqlite3
from pathlib import Path

import pandas as pd


def init_db(db_path: str = "./output/encontreras.db") -> None:
    """Initialize the SQLite database schema if it doesn't exist."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(path))
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            website TEXT,
            domain TEXT,
            address TEXT,
            rating REAL,
            reviews_count INTEGER,
            category TEXT,
            hours TEXT,
            description TEXT,
            price_level TEXT,
            maps_url TEXT,
            plus_code TEXT,
            emails TEXT,
            instagram TEXT,
            tiktok TEXT,
            facebook TEXT,
            site_status TEXT,
            site_issues TEXT,
            score INTEGER,
            quality_label TEXT,
            ig_followers TEXT,
            tiktok_followers TEXT,
            fb_followers TEXT,
            context TEXT,
            why_they_matter TEXT,
            icebreaker TEXT,
            notion_url TEXT,
            inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def save_to_db(df: pd.DataFrame, db_path: str = "./output/encontreras.db") -> None:
    """
    Save or Update (UPSERT) businesses in the SQLite database.
    Matches existing records by phone or domain to avoid duplicates.
    """
    init_db(db_path)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    fields = [
        "name", "phone", "website", "domain", "address", "rating", "reviews_count",
        "category", "hours", "description", "price_level", "maps_url", "plus_code",
        "emails", "instagram", "tiktok", "facebook", "site_status", "site_issues",
        "score", "quality_label", "ig_followers", "tiktok_followers", "fb_followers",
        "context", "why_they_matter", "icebreaker", "notion_url"
    ]
    
    for _, row in df.iterrows():
        biz_dict = row.to_dict()
        
        # Flatten lists to comma-separated strings for SQLite
        emails = biz_dict.get('emails', [])
        if isinstance(emails, list):
             biz_dict['emails'] = ",".join(emails) if emails else None
             
        site_issues = biz_dict.get('site_issues', [])
        if isinstance(site_issues, list):
             biz_dict['site_issues'] = ",".join(site_issues) if site_issues else None

        # Clean NaN/None for SQL injection
        for k, v in biz_dict.items():
            if pd.isna(v):
                biz_dict[k] = None
                
        # 1. Match existing record
        existing_id = None
        phone = biz_dict.get('phone')
        domain = biz_dict.get('domain')
        
        if phone:
            cursor.execute("SELECT id FROM businesses WHERE phone = ?", (phone,))
            res = cursor.fetchone()
            if res:
                existing_id = res['id']
                
        if not existing_id and domain:
            cursor.execute("SELECT id FROM businesses WHERE domain = ?", (domain,))
            res = cursor.fetchone()
            if res:
                existing_id = res['id']

        # 2. Extract values in the exact order of 'fields'
        values = [biz_dict.get(f) for f in fields]
        
        # 3. Insert or Update
        if existing_id:
            set_clause = ", ".join([f"{f} = ?" for f in fields])
            values.append(existing_id)
            cursor.execute(f'''
                UPDATE businesses 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', values)
        else:
            placeholders = ", ".join(["?"] * len(fields))
            cols = ", ".join(fields)
            cursor.execute(f'''
                INSERT INTO businesses ({cols})
                VALUES ({placeholders})
            ''', values)

    conn.commit()
    conn.close()

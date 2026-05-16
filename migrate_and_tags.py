"""
migrate_add_tags.py
===================
Jalankan SEKALI untuk menambah kolom `tags` ke tabel reviews yang sudah ada.
Letakkan file ini di root project (sejajar dengan main.py), lalu jalankan:

    python migrate_add_tags.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from database import engine

def run():
    with engine.connect() as conn:
        # cek apakah kolom sudah ada
        result = conn.execute(text("PRAGMA table_info(reviews)"))
        cols = [row[1] for row in result]
        if "tags" in cols:
            print("[migrate] Kolom 'tags' sudah ada, tidak perlu migrasi.")
            return
        conn.execute(text("ALTER TABLE reviews ADD COLUMN tags TEXT DEFAULT '[]'"))
        conn.commit()
        print("[migrate] Kolom 'tags' berhasil ditambahkan ke tabel reviews.")

if __name__ == "__main__":
    run()

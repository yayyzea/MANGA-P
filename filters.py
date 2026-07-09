# filters.py
"""
Modul untuk semua logika filter.

Isi modul:
- Konstanta pilihan genre & status (dipakai oleh filter panel UI).
- Fungsi pencocokan (matching) per-kriteria (query, genre, status, tahun).
- Fungsi utama `filter_collection_entries()` untuk memfilter koleksi
  manga milik user (dipakai di halaman Library).
"""

from __future__ import annotations


# ─────────────────────────────────────────────────────────────────────────────
# Konstanta pilihan filter
# ─────────────────────────────────────────────────────────────────────────────

# Daftar genre yang bisa dipilih di filter panel (Library & Search page).
GENRES = [
    "Action",        "Drama",
    "Adventure",     "Fantasy",
    "Avant Garde",   "Gourmet",
    "Award Winning", "Horror",
    "Comedy",        "Mystery",
    "Romance",       "Sci-Fi",
    "Slice of Life", "Sports",
    "Supernatural",
]

# Status koleksi milik user (dipakai di Library, Detail, dan model UserCollection).
COLLECTION_STATUS_OPTIONS = ["Plan to Read", "Reading", "Completed", "Dropped"]

# Status publikasi manga itu sendiri (dipakai di filter panel Search/Home page).
MANGA_STATUS_OPTIONS = ["Publishing", "Finished", "On Hiatus"]


# ─────────────────────────────────────────────────────────────────────────────
# Fungsi pencocokan per-kriteria
# ─────────────────────────────────────────────────────────────────────────────

def manga_matches_query(manga, query: str) -> bool:
    """True kalau judul manga cocok dengan keyword pencarian (case-insensitive)."""
    q = (query or "").strip().lower()
    if not q:
        return True
    return q in (manga.title or "").lower()


def manga_matches_genres(manga, genres: list) -> bool:
    """True kalau manga punya minimal salah satu genre yang dipilih."""
    if not genres:
        return True
    manga_genres = [g.strip().lower() for g in (manga.genres or "").split(",")]
    return any(g.lower() in manga_genres for g in genres)


def entry_matches_statuses(entry_status: str, statuses: list) -> bool:
    """True kalau status koleksi entry ada di daftar status yang dipilih."""
    if not statuses:
        return True
    return entry_status in statuses


def manga_matches_year(manga, year) -> bool:
    """True kalau tahun rilis manga sesuai filter tahun (kalau valid)."""
    if not year:
        return True
    try:
        return manga.year == int(year)
    except (TypeError, ValueError):
        # Kalau input tahun tidak valid, jangan buang entry (biarkan lolos)
        return True


# ─────────────────────────────────────────────────────────────────────────────
# Fungsi filter utama
# ─────────────────────────────────────────────────────────────────────────────

def filter_collection_entries(entries, query: str = "", genres: list = None,
                               statuses: list = None, year: str = None):
    """
    Filter list UserCollection entries berdasarkan query judul, genre,
    status koleksi, dan tahun rilis sekaligus.

    Dipakai oleh LibraryPage untuk menyaring 'Last Read' & 'My Books'.
    """
    genres = genres or []
    statuses = statuses or []

    result = []
    for entry in entries:
        manga = entry.manga
        if not manga:
            continue
        if not manga_matches_query(manga, query):
            continue
        if not manga_matches_genres(manga, genres):
            continue
        if not entry_matches_statuses(entry.status, statuses):
            continue
        if not manga_matches_year(manga, year):
            continue
        result.append(entry)
    return result

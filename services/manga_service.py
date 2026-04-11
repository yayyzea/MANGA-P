from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from models.manga import Manga
from database import get_session
from services.jikan_service import JikanService

CACHE_EXPIRY_DAYS = 7


class MangaService:
    def __init__(self):
        self.jikan = JikanService()

    # ── Public API ────────────────────────────────────────────────────────────

    def search(
        self,
        query: str = "",
        genres: list[str] = None,
        status: str = None,
        year: int = None,
        sort_by: str = "score",
        sort_order: str = "desc",
        page: int = 1,
        limit: int = 16,
    ) -> list[Manga]:
        session = get_session()
        try:
            has_query  = bool(query and query.strip())
            has_genres = bool(genres)

            if has_query:
                self._fetch_and_cache_keyword(query, session)
            if has_genres:
                self._fetch_and_cache_genres(genres, status, session)

            results = self._query_db(
                session, query, genres, status, year, sort_by, sort_order
            )
            offset = (page - 1) * limit
            return results[offset: offset + limit]
        finally:
            session.close()

    def get_top_manga(self, limit: int = 8) -> list[Manga]:
        session = get_session()
        try:
            cached = (
                session.query(Manga)
                .filter(Manga.is_manual == False, Manga.score != None)
                .order_by(Manga.score.desc())
                .limit(limit)
                .all()
            )
            if len(cached) >= limit:
                return cached
            raw_list = self.jikan.get_top_manga(limit=limit)
            self._bulk_upsert(raw_list, session)
            return (
                session.query(Manga)
                .filter(Manga.is_manual == False, Manga.score != None)
                .order_by(Manga.score.desc())
                .limit(limit)
                .all()
            )
        finally:
            session.close()

    def get_by_id(self, manga_id: int) -> Optional[Manga]:
        session = get_session()
        try:
            manga = session.query(Manga).filter(Manga.id == manga_id).first()
            if manga and self._is_stale(manga) and manga.mal_id:
                raw = self.jikan.get_manga_by_id(manga.mal_id)
                if raw:
                    for key, val in raw.items():
                        if key not in ("id", "created_at") and hasattr(manga, key):
                            setattr(manga, key, val)
                    session.commit()
                    session.refresh(manga)
            return manga
        finally:
            session.close()

    def get_recommendations(self, manga: Manga, limit: int = 4) -> list[Manga]:
        """
        Priority order:
        1. Same title keyword (e.g. "Naruto" → other Naruto series)
        2. Same author + same genre
        3. Same genre only (fetch from Jikan if cache insufficient)
        """
        if not manga:
            return []

        # Parse helpers
        try:
            genre_list = manga.genres_list()
        except AttributeError:
            genre_list = [g.strip() for g in (manga.genres or "").split(",") if g.strip()]

        # Extract base title keyword (first meaningful word, min 4 chars)
        title_words = (manga.title or "").split()
        title_kw    = next((w for w in title_words if len(w) >= 4), title_words[0] if title_words else "")

        # Author (first author name)
        author_kw = ""
        if manga.authors:
            parts     = manga.authors.split(",")
            author_kw = parts[0].strip() if parts else ""

        session = get_session()
        try:
            results = []
            seen_ids = {manga.id}

            def _add(items):
                for m in items:
                    if m.id not in seen_ids:
                        seen_ids.add(m.id)
                        results.append(m)

            # ── Priority 1: same title keyword ────────────────────────────────
            if title_kw:
                p1 = (
                    session.query(Manga)
                    .filter(
                        Manga.title.ilike(f"%{title_kw}%"),
                        Manga.id != manga.id,
                    )
                    .order_by(Manga.score.desc())
                    .limit(limit)
                    .all()
                )
                _add(p1)

            # ── Priority 2: same author + same genre ──────────────────────────
            if len(results) < limit and author_kw and genre_list:
                genre_filters = [Manga.genres.contains(g) for g in genre_list[:2]]
                p2 = (
                    session.query(Manga)
                    .filter(
                        Manga.authors.contains(author_kw),
                        or_(*genre_filters),
                        Manga.id.notin_(seen_ids),
                    )
                    .order_by(Manga.score.desc())
                    .limit(limit - len(results))
                    .all()
                )
                _add(p2)

            # ── Priority 3: same genre (DB first, then Jikan fallback) ─────────
            if len(results) < limit and genre_list:
                genre_filters = [Manga.genres.contains(g) for g in genre_list[:3]]
                p3 = (
                    session.query(Manga)
                    .filter(
                        or_(*genre_filters),
                        Manga.id.notin_(seen_ids),
                    )
                    .order_by(Manga.score.desc())
                    .limit(limit - len(results))
                    .all()
                )
                _add(p3)

                # Still not enough → fetch from Jikan by genre
                if len(results) < limit:
                    raw_list = self.jikan.search_by_genres(genre_list[:2], limit=20)
                    self._bulk_upsert(raw_list, session)
                    genre_filters2 = [Manga.genres.contains(g) for g in genre_list[:3]]
                    p3b = (
                        session.query(Manga)
                        .filter(
                            or_(*genre_filters2),
                            Manga.id.notin_(seen_ids),
                        )
                        .order_by(Manga.score.desc())
                        .limit(limit - len(results))
                        .all()
                    )
                    _add(p3b)

            return results[:limit]

        finally:
            session.close()

    # ── Cache helpers ─────────────────────────────────────────────────────────

    def _fetch_and_cache_keyword(self, query: str, session: Session):
        raw_list = self.jikan.search_manga(query)
        self._bulk_upsert(raw_list, session)

    def _fetch_and_cache_genres(self, genres: list[str], status: str, session: Session):
        first_genre = genres[0] if genres else ""
        if first_genre:
            cached_count = (
                session.query(Manga)
                .filter(Manga.genres.contains(first_genre))
                .count()
            )
            if cached_count >= 8:
                return
        raw_list = self.jikan.search_by_genres(genres, status=status, limit=20)
        self._bulk_upsert(raw_list, session)

    def _bulk_upsert(self, raw_list: list[dict], session: Session):
        seen = set()
        for raw in raw_list:
            mal_id = raw.get("mal_id")
            if mal_id and mal_id in seen:
                continue
            if mal_id:
                seen.add(mal_id)
                existing = session.query(Manga).filter(Manga.mal_id == mal_id).first()
                if existing:
                    if self._is_stale(existing):
                        for key, val in raw.items():
                            if key not in ("id", "created_at") and hasattr(existing, key):
                                setattr(existing, key, val)
                    continue
            try:
                manga = Manga(**{k: v for k, v in raw.items() if k != "id"})
                session.add(manga)
                session.flush()
            except Exception as e:
                print(f"[MangaService] Skipping mal_id={mal_id}: {e}")
                session.rollback()
        try:
            session.commit()
        except Exception as e:
            print(f"[MangaService] Commit failed: {e}")
            session.rollback()

    def _query_db(self, session, query, genres, status, year, sort_by, sort_order):
        q = session.query(Manga)
        if query:
            q = q.filter(or_(
                Manga.title.ilike(f"%{query}%"),
                Manga.title_en.ilike(f"%{query}%"),
            ))
        if genres:
            for genre in genres:
                q = q.filter(Manga.genres.contains(genre))
        if status:
            q = q.filter(Manga.status == status)
        if year:
            q = q.filter(Manga.year == year)
        sort_col = {"score": Manga.score, "title": Manga.title, "year": Manga.year}.get(sort_by, Manga.score)
        q = q.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
        return q.all()

    def _is_stale(self, manga: Manga) -> bool:
        if not manga.fetched_at:
            return True
        return datetime.now() - manga.fetched_at > timedelta(days=CACHE_EXPIRY_DAYS)

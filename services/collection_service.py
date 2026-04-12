from datetime import date, datetime
from typing import Optional
from sqlalchemy.orm import Session

from models.user_collection import UserCollection
from models.manga import Manga
from database import get_session


class CollectionService:
    """Manages user's personal manga collection (CRUD bookmark)."""

    # ── Create ────────────────────────────────────────────────────────────────

    def add(
        self,
        manga_id: int,
        status: str = "Plan to Read",
        current_chapter: int = 0,
        score: int = None,
        start_date: date = None,
        notes: str = None,
    ) -> Optional[UserCollection]:
        """Add a manga to the user's collection."""
        session = get_session()
        try:
            existing = (
                session.query(UserCollection)
                .filter(UserCollection.manga_id == manga_id)
                .first()
            )
            if existing:
                return existing  # Already in collection

            entry = UserCollection(
                manga_id=manga_id,
                status=status,
                current_chapter=current_chapter,
                score=score,
                start_date=start_date,
                notes=notes,
            )
            session.add(entry)
            session.commit()
            session.refresh(entry)
            return entry
        finally:
            session.close()

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_all(
        self,
        status_filter: str = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[UserCollection]:
        """Get all collection entries, optionally filtered and sorted."""
        session = get_session()
        try:
            q = session.query(UserCollection).join(Manga)
            if status_filter:
                q = q.filter(UserCollection.status == status_filter)

            sort_col = {
                "created_at": UserCollection.created_at,
                "title": Manga.title,
                "score": UserCollection.score,
                "updated_at": UserCollection.updated_at,
            }.get(sort_by, UserCollection.created_at)

            if sort_order == "asc":
                q = q.order_by(sort_col.asc())
            else:
                q = q.order_by(sort_col.desc())

            return q.all()
        finally:
            session.close()

    def get_by_manga_id(self, manga_id: int) -> Optional[UserCollection]:
        """Check if a manga is in the collection."""
        session = get_session()
        try:
            return (
                session.query(UserCollection)
                .filter(UserCollection.manga_id == manga_id)
                .first()
            )
        finally:
            session.close()

    def get_last_read(self, limit: int = 6) -> list[UserCollection]:
        """Get recently updated collection entries (last read)."""
        session = get_session()
        try:
            return (
                session.query(UserCollection)
                .filter(UserCollection.status.in_(["Reading", "Completed"]))
                .order_by(UserCollection.updated_at.desc())
                .limit(limit)
                .all()
            )
        finally:
            session.close()

    def is_in_collection(self, manga_id: int) -> bool:
        """Check whether a manga is already in the collection."""
        return self.get_by_manga_id(manga_id) is not None

    # ── Update ────────────────────────────────────────────────────────────────

    def update(
        self,
        collection_id: int,
        status: str = None,
        current_chapter: int = None,
        score: int = None,
        start_date: date = None,
        notes: str = None,
    ) -> Optional[UserCollection]:
        """Update a collection entry."""
        session = get_session()
        try:
            entry = (
                session.query(UserCollection)
                .filter(UserCollection.id == collection_id)
                .first()
            )
            if not entry:
                return None

            if status is not None:
                entry.status = status
                if status == "Completed" and not entry.finish_date:
                    entry.finish_date = date.today()
                if status == "Reading" and not entry.start_date:
                    entry.start_date = date.today()
            if current_chapter is not None:
                entry.current_chapter = current_chapter
            if score is not None:
                entry.score = score
            if start_date is not None:
                entry.start_date = start_date
            if notes is not None:
                entry.notes = notes

            entry.updated_at = datetime.now()
            session.commit()
            session.refresh(entry)
            return entry
        finally:
            session.close()

    # ── Delete ────────────────────────────────────────────────────────────────

    def delete(self, collection_id: int) -> bool:
        """Delete a collection entry (cascades to reviews)."""
        session = get_session()
        try:
            entry = (
                session.query(UserCollection)
                .filter(UserCollection.id == collection_id)
                .first()
            )
            if not entry:
                return False
            session.delete(entry)
            session.commit()
            return True
        finally:
            session.close()

    # ── Stats ─────────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Return aggregated stats for the dashboard."""
        session = get_session()
        try:
            all_entries = session.query(UserCollection).all()
            counts = {"Plan to Read": 0, "Reading": 0, "Completed": 0, "Dropped": 0}
            genre_counter = {}

            for entry in all_entries:
                counts[entry.status] = counts.get(entry.status, 0) + 1
                if entry.manga and entry.manga.genres:
                    for g in entry.manga.genres_list():
                        genre_counter[g] = genre_counter.get(g, 0) + 1

            top_genre = max(genre_counter, key=genre_counter.get) if genre_counter else None

            return {
                "total": len(all_entries),
                "counts": counts,
                "top_genre": top_genre,
            }
        finally:
            session.close()

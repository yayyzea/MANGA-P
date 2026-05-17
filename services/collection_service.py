from datetime import date, datetime
from typing import Optional
from sqlalchemy.orm import joinedload
from sqlalchemy import func

from models.user_collection import UserCollection
from models.manga import Manga
from database import get_session


class CollectionService:

    def add(
        self,
        user_id: int,
        manga_id: int,
        status: str = "Plan to Read",
        current_chapter: int = 0,
        score: int = None,
        start_date: date = None,
        notes: str = None,
    ) -> Optional[UserCollection]:
        session = get_session()
        try:
            existing = (
                session.query(UserCollection)
                .filter(UserCollection.user_id == user_id)
                .filter(UserCollection.manga_id == manga_id)
                .first()
            )
            if existing:
                if existing.manga:
                    _ = existing.manga.title
                return existing

            entry = UserCollection(
                user_id=user_id,
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
            if entry.manga:
                _ = entry.manga.title
                _ = entry.manga.genres
            return entry
        finally:
            session.close()

    def get_all(self, user_id: int, status_filter: str = None,
                sort_by: str = "created_at", sort_order: str = "desc"):
        session = get_session()
        try:
            q = session.query(UserCollection).options(
                joinedload(UserCollection.manga)
            ).filter(UserCollection.user_id == user_id)
            if status_filter:
                q = q.filter(UserCollection.status == status_filter)
            sort_col = {
                "created_at": UserCollection.created_at,
                "title": Manga.title,
                "score": UserCollection.score,
                "updated_at": UserCollection.updated_at,
            }.get(sort_by, UserCollection.created_at)
            q = q.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
            results = q.all()
            for obj in results:
                if obj.manga:
                    _ = obj.manga.title
            return results
        finally:
            session.close()

    def get_by_manga_id(self, manga_id: int, user_id: int = None):
        session = get_session()
        try:
            q = session.query(UserCollection).options(
                joinedload(UserCollection.manga)
            ).filter(UserCollection.manga_id == manga_id)
            if user_id is not None:
                q = q.filter(UserCollection.user_id == user_id)
            entry = q.first()
            if entry and entry.manga:
                _ = entry.manga.title
            return entry
        finally:
            session.close()

    def update(self, collection_id: int, status: str = None,
               current_chapter: int = None, score: int = None,
               start_date: date = None, notes: str = None):
        session = get_session()
        try:
            entry = session.query(UserCollection).options(
                joinedload(UserCollection.manga)
            ).filter(UserCollection.id == collection_id).first()
            if not entry:
                return None
            if status is not None:
                entry.status = status
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

    def delete(self, collection_id: int, user_id: int = None) -> bool:
        session = get_session()
        try:
            q = session.query(UserCollection).filter(UserCollection.id == collection_id)
            if user_id is not None:
                q = q.filter(UserCollection.user_id == user_id)
            entry = q.first()
            if not entry:
                return False
            session.delete(entry)
            session.commit()
            return True
        finally:
            session.close()

    def get_stats(self, user_id: int) -> dict:
        session = get_session()
        try:
            total = session.query(func.count(UserCollection.id)).filter(
                UserCollection.user_id == user_id
            ).scalar() or 0
            
            status_rows = session.query(
                UserCollection.status, func.count(UserCollection.id)
            ).filter(UserCollection.user_id == user_id).group_by(
                UserCollection.status
            ).all()
            
            counts = {"Plan to Read": 0, "Reading": 0, "Completed": 0, "Dropped": 0}
            for status, cnt in status_rows:
                if status in counts:
                    counts[status] = cnt
            
            genre_rows = session.query(Manga.genres).join(
                UserCollection, UserCollection.manga_id == Manga.id
            ).filter(
                UserCollection.user_id == user_id,
                Manga.genres != None,
                Manga.genres != ""
            ).all()
            
            genre_counter = {}
            for row in genre_rows:
                if row[0]:
                    for g in row[0].split(","):
                        g = g.strip()
                        if g:
                            genre_counter[g] = genre_counter.get(g, 0) + 1
            
            top_genre = max(genre_counter, key=genre_counter.get) if genre_counter else None

            author_rows = session.query(Manga.authors).join(
                UserCollection, UserCollection.manga_id == Manga.id
            ).filter(
                UserCollection.user_id == user_id,
                Manga.authors != None,
                Manga.authors != ""
            ).all()

            author_counter = {}
            for row in author_rows:
                if row[0]:
                    for a in row[0].split(","):
                        a = a.strip()
                        if a:
                            author_counter[a] = author_counter.get(a, 0) + 1

            top_author = max(author_counter, key=author_counter.get) if author_counter else None

            return {
                "total": total,
                "counts": counts,
                "top_genre": top_genre,
                "top_author": top_author,
                "genre_counts": dict(sorted(genre_counter.items(), key=lambda x: x[1], reverse=True)),
                "author_counts": dict(sorted(author_counter.items(), key=lambda x: x[1], reverse=True))
            }
        finally:
            session.close()

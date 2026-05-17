from datetime import datetime
from typing import Optional
from sqlalchemy import func

from models.review import Review
from models.manga import Manga
from database import get_session


class ReviewService:

    def add(self, manga_id: int, collection_id: int, user_id: int,
            rating: int, review_text: str = None, tags: list = None):
        import json
        if not (1 <= rating <= 10):
            raise ValueError("Rating must be between 1 and 10.")
        session = get_session()
        try:
            existing = session.query(Review).filter(
                Review.collection_id == collection_id
            ).first()
            if existing:
                return existing
            review = Review(
                user_id=user_id, manga_id=manga_id,
                collection_id=collection_id, rating=rating,
                review_text=review_text,
                tags=json.dumps(tags or [], ensure_ascii=False)
            )
            session.add(review)
            session.commit()
            session.refresh(review)
            return review
        finally:
            session.close()

    def get_by_manga(self, manga_id: int, user_id: int = None):
        session = get_session()
        try:
            q = session.query(Review).filter(Review.manga_id == manga_id)
            if user_id is not None:
                q = q.filter(Review.user_id == user_id)
            return q.first()
        finally:
            session.close()

    def update(self, review_id: int, rating: int = None, review_text: str = None, tags: list = None):
        import json
        session = get_session()
        try:
            review = session.query(Review).filter(Review.id == review_id).first()
            if not review:
                return None
            if rating is not None:
                review.rating = rating
            if review_text is not None:
                review.review_text = review_text
            if tags is not None:
                review.tags = json.dumps(tags, ensure_ascii=False)
            review.updated_at = datetime.now()
            session.commit()
            return review
        finally:
            session.close()

    def delete(self, review_id: int) -> bool:
        session = get_session()
        try:
            review = session.query(Review).filter(Review.id == review_id).first()
            if not review:
                return False
            session.delete(review)
            session.commit()
            return True
        finally:
            session.close()

    def get_average_rating(self, user_id: int = None) -> Optional[float]:
        session = get_session()
        try:
            q = session.query(func.avg(Review.rating))
            if user_id is not None:
                q = q.filter(Review.user_id == user_id)
            result = q.filter(Review.rating != None).scalar()
            return round(float(result), 1) if result else None
        finally:
            session.close()

    def get_last_review_data(self, user_id: int) -> Optional[dict]:
        session = get_session()
        try:
            result = session.query(Review, Manga).join(
                Manga, Review.manga_id == Manga.id
            ).filter(Review.user_id == user_id).order_by(
                Review.updated_at.desc()
            ).first()
            if result:
                import json
                r, m = result
                try:
                    tags = json.loads(r.tags) if r.tags else []
                except Exception:
                    tags = []
                return {
                    "manga_id": r.manga_id,
                    "title": m.title or "—",
                    "cover_url": m.cover_url or "",
                    "rating": r.rating,
                    "review_text": r.review_text or "",
                    "tags": tags,
                }
            return None
        finally:
            session.close()
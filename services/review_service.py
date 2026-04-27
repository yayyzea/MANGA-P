from datetime import datetime
from typing import Optional

from models.review import Review
from database import get_session


class ReviewService:
    """Manages user reviews and ratings."""

    # ── Create ────────────────────────────────────────────────────────────────

    def add(
        self,
        manga_id: int,
        collection_id: int,
        rating: int,
        review_text: str = None,
    ) -> Optional[Review]:
        """Add a review. One review per collection entry."""
        if not (1 <= rating <= 10):
            raise ValueError("Rating must be between 1 and 10.")

        session = get_session()
        try:
            existing = (
                session.query(Review)
                .filter(Review.collection_id == collection_id)
                .first()
            )
            if existing:
                return existing  # Already has a review — use update instead

            review = Review(
                manga_id=manga_id,
                collection_id=collection_id,
                rating=rating,
                review_text=review_text,
            )
            session.add(review)
            session.commit()
            session.refresh(review)
            return review
        finally:
            session.close()

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_by_collection(self, collection_id: int) -> Optional[Review]:
        """Get review for a specific collection entry."""
        session = get_session()
        try:
            return (
                session.query(Review)
                .filter(Review.collection_id == collection_id)
                .first()
            )
        finally:
            session.close()

    def get_by_manga(self, manga_id: int) -> Optional[Review]:
        """Get review for a manga."""
        session = get_session()
        try:
            return (
                session.query(Review)
                .filter(Review.manga_id == manga_id)
                .first()
            )
        finally:
            session.close()

    def get_all(self) -> list[Review]:
        """Get all reviews ordered by most recent."""
        session = get_session()
        try:
            return (
                session.query(Review)
                .order_by(Review.updated_at.desc())
                .all()
            )
        finally:
            session.close()

    # ── Update ────────────────────────────────────────────────────────────────

    def update(
        self,
        review_id: int,
        rating: int = None,
        review_text: str = None,
    ) -> Optional[Review]:
        """Update an existing review."""
        session = get_session()
        try:
            review = session.query(Review).filter(Review.id == review_id).first()
            if not review:
                return None

            if rating is not None:
                if not (1 <= rating <= 10):
                    raise ValueError("Rating must be between 1 and 10.")
                review.rating = rating
            if review_text is not None:
                review.review_text = review_text

            review.updated_at = datetime.now()
            session.commit()
            session.refresh(review)
            return review
        finally:
            session.close()

    # ── Delete ────────────────────────────────────────────────────────────────

    def delete(self, review_id: int) -> bool:
        """Delete a review."""
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

    # ── Stats ─────────────────────────────────────────────────────────────────

    def get_average_rating(self) -> Optional[float]:
        """Calculate average rating across all reviews."""
        session = get_session()
        try:
            reviews = session.query(Review).all()
            if not reviews:
                return None
            return round(sum(r.rating for r in reviews) / len(reviews), 1)
        finally:
            session.close()

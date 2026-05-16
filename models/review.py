from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, CheckConstraint
import json
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 10", name="check_rating_range"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    manga_id = Column(Integer, ForeignKey("manga.id"), nullable=False)
    collection_id = Column(Integer, ForeignKey("user_collection.id"), nullable=True)
    rating = Column(Integer, nullable=False)
    review_text = Column(Text, nullable=True)
    tags = Column(Text, nullable=True, default="[]")   # JSON list of tag strings
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="reviews")
    manga = relationship("Manga", back_populates="reviews")
    collection = relationship("UserCollection", back_populates="reviews")

    def get_tags(self) -> list:
        """Kembalikan tags sebagai list Python."""
        try:
            return json.loads(self.tags or "[]")
        except Exception:
            return []

    def set_tags(self, tags: list):
        """Simpan tags dari list Python ke JSON string."""
        self.tags = json.dumps(tags, ensure_ascii=False)

    def __repr__(self):
        return f"<Review(id={self.id}, manga_id={self.manga_id}, rating={self.rating})>"

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 10", name="check_rating_range"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    manga_id = Column(Integer, ForeignKey("manga.id"), nullable=False)
    collection_id = Column(Integer, ForeignKey("user_collection.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    review_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    manga = relationship("Manga", back_populates="reviews")
    collection = relationship("UserCollection", back_populates="reviews")

    def __repr__(self):
        return f"<Review(id={self.id}, manga_id={self.manga_id}, rating={self.rating})>"

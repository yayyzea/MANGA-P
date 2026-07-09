from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# Konstanta status koleksi terpusat di modul filters.py (root project).
from filters import COLLECTION_STATUS_OPTIONS


class UserCollection(Base):
    __tablename__ = "user_collection"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    manga_id = Column(Integer, ForeignKey("manga.id"), nullable=False)
    status = Column(String(20), nullable=False, default="Plan to Read")
    current_chapter = Column(Integer, default=0)
    score = Column(Integer, nullable=True)
    start_date = Column(Date, nullable=True)
    finish_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="collections")
    manga = relationship("Manga", back_populates="collections")
    reviews = relationship(
        "Review",
        back_populates="collection",
        cascade="all, delete-orphan"
    )

    STATUS_OPTIONS = COLLECTION_STATUS_OPTIONS

    def __repr__(self):
        return f"<UserCollection(id={self.id}, manga_id={self.manga_id}, status='{self.status}')>"

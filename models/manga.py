from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Manga(Base):
    __tablename__ = "manga"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mal_id = Column(Integer, unique=True, nullable=True)
    title = Column(String(500), nullable=False)
    title_english = Column(String(500), nullable=True)
    title_en = Column(String(255), nullable=True)  # backward compat
    synopsis = Column(Text, nullable=True)
    cover_url = Column(String(1000), nullable=True)
    authors = Column(String(500), nullable=True)
    genres = Column(String(500), nullable=True)
    status = Column(String(50), nullable=True)
    score = Column(Float, nullable=True)
    chapters = Column(Integer, nullable=True)
    year = Column(Integer, nullable=True)
    is_manual = Column(Boolean, default=False)
    fetched_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    collections = relationship(
        "UserCollection",
        back_populates="manga",
        cascade="all, delete-orphan"
    )
    reviews = relationship(
        "Review",
        back_populates="manga",
        cascade="all, delete-orphan"
    )

    def genres_list(self):
        if not self.genres:
            return []
        return [g.strip() for g in self.genres.split(",")]

    def authors_list(self):
        if not self.authors:
            return []
        # Format dari MAL: "Lastname, Firstname, Lastname2, Firstname2"
        # Setiap 2 elemen = 1 author (nama belakang + nama depan)
        parts = [a.strip() for a in self.authors.split(",")]
        if len(parts) % 2 == 0:
            return [f"{parts[i]} {parts[i+1]}" for i in range(0, len(parts), 2)]
        # Fallback: kalau jumlah ganjil, kembalikan apa adanya
        return parts

    def __repr__(self):
        return f"<Manga(id={self.id}, title='{self.title}')>"
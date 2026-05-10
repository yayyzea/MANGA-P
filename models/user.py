from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from database import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    username   = Column(String(100), unique=True, nullable=False)
    email      = Column(String(255), unique=True, nullable=False)
    password   = Column(String(255), nullable=False)
    name       = Column(String(255), nullable=True)
    bio        = Column(Text, nullable=True)
    avatar_path= Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    collections = relationship("UserCollection", back_populates="user")
    reviews = relationship("Review", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

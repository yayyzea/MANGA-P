from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "manga_p.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    """Create all tables if they don't exist."""
    from models.manga import Manga
    from models.user_collection import UserCollection
    from models.review import Review
    Base.metadata.create_all(bind=engine)
    print(f"[DB] Database initialized at: {DB_PATH}")


def get_session():
    """Return a new database session."""
    return SessionLocal()

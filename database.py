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
    from models.user import User
    from models.manga import Manga
    from models.user_collection import UserCollection
    from models.review import Review
    Base.metadata.create_all(bind=engine)
    _migrate(engine)
    print(f"[DB] Database initialized at: {DB_PATH}")


def _migrate(eng):
    """Jalankan migrasi kolom baru secara otomatis (idempotent)."""
    from sqlalchemy import text, inspect
    with eng.connect() as conn:
        inspector = inspect(eng)

       
        review_cols = [c["name"] for c in inspector.get_columns("reviews")]
        if "tags" not in review_cols:
            conn.execute(text("ALTER TABLE reviews ADD COLUMN tags TEXT DEFAULT '[]'"))
            conn.commit()
            print("[DB] Migrasi: kolom 'tags' ditambahkan ke tabel reviews.")


def get_session():
    return SessionLocal()

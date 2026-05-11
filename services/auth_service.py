from database import get_session
from models.user import User
import hashlib

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

class AuthService:
    def login(self, email_or_username: str, password: str):
        if not email_or_username or not password:
            return None
        session = get_session()
        try:
            user = session.query(User).filter(
                (User.username == email_or_username) |
                (User.email == email_or_username)
            ).first()
            if not user or user.password != _hash(password):
                return None
            return {"id": user.id, "username": user.username, "email": user.email}
        finally:
            session.close()

    def register(self, username: str, email: str, password: str):
        if not username or not email or not password:
            return False, "Semua field wajib diisi"
        session = get_session()
        try:
            existing = session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            if existing:
                return False, "Username atau email sudah digunakan"
            new_user = User(username=username, email=email, password=_hash(password))
            session.add(new_user)
            session.commit()
            return True, None
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

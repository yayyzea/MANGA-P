from database import get_session
from models.user import User
import hashlib


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class AuthService:

    def login(self, email_or_username: str, password: str):
        """
        Returns user dict on success, None on failure.
        Accepts either username or email as the first argument.
        """
        if not email_or_username or not password:
            return None
        session = get_session()
        try:
            user = session.query(User).filter(
                (User.username == email_or_username) |
                (User.email    == email_or_username)
            ).first()
            if not user or user.password != _hash(password):
                return None
            return {"id": user.id, "username": user.username, "email": user.email}
        finally:
            session.close()

    def register(self, username: str, email: str, password: str):
        """
        Returns (True, None) on success.
        Returns (False, error_message) on failure.
        Checks username and email uniqueness separately for a clear error message.
        """
        if not username or not email or not password:
            return False, "All fields are required."

        username = username.strip()
        email    = email.strip()

        session = get_session()
        try:
            # Check username uniqueness
            if session.query(User).filter(User.username == username).first():
                return False, "Username is already taken. Please choose another."

            # Check email uniqueness
            if session.query(User).filter(User.email == email).first():
                return False, "An account with this email already exists."

            new_user = User(username=username, email=email, password=_hash(password))
            session.add(new_user)
            session.commit()
            return True, None

        except Exception as e:
            session.rollback()
            return False, f"Registration failed: {e}"
        finally:
            session.close()

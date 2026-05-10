from database import get_session
from models.user import User
import hashlib

class UserService:
    def get_profile(self, user_id: int):
        session = get_session()
        try:
            return session.query(User).filter(User.id == user_id).first()
        finally:
            session.close()

    def update_profile(self, user_id: int, name=None, email=None,
                       password=None, bio=None, avatar_path=None):
        session = get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            if name: user.name = name
            if email: user.email = email
            if bio: user.bio = bio
            if avatar_path: user.avatar_path = avatar_path
            if password:
                user.password = hashlib.sha256(password.encode()).hexdigest()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()

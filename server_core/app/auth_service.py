"""Password hashing and short-lived signed access tokens."""
from datetime import datetime, timedelta, timezone
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models import User

password_hash = PasswordHasher()


class AuthService:
    def hash_password(self, password: str) -> str:
        return password_hash.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return password_hash.verify(hashed_password, plain_password)
        except (VerifyMismatchError, VerificationError, ValueError):
            return False

    def create_user(self, db: Session, email: str, password: str) -> User:
        email = email.strip().lower()
        if db.query(User).filter(User.email == email).first():
            raise ValueError("Email already registered.")
        user = User(email=email, password_hash=self.hash_password(password))
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
        except IntegrityError:
            db.rollback()
            raise ValueError("Email already registered.") from None
        except Exception:
            db.rollback()
            raise
        return user

    def authenticate_user(self, db: Session, email: str, password: str):
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if not user or not user.is_active or not self.verify_password(password, user.password_hash):
            return None
        return user

    def create_access_token(self, subject: str) -> str:
        now = datetime.now(timezone.utc)
        return jwt.encode({"sub": subject, "iat": now, "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)}, SECRET_KEY, algorithm=ALGORITHM)

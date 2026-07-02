"""
auth.py — Password hashing, JWT creation/verification, and the
          get_current_user FastAPI dependency.
"""
import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

# ---------------------------------------------------------------------------
# Config — read from env, fall back to dev defaults (never hardcode in prod)
# ---------------------------------------------------------------------------

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production-please")
ALGORITHM  = "HS256"
TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 h

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db:    Session = Depends(get_db),
) -> User:
    """
    Validates the bearer token and returns the corresponding User row.
    Raises HTTP 401 for any auth failure.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = _decode_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user = db.get(User, int(user_id_str))
    if user is None:
        raise credentials_exc
    return user

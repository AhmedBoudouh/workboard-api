from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from datetime import datetime, timezone, timedelta
import jwt
from sqlalchemy import select
from config import settings
from database import Session
from models import UserDB

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_user(username: str, db: Session):
    user = db.scalar(select(UserDB).where(UserDB.username == username))
    return user


def authenticate_user(username, password, db: Session):
    user = get_user(username, db)
    if not user:
        return None
    correct_password = password_hash.verify(password, user.hashed_password)
    if not correct_password:
        return None

    return user


def create_token(username):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": username, "exp": expire}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return token

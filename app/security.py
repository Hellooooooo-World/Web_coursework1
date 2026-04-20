from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from starlette.requests import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
    )


def get_current_user(
    user_id: int | None,
    db: Session,
) -> User | None:
    if not user_id:
        return None
    return db.get(User, user_id)


def get_session_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    user_id = request.session.get("user_id")
    user = get_current_user(user_id=user_id, db=db)
    return user


def require_session_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    user = get_session_user(request=request, db=db)
    if not user:
        raise _unauthorized("Not authenticated")
    return user

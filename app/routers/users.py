from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserOut
from app.security import get_password_hash, require_session_user

# Hidden from Swagger/ReDoc, but still usable programmatically.
router = APIRouter(prefix="/users", tags=["users"], include_in_schema=False)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_session_user),
) -> User:
    user = User(username=payload.username, password_hash=get_password_hash(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username already exists.") from exc
    db.refresh(user)
    return user

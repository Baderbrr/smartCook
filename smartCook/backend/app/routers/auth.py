from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.i18n import Lang, get_lang, tr
from app.models import User
from app.schemas import Token, UserCreate, UserLogin, UserOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_for(user: User) -> Token:
    return Token(access_token=create_access_token(user.id), user=UserOut.model_validate(user))


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db), lang: Lang = Depends(get_lang)):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, tr("email_taken", lang))
    user = User(
        email=email,
        display_name=data.display_name.strip(),
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    return _token_for(user)


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db), lang: Lang = Depends(get_lang)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, tr("bad_credentials", lang))
    return _token_for(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user

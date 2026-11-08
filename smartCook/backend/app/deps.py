from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.i18n import Lang, get_lang, tr
from app.models import User
from app.security import decode_access_token

_bearer = HTTPBearer(auto_error=False)


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        return None
    return db.get(User, user_id)


def get_current_user(
    user: User | None = Depends(get_optional_user), lang: Lang = Depends(get_lang)
) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=tr("auth_required", lang),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

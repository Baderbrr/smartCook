from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.i18n import Lang, get_lang, tr
from app.models import Favorite, Recipe, User
from app.schemas import RecipeSummary
from app.services.serializers import recipe_summary

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("", response_model=list[RecipeSummary])
def list_favorites(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    lang: Lang = Depends(get_lang),
):
    favorites = db.scalars(
        select(Favorite).where(Favorite.user_id == user.id).order_by(Favorite.created_at.desc())
    ).all()
    ids = {f.recipe_id for f in favorites}
    return [recipe_summary(f.recipe, lang, ids) for f in favorites]


@router.put("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def add_favorite(
    recipe_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    lang: Lang = Depends(get_lang),
):
    if db.get(Recipe, recipe_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, tr("recipe_not_found", lang))
    # PUT is idempotent: adding an existing favorite is a no-op.
    if db.get(Favorite, (user.id, recipe_id)) is None:
        db.add(Favorite(user_id=user.id, recipe_id=recipe_id))
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(
    recipe_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    favorite = db.get(Favorite, (user.id, recipe_id))
    if favorite is not None:
        db.delete(favorite)
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

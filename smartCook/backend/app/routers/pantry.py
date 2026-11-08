from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.i18n import Lang, get_lang, tr
from app.models import Ingredient, PantryItem, User
from app.schemas import PantryItemCreate, PantryItemOut, PantryItemUpdate
from app.services.serializers import pantry_item_out
from app.utils import polish_sort_key

router = APIRouter(prefix="/pantry", tags=["pantry"])


def _get_own_item(db: Session, user: User, item_id: int, lang: Lang) -> PantryItem:
    item = db.get(PantryItem, item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, tr("pantry_item_not_found", lang))
    return item


@router.get("", response_model=list[PantryItemOut])
def list_pantry(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    lang: Lang = Depends(get_lang),
):
    items = db.scalars(select(PantryItem).where(PantryItem.user_id == user.id))
    out = [pantry_item_out(item, lang) for item in items]
    return sorted(out, key=lambda i: polish_sort_key(i.ingredient.name))


@router.post("", response_model=PantryItemOut, status_code=status.HTTP_201_CREATED)
def add_pantry_item(
    data: PantryItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    lang: Lang = Depends(get_lang),
):
    ingredient = db.get(Ingredient, data.ingredient_id)
    if ingredient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, tr("ingredient_not_found", lang))
    exists = db.scalar(
        select(PantryItem).where(
            PantryItem.user_id == user.id, PantryItem.ingredient_id == data.ingredient_id
        )
    )
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, tr("pantry_duplicate", lang))
    item = PantryItem(
        user_id=user.id,
        ingredient_id=ingredient.id,
        quantity=data.quantity,
        unit=data.unit or (ingredient.default_unit if data.quantity else None),
        expires_at=data.expires_at,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return pantry_item_out(item, lang)


@router.patch("/{item_id}", response_model=PantryItemOut)
def update_pantry_item(
    item_id: int,
    data: PantryItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    lang: Lang = Depends(get_lang),
):
    item = _get_own_item(db, user, item_id, lang)
    # exclude_unset lets the client clear a field by sending null explicitly.
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    return pantry_item_out(item, lang)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pantry_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    lang: Lang = Depends(get_lang),
):
    item = _get_own_item(db, user, item_id, lang)
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

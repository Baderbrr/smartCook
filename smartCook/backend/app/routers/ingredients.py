from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.i18n import Lang, get_lang
from app.models import Ingredient
from app.schemas import IngredientOut
from app.services.serializers import ingredient_out
from app.utils import polish_sort_key

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("", response_model=list[IngredientOut])
def list_ingredients(
    q: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
    lang: Lang = Depends(get_lang),
):
    stmt = select(Ingredient)
    if category:
        stmt = stmt.where(Ingredient.category == category)
    items = [ingredient_out(ing, lang) for ing in db.scalars(stmt)]
    # Text search is done in Python: SQLite's LOWER() ignores non-ASCII letters like "Ż".
    if q:
        needle = q.casefold().strip()
        items = [i for i in items if needle in i.name.casefold()]
    return sorted(items, key=lambda i: polish_sort_key(i.name))

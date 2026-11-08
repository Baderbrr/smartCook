from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.i18n import Lang, get_lang, tr
from app.models import Ingredient, PantryItem, Recipe, ShoppingListItem, User
from app.schemas import PantryItemOut, ShoppingItemCreate, ShoppingItemOut, ShoppingItemUpdate
from app.services.matching import required_ingredients
from app.services.serializers import pantry_item_out, shopping_item_out
from app.utils import polish_sort_key

router = APIRouter(prefix="/shopping-list", tags=["shopping-list"])


def _items(db: Session, user: User) -> list[ShoppingListItem]:
    return list(db.scalars(select(ShoppingListItem).where(ShoppingListItem.user_id == user.id)))


def _list_out(db: Session, user: User, lang: Lang) -> list[ShoppingItemOut]:
    out = [shopping_item_out(item, lang) for item in _items(db, user)]
    # Unchecked first, then alphabetically.
    return sorted(out, key=lambda i: (i.checked, polish_sort_key(i.ingredient.name)))


def _add_or_merge(
    db: Session,
    user: User,
    ingredient: Ingredient,
    quantity: float | None,
    unit: str | None,
    recipe_id: int | None = None,
) -> None:
    """Add an item, or merge it into an unchecked item for the same ingredient."""
    existing = db.scalar(
        select(ShoppingListItem).where(
            ShoppingListItem.user_id == user.id,
            ShoppingListItem.ingredient_id == ingredient.id,
            ShoppingListItem.checked.is_(False),
        )
    )
    if existing is None:
        db.add(
            ShoppingListItem(
                user_id=user.id,
                ingredient_id=ingredient.id,
                quantity=quantity,
                unit=unit,
                recipe_id=recipe_id,
            )
        )
    elif quantity is not None and existing.quantity is not None and existing.unit == unit:
        existing.quantity += quantity


@router.get("", response_model=list[ShoppingItemOut])
def list_items(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    lang: Lang = Depends(get_lang),
):
    return _list_out(db, user, lang)


@router.post("", response_model=list[ShoppingItemOut], status_code=status.HTTP_201_CREATED)
def add_item(
    data: ShoppingItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    lang: Lang = Depends(get_lang),
):
    ingredient = db.get(Ingredient, data.ingredient_id)
    if ingredient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, tr("ingredient_not_found", lang))
    unit = data.unit or (ingredient.default_unit if data.quantity else None)
    _add_or_merge(db, user, ingredient, data.quantity, unit)
    db.commit()
    return _list_out(db, user, lang)


@router.post("/from-recipe/{recipe_id}", response_model=list[ShoppingItemOut])
def add_missing_from_recipe(
    recipe_id: int,
    servings: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    lang: Lang = Depends(get_lang),
):
    """Put every required ingredient of the recipe that is not in the pantry on the list."""
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, tr("recipe_not_found", lang))
    scale = (servings / recipe.servings) if servings and servings > 0 else 1.0
    in_pantry = set(db.scalars(select(PantryItem.ingredient_id).where(PantryItem.user_id == user.id)))
    required_ids = {ing.id for ing in required_ingredients(recipe)}
    for ri in recipe.ingredients:
        if ri.ingredient_id in required_ids and ri.ingredient_id not in in_pantry:
            quantity = round(ri.quantity * scale, 2) if ri.quantity is not None else None
            _add_or_merge(db, user, ri.ingredient, quantity, ri.unit, recipe.id)
    db.commit()
    return _list_out(db, user, lang)


@router.post("/checked/to-pantry", response_model=list[PantryItemOut])
def move_checked_to_pantry(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    lang: Lang = Depends(get_lang),
):
    """Move bought (checked) items into the pantry, adding up quantities where units match."""
    pantry = {
        item.ingredient_id: item
        for item in db.scalars(select(PantryItem).where(PantryItem.user_id == user.id))
    }
    for item in _items(db, user):
        if not item.checked:
            continue
        target = pantry.get(item.ingredient_id)
        if target is None:
            target = PantryItem(
                user_id=user.id,
                ingredient_id=item.ingredient_id,
                quantity=item.quantity,
                unit=item.unit,
            )
            db.add(target)
            pantry[item.ingredient_id] = target
        elif item.quantity is not None and target.quantity is not None and target.unit == item.unit:
            target.quantity += item.quantity
        db.delete(item)
    db.commit()
    out = [pantry_item_out(p, lang) for p in pantry.values()]
    return sorted(out, key=lambda i: polish_sort_key(i.ingredient.name))


@router.delete("/checked", status_code=status.HTTP_204_NO_CONTENT)
def clear_checked(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    for item in _items(db, user):
        if item.checked:
            db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _get_own_item(db: Session, user: User, item_id: int, lang: Lang) -> ShoppingListItem:
    item = db.get(ShoppingListItem, item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, tr("shopping_item_not_found", lang))
    return item


@router.patch("/{item_id}", response_model=ShoppingItemOut)
def update_item(
    item_id: int,
    data: ShoppingItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    lang: Lang = Depends(get_lang),
):
    item = _get_own_item(db, user, item_id, lang)
    for key, value in data.model_dump(exclude_unset=True).items():
        if key == "checked" and value is None:
            continue
        setattr(item, key, value)
    db.commit()
    return shopping_item_out(item, lang)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    lang: Lang = Depends(get_lang),
):
    item = _get_own_item(db, user, item_id, lang)
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

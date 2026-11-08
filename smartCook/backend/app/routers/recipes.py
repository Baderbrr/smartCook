from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user, get_optional_user
from app.i18n import Lang, get_lang, tr
from app.models import Favorite, PantryItem, Recipe, Tag, User
from app.schemas import (
    CookResult,
    RecipeDetail,
    RecipeMeta,
    RecipeSuggestion,
    RecipeSummary,
)
from app.services.matching import match_recipe, pantry_sets, rank_recipes
from app.services.serializers import (
    ingredient_out,
    match_info,
    recipe_detail,
    recipe_summary,
)
from app.utils import polish_sort_key

router = APIRouter(prefix="/recipes", tags=["recipes"])

DIFFICULTIES = ["easy", "medium", "hard"]


class RecipeFilters:
    """Query parameters shared by the catalogue and the suggestions endpoints."""

    def __init__(
        self,
        q: str | None = None,
        category: str | None = None,
        tag: list[str] = Query(default=[]),
        difficulty: str | None = None,
        max_time: int | None = Query(default=None, gt=0),
    ):
        self.q = q
        self.category = category
        self.tags = tag
        self.difficulty = difficulty
        self.max_time = max_time

    def load(self, db: Session, lang: Lang) -> list[Recipe]:
        stmt = select(Recipe)
        if self.category:
            stmt = stmt.where(Recipe.category == self.category)
        if self.difficulty:
            stmt = stmt.where(Recipe.difficulty == self.difficulty)
        if self.max_time:
            stmt = stmt.where(Recipe.prep_time_minutes <= self.max_time)
        for code in self.tags:
            stmt = stmt.where(Recipe.tags.any(Tag.code == code))
        recipes = list(db.scalars(stmt))
        # Text search is done in Python: SQLite's LOWER() ignores non-ASCII letters like "Ż".
        if self.q:
            needle = self.q.casefold().strip()
            recipes = [r for r in recipes if needle in r.title(lang).casefold()]
        return recipes


def favorite_ids(db: Session, user: User | None) -> set[int]:
    if user is None:
        return set()
    return set(db.scalars(select(Favorite.recipe_id).where(Favorite.user_id == user.id)))


def user_pantry(db: Session, user: User) -> list[PantryItem]:
    return list(db.scalars(select(PantryItem).where(PantryItem.user_id == user.id)))


def _get_recipe(db: Session, recipe_id: int, lang: Lang) -> Recipe:
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, tr("recipe_not_found", lang))
    return recipe


@router.get("/meta", response_model=RecipeMeta)
def recipes_meta(db: Session = Depends(get_db)):
    return RecipeMeta(
        categories=sorted(set(db.scalars(select(Recipe.category)))),
        tags=sorted(db.scalars(select(Tag.code))),
        difficulties=DIFFICULTIES,
    )


@router.get("", response_model=list[RecipeSummary])
def list_recipes(
    filters: RecipeFilters = Depends(),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
    lang: Lang = Depends(get_lang),
):
    favs = favorite_ids(db, user)
    out = [recipe_summary(r, lang, favs) for r in filters.load(db, lang)]
    return sorted(out, key=lambda r: polish_sort_key(r.title))


@router.get("/suggestions", response_model=list[RecipeSuggestion])
def suggest_recipes(
    filters: RecipeFilters = Depends(),
    min_match: int = Query(default=0, ge=0, le=100, description="Minimum match in percent"),
    max_missing: int | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    lang: Lang = Depends(get_lang),
):
    available, expiring = pantry_sets(
        user_pantry(db, user), date.today(), settings.expiring_within_days
    )
    matches = rank_recipes(
        filters.load(db, lang),
        available,
        expiring,
        min_ratio=min_match / 100,
        max_missing=max_missing,
    )
    favs = favorite_ids(db, user)
    return [
        RecipeSuggestion(
            **recipe_summary(m.recipe, lang, favs).model_dump(),
            match=match_info(m, lang),
        )
        for m in matches
    ]


@router.get("/{recipe_id}", response_model=RecipeDetail)
def get_recipe(
    recipe_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
    lang: Lang = Depends(get_lang),
):
    recipe = _get_recipe(db, recipe_id, lang)
    if user is None:
        return recipe_detail(recipe, lang, set(), None, None)
    available, expiring = pantry_sets(
        user_pantry(db, user), date.today(), settings.expiring_within_days
    )
    match = match_recipe(recipe, available, expiring)
    return recipe_detail(recipe, lang, favorite_ids(db, user), available, match)


@router.post("/{recipe_id}/cook", response_model=CookResult)
def cook_recipe(
    recipe_id: int,
    servings: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    lang: Lang = Depends(get_lang),
):
    """Subtract the recipe's ingredients from the pantry after cooking it.

    Only items whose quantity is known and whose unit matches the recipe's unit are
    reduced; an item that drops to zero is removed. Everything else is left as is,
    because we cannot reliably convert between e.g. "pcs" and "g".
    """
    recipe = _get_recipe(db, recipe_id, lang)
    scale = (servings / recipe.servings) if servings else 1.0
    pantry = {item.ingredient_id: item for item in user_pantry(db, user)}
    updated, removed = [], []
    for ri in recipe.ingredients:
        item = pantry.get(ri.ingredient_id)
        if item is None or ri.ingredient.is_staple:
            continue
        if item.quantity is None or ri.quantity is None or item.unit != ri.unit:
            continue
        remaining = item.quantity - ri.quantity * scale
        if remaining <= 1e-9:
            db.delete(item)
            removed.append(ingredient_out(ri.ingredient, lang))
        else:
            item.quantity = round(remaining, 3)
            updated.append(ingredient_out(ri.ingredient, lang))
    db.commit()
    return CookResult(updated=updated, removed=removed)

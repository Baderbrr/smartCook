"""Turn ORM objects into localized API schemas."""

from app.i18n import Lang
from app.models import Ingredient, PantryItem, Recipe, ShoppingListItem
from app.schemas import (
    IngredientOut,
    MatchInfo,
    PantryItemOut,
    RecipeDetail,
    RecipeIngredientOut,
    RecipeSummary,
    ShoppingItemOut,
)
from app.services.matching import RecipeMatch


def ingredient_out(ing: Ingredient, lang: Lang) -> IngredientOut:
    return IngredientOut(
        id=ing.id,
        name=ing.name(lang),
        category=ing.category,
        default_unit=ing.default_unit,
        is_staple=ing.is_staple,
    )


def pantry_item_out(item: PantryItem, lang: Lang) -> PantryItemOut:
    return PantryItemOut(
        id=item.id,
        ingredient=ingredient_out(item.ingredient, lang),
        quantity=item.quantity,
        unit=item.unit,
        expires_at=item.expires_at,
        added_at=item.added_at,
    )


def shopping_item_out(item: ShoppingListItem, lang: Lang) -> ShoppingItemOut:
    return ShoppingItemOut(
        id=item.id,
        ingredient=ingredient_out(item.ingredient, lang),
        quantity=item.quantity,
        unit=item.unit,
        checked=item.checked,
        recipe_id=item.recipe_id,
        recipe_title=item.recipe.title(lang) if item.recipe else None,
    )


def _summary_fields(recipe: Recipe, lang: Lang, favorite_ids: set[int]) -> dict:
    return dict(
        id=recipe.id,
        title=recipe.title(lang),
        description=recipe.description(lang),
        prep_time_minutes=recipe.prep_time_minutes,
        servings=recipe.servings,
        difficulty=recipe.difficulty,
        category=recipe.category,
        image_url=recipe.image_url,
        tags=sorted(tag.code for tag in recipe.tags),
        is_favorite=recipe.id in favorite_ids,
    )


def recipe_summary(recipe: Recipe, lang: Lang, favorite_ids: set[int]) -> RecipeSummary:
    return RecipeSummary(**_summary_fields(recipe, lang, favorite_ids))


def match_info(m: RecipeMatch, lang: Lang) -> MatchInfo:
    return MatchInfo(
        match_percent=m.percent,
        matched_count=m.matched_count,
        required_count=m.required_count,
        missing=[ingredient_out(i, lang) for i in m.missing],
        expiring_used=[ingredient_out(i, lang) for i in m.expiring_used],
    )


def recipe_detail(
    recipe: Recipe,
    lang: Lang,
    favorite_ids: set[int],
    available_ids: set[int] | None,
    match: RecipeMatch | None,
) -> RecipeDetail:
    ingredients = [
        RecipeIngredientOut(
            ingredient=ingredient_out(ri.ingredient, lang),
            quantity=ri.quantity,
            unit=ri.unit,
            optional=ri.optional,
            available=None
            if available_ids is None
            else ri.ingredient.is_staple or ri.ingredient.id in available_ids,
        )
        for ri in sorted(recipe.ingredients, key=lambda ri: (ri.optional, ri.ingredient.is_staple, ri.id))
    ]
    return RecipeDetail(
        **_summary_fields(recipe, lang, favorite_ids),
        steps=recipe.steps(lang),
        ingredients=ingredients,
        match=match_info(m=match, lang=lang) if match else None,
    )

"""Recipe matching based on ingredient availability.

For every recipe we look only at its *required* ingredients: optional ingredients and
staples (salt, pepper, oil, water...) never block a recipe. The match ratio is

    match = |required ∩ pantry| / |required|

Recipes are ranked lexicographically by:
    1. higher match ratio,
    2. fewer missing ingredients (matters when ratios tie, e.g. 2/4 vs 4/8),
    3. more pantry ingredients that are about to expire (reduces food waste),
    4. shorter preparation time.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, timedelta

from app.models import Ingredient, PantryItem, Recipe


@dataclass
class RecipeMatch:
    recipe: Recipe
    required_count: int
    matched_count: int
    missing: list[Ingredient] = field(default_factory=list)
    expiring_used: list[Ingredient] = field(default_factory=list)

    @property
    def ratio(self) -> float:
        if self.required_count == 0:
            return 1.0
        return self.matched_count / self.required_count

    @property
    def percent(self) -> int:
        return round(self.ratio * 100)


def required_ingredients(recipe: Recipe) -> list[Ingredient]:
    return [
        ri.ingredient
        for ri in recipe.ingredients
        if not ri.optional and not ri.ingredient.is_staple
    ]


def pantry_sets(
    items: Iterable[PantryItem], today: date, expiring_within_days: int
) -> tuple[set[int], set[int]]:
    """Return (available ingredient ids, ids of ingredients expiring within the window)."""
    items = list(items)
    limit = today + timedelta(days=expiring_within_days)
    available = {item.ingredient_id for item in items}
    expiring = {
        item.ingredient_id
        for item in items
        if item.expires_at is not None and item.expires_at <= limit
    }
    return available, expiring


def match_recipe(
    recipe: Recipe, available_ids: set[int], expiring_ids: set[int] = frozenset()
) -> RecipeMatch:
    required = required_ingredients(recipe)
    missing = [ing for ing in required if ing.id not in available_ids]
    # Optional ingredients count here too: using them up is still worth rewarding.
    expiring_used = [ri.ingredient for ri in recipe.ingredients if ri.ingredient.id in expiring_ids]
    return RecipeMatch(
        recipe=recipe,
        required_count=len(required),
        matched_count=len(required) - len(missing),
        missing=missing,
        expiring_used=expiring_used,
    )


def _rank_key(m: RecipeMatch) -> tuple:
    return (-m.ratio, len(m.missing), -len(m.expiring_used), m.recipe.prep_time_minutes, m.recipe.id)


def rank_recipes(
    recipes: Iterable[Recipe],
    available_ids: set[int],
    expiring_ids: set[int] = frozenset(),
    *,
    min_ratio: float = 0.0,
    max_missing: int | None = None,
) -> list[RecipeMatch]:
    """Match every recipe against the pantry, drop the ones that don't qualify, and sort."""
    results = []
    for recipe in recipes:
        m = match_recipe(recipe, available_ids, expiring_ids)
        # A recipe sharing nothing with the pantry is not a suggestion.
        if m.required_count > 0 and m.matched_count == 0:
            continue
        if m.ratio < min_ratio:
            continue
        if max_missing is not None and len(m.missing) > max_missing:
            continue
        results.append(m)
    results.sort(key=_rank_key)
    return results

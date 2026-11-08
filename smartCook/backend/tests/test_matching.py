"""Unit tests of the matching algorithm on in-memory (unsaved) ORM objects."""

from datetime import date, timedelta

from app.models import Ingredient, PantryItem, Recipe, RecipeIngredient
from app.services.matching import match_recipe, pantry_sets, rank_recipes

EGGS = Ingredient(id=1, name_pl="jajka", name_en="eggs", is_staple=False)
MILK = Ingredient(id=2, name_pl="mleko", name_en="milk", is_staple=False)
FLOUR = Ingredient(id=3, name_pl="mąka", name_en="flour", is_staple=False)
CHEESE = Ingredient(id=4, name_pl="ser", name_en="cheese", is_staple=False)
SALT = Ingredient(id=5, name_pl="sól", name_en="salt", is_staple=True)


def make_recipe(recipe_id, required, optional=(), time=30):
    recipe = Recipe(id=recipe_id, prep_time_minutes=time)
    for ing in required:
        recipe.ingredients.append(RecipeIngredient(ingredient=ing, optional=False))
    for ing in optional:
        recipe.ingredients.append(RecipeIngredient(ingredient=ing, optional=True))
    return recipe


def test_full_match():
    recipe = make_recipe(1, [EGGS, MILK])
    m = match_recipe(recipe, {1, 2})
    assert m.percent == 100
    assert m.missing == []


def test_partial_match_lists_missing():
    recipe = make_recipe(1, [EGGS, MILK, FLOUR])
    m = match_recipe(recipe, {1})
    assert (m.matched_count, m.required_count) == (1, 3)
    assert m.percent == 33
    assert m.missing == [MILK, FLOUR]


def test_staples_and_optional_are_ignored():
    recipe = make_recipe(1, [EGGS, SALT], optional=[CHEESE])
    m = match_recipe(recipe, {1})
    assert m.required_count == 1
    assert m.percent == 100


def test_recipe_with_only_staples_is_always_available():
    recipe = make_recipe(1, [SALT])
    assert match_recipe(recipe, set()).ratio == 1.0


def test_ranking_order():
    full = make_recipe(1, [EGGS, MILK])
    half_small = make_recipe(2, [EGGS, FLOUR])  # 1/2 missing 1
    half_big = make_recipe(3, [EGGS, MILK, FLOUR, CHEESE])  # 2/4 missing 2
    ranked = rank_recipes([half_big, half_small, full], {1, 2})
    assert [m.recipe.id for m in ranked] == [1, 2, 3]


def test_ranking_prefers_expiring_then_time():
    slow_expiring = make_recipe(1, [EGGS], time=60)
    fast = make_recipe(2, [MILK], time=10)
    slower = make_recipe(3, [MILK], time=20)
    ranked = rank_recipes([slower, fast, slow_expiring], {1, 2}, expiring_ids={1})
    assert [m.recipe.id for m in ranked] == [1, 2, 3]


def test_recipes_without_any_owned_ingredient_are_dropped():
    ranked = rank_recipes([make_recipe(1, [FLOUR, CHEESE])], {1})
    assert ranked == []


def test_filters_min_ratio_and_max_missing():
    recipes = [make_recipe(1, [EGGS]), make_recipe(2, [EGGS, MILK, FLOUR])]
    assert [m.recipe.id for m in rank_recipes(recipes, {1}, min_ratio=0.5)] == [1]
    assert [m.recipe.id for m in rank_recipes(recipes, {1}, max_missing=1)] == [1]
    assert len(rank_recipes(recipes, {1}, max_missing=2)) == 2


def test_pantry_sets_expiry_window():
    today = date(2026, 1, 10)
    items = [
        PantryItem(ingredient_id=1, expires_at=today + timedelta(days=2)),
        PantryItem(ingredient_id=2, expires_at=today + timedelta(days=10)),
        PantryItem(ingredient_id=3, expires_at=None),
        PantryItem(ingredient_id=4, expires_at=today - timedelta(days=1)),
    ]
    available, expiring = pantry_sets(items, today, expiring_within_days=3)
    assert available == {1, 2, 3, 4}
    assert expiring == {1, 4}

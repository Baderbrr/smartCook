"""Performance benchmark of the matching algorithm and the suggestions endpoint.

Usage (from the backend directory):
    python -m benchmarks.bench_matching
"""

import os
import random
import statistics
import time

os.environ.setdefault("DATABASE_URL", "sqlite://")

from app.models import Ingredient, Recipe, RecipeIngredient
from app.services.matching import rank_recipes

SIZES = [100, 1_000, 10_000, 50_000]
INGREDIENT_POOL = 500
PANTRY_SIZE = 20
RUNS = 5


def synthetic_recipes(count: int, rng: random.Random) -> list[Recipe]:
    ingredients = [
        Ingredient(id=i, name_pl=f"s{i}", name_en=f"i{i}", is_staple=i < 10)
        for i in range(INGREDIENT_POOL)
    ]
    recipes = []
    for rid in range(count):
        recipe = Recipe(id=rid, prep_time_minutes=rng.randint(5, 120))
        for ing in rng.sample(ingredients, rng.randint(5, 15)):
            recipe.ingredients.append(RecipeIngredient(ingredient=ing, optional=rng.random() < 0.15))
        recipes.append(recipe)
    return recipes


def bench_algorithm() -> None:
    rng = random.Random(42)
    print(f"{'recipes':>8} | {'ingredient links':>16} | {'median ms':>9} | {'results':>7}")
    for size in SIZES:
        recipes = synthetic_recipes(size, rng)
        links = sum(len(r.ingredients) for r in recipes)
        pantry = set(rng.sample(range(10, INGREDIENT_POOL), PANTRY_SIZE))
        expiring = set(list(pantry)[:3])
        times = []
        for _ in range(RUNS):
            start = time.perf_counter()
            result = rank_recipes(recipes, pantry, expiring)
            times.append((time.perf_counter() - start) * 1000)
        print(f"{size:>8} | {links:>16} | {statistics.median(times):>9.2f} | {len(result):>7}")


def bench_endpoint(requests: int = 200) -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        token = client.post(
            "/api/auth/login", json={"email": "demo@smartcook.pl", "password": "demo1234"}
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        client.get("/api/recipes/suggestions", headers=headers)  # warm-up
        times = []
        for _ in range(requests):
            start = time.perf_counter()
            res = client.get("/api/recipes/suggestions", headers=headers)
            times.append((time.perf_counter() - start) * 1000)
            assert res.status_code == 200
        times.sort()
        p95 = times[int(len(times) * 0.95) - 1]
        print(
            f"GET /api/recipes/suggestions x{requests}: "
            f"median {statistics.median(times):.2f} ms, p95 {p95:.2f} ms, max {times[-1]:.2f} ms"
        )


if __name__ == "__main__":
    bench_algorithm()
    bench_endpoint()

"""Seed the database with ingredients, recipes and a demo account.

Usage:
    python -m app.seed          # seed only if the database is empty
    python -m app.seed --reset  # drop all tables and seed from scratch
"""

import argparse
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import Ingredient, PantryItem, Recipe, RecipeIngredient, Tag, User
from app.security import hash_password
from app.seed_data import DEMO_PANTRY, DEMO_USER, INGREDIENTS, RECIPES


def seed_database(db: Session) -> bool:
    """Insert initial data if there are no recipes yet. Returns True if anything was inserted."""
    if db.scalar(select(Recipe.id).limit(1)) is not None:
        return False

    ingredients: dict[str, Ingredient] = {}
    for name_pl, name_en, category, unit, staple in INGREDIENTS:
        ing = Ingredient(
            name_pl=name_pl, name_en=name_en, category=category, default_unit=unit, is_staple=staple
        )
        db.add(ing)
        ingredients[name_pl] = ing

    tags: dict[str, Tag] = {}
    for data in RECIPES:
        recipe = Recipe(
            title_pl=data["title"][0],
            title_en=data["title"][1],
            description_pl=data["description"][0],
            description_en=data["description"][1],
            instructions_pl="\n".join(data["steps_pl"]),
            instructions_en="\n".join(data["steps_en"]),
            prep_time_minutes=data["time"],
            servings=data["servings"],
            difficulty=data["difficulty"],
            category=data["category"],
        )
        for code in data["tags"]:
            recipe.tags.append(tags.setdefault(code, Tag(code=code)))
        for row in data["ingredients"]:
            name, quantity, unit = row[:3]
            optional = len(row) > 3 and row[3]
            if name not in ingredients:
                raise ValueError(f"Unknown ingredient {name!r} in recipe {data['title'][1]!r}")
            recipe.ingredients.append(
                RecipeIngredient(
                    ingredient=ingredients[name], quantity=quantity, unit=unit, optional=optional
                )
            )
        db.add(recipe)

    if db.scalar(select(User).where(User.email == DEMO_USER["email"])) is None:
        demo = User(
            email=DEMO_USER["email"],
            display_name=DEMO_USER["display_name"],
            hashed_password=hash_password(DEMO_USER["password"]),
        )
        db.add(demo)
        today = date.today()
        for name, quantity, unit, days in DEMO_PANTRY:
            demo.pantry_items.append(
                PantryItem(
                    ingredient=ingredients[name],
                    quantity=quantity,
                    unit=unit,
                    expires_at=today + timedelta(days=days) if days is not None else None,
                )
            )

    db.commit()
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="drop all tables before seeding")
    args = parser.parse_args()

    if args.reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        inserted = seed_database(db)
    print("Database seeded." if inserted else "Database already contains data - nothing to do.")


if __name__ == "__main__":
    main()

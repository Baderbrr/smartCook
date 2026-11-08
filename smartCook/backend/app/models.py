from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Categories, tags, difficulty levels and units are stored as codes (e.g. "soup", "tbsp")
# and translated by the frontend. Free text (names, descriptions, steps) has _pl/_en columns.


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


recipe_tags = Table(
    "recipe_tags",
    Base.metadata,
    Column("recipe_id", ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    pantry_items: Mapped[list["PantryItem"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    shopping_items: Mapped[list["ShoppingListItem"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    favorites: Mapped[list["Favorite"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name_pl: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name_en: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[str] = mapped_column(String(50))
    default_unit: Mapped[str] = mapped_column(String(20))
    # Staples (salt, pepper, water...) are always treated as available.
    is_staple: Mapped[bool] = mapped_column(Boolean, default=False)

    def name(self, lang: str) -> str:
        return self.name_en if lang == "en" else self.name_pl


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title_pl: Mapped[str] = mapped_column(String(200))
    title_en: Mapped[str] = mapped_column(String(200))
    description_pl: Mapped[str] = mapped_column(Text)
    description_en: Mapped[str] = mapped_column(Text)
    # Preparation steps separated by newlines.
    instructions_pl: Mapped[str] = mapped_column(Text)
    instructions_en: Mapped[str] = mapped_column(Text)
    prep_time_minutes: Mapped[int] = mapped_column(Integer)
    servings: Mapped[int] = mapped_column(Integer)
    difficulty: Mapped[str] = mapped_column(String(10))  # easy | medium | hard
    category: Mapped[str] = mapped_column(String(50), index=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan", lazy="selectin"
    )
    tags: Mapped[list[Tag]] = relationship(secondary=recipe_tags, lazy="selectin")

    def title(self, lang: str) -> str:
        return self.title_en if lang == "en" else self.title_pl

    def description(self, lang: str) -> str:
        return self.description_en if lang == "en" else self.description_pl

    def steps(self, lang: str) -> list[str]:
        text = self.instructions_en if lang == "en" else self.instructions_pl
        return [line for line in text.splitlines() if line.strip()]


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    __table_args__ = (UniqueConstraint("recipe_id", "ingredient_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id", ondelete="RESTRICT"))
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    optional: Mapped[bool] = mapped_column(Boolean, default=False)

    recipe: Mapped[Recipe] = relationship(back_populates="ingredients")
    ingredient: Mapped[Ingredient] = relationship(lazy="joined")


class PantryItem(Base):
    __tablename__ = "pantry_items"
    __table_args__ = (UniqueConstraint("user_id", "ingredient_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id", ondelete="RESTRICT"))
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    expires_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="pantry_items")
    ingredient: Mapped[Ingredient] = relationship(lazy="joined")


class ShoppingListItem(Base):
    __tablename__ = "shopping_list_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id", ondelete="RESTRICT"))
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    checked: Mapped[bool] = mapped_column(Boolean, default=False)
    recipe_id: Mapped[int | None] = mapped_column(
        ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="shopping_items")
    ingredient: Mapped[Ingredient] = relationship(lazy="joined")
    recipe: Mapped[Recipe | None] = relationship(lazy="joined")


class Favorite(Base):
    __tablename__ = "favorites"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="favorites")
    recipe: Mapped[Recipe] = relationship()

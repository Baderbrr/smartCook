from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Auth ---


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=64)
    display_name: str = Field(min_length=1, max_length=100)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        # bcrypt only uses the first 72 bytes of the password.
        if len(value.encode("utf-8")) > 72:
            raise ValueError("password is too long")
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORMModel):
    id: int
    email: str
    display_name: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# --- Ingredients ---


class IngredientOut(BaseModel):
    id: int
    name: str
    category: str
    default_unit: str
    is_staple: bool


# --- Pantry ---


class PantryItemCreate(BaseModel):
    ingredient_id: int
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, max_length=20)
    expires_at: date | None = None


class PantryItemUpdate(BaseModel):
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, max_length=20)
    expires_at: date | None = None


class PantryItemOut(BaseModel):
    id: int
    ingredient: IngredientOut
    quantity: float | None
    unit: str | None
    expires_at: date | None
    added_at: datetime


# --- Recipes ---


class MatchInfo(BaseModel):
    match_percent: int
    matched_count: int
    required_count: int
    missing: list[IngredientOut]
    expiring_used: list[IngredientOut]


class RecipeSummary(BaseModel):
    id: int
    title: str
    description: str
    prep_time_minutes: int
    servings: int
    difficulty: str
    category: str
    image_url: str | None
    tags: list[str]
    is_favorite: bool = False


class RecipeSuggestion(RecipeSummary):
    match: MatchInfo


class RecipeIngredientOut(BaseModel):
    ingredient: IngredientOut
    quantity: float | None
    unit: str | None
    optional: bool
    # None for anonymous users, otherwise whether the user has it (staples always count).
    available: bool | None = None


class RecipeDetail(RecipeSummary):
    steps: list[str]
    ingredients: list[RecipeIngredientOut]
    match: MatchInfo | None = None


class RecipeMeta(BaseModel):
    categories: list[str]
    tags: list[str]
    difficulties: list[str]


class CookResult(BaseModel):
    updated: list[IngredientOut]
    removed: list[IngredientOut]


# --- Shopping list ---


class ShoppingItemCreate(BaseModel):
    ingredient_id: int
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, max_length=20)


class ShoppingItemUpdate(BaseModel):
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, max_length=20)
    checked: bool | None = None


class ShoppingItemOut(BaseModel):
    id: int
    ingredient: IngredientOut
    quantity: float | None
    unit: str | None
    checked: bool
    recipe_id: int | None
    recipe_title: str | None

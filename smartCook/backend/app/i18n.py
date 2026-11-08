from typing import Literal

from fastapi import Header

Lang = Literal["pl", "en"]
SUPPORTED_LANGS: tuple[Lang, ...] = ("pl", "en")
DEFAULT_LANG: Lang = "pl"

MESSAGES: dict[str, dict[Lang, str]] = {
    "auth_required": {"pl": "Wymagane zalogowanie", "en": "Login required"},
    "email_taken": {
        "pl": "Konto z tym adresem e-mail już istnieje",
        "en": "An account with this email already exists",
    },
    "bad_credentials": {
        "pl": "Nieprawidłowy e-mail lub hasło",
        "en": "Invalid email or password",
    },
    "ingredient_not_found": {"pl": "Nie znaleziono składnika", "en": "Ingredient not found"},
    "recipe_not_found": {"pl": "Nie znaleziono przepisu", "en": "Recipe not found"},
    "pantry_item_not_found": {
        "pl": "Nie znaleziono pozycji w spiżarni",
        "en": "Pantry item not found",
    },
    "pantry_duplicate": {
        "pl": "Ten składnik jest już w spiżarni",
        "en": "This ingredient is already in your pantry",
    },
    "shopping_item_not_found": {
        "pl": "Nie znaleziono pozycji na liście zakupów",
        "en": "Shopping list item not found",
    },
}


def get_lang(accept_language: str | None = Header(default=None)) -> Lang:
    """Pick the response language from the first entry of the Accept-Language header."""
    if accept_language:
        primary = accept_language.split(",")[0].strip().lower()[:2]
        if primary in SUPPORTED_LANGS:
            return primary  # type: ignore[return-value]
    return DEFAULT_LANG


def tr(key: str, lang: Lang) -> str:
    return MESSAGES[key][lang]

# SmartCook – Specification

## 1. Goal

Help people decide what to cook based on what they already have at home. That reduces both extra shopping trips and food waste. The system:

1. stores the user's available ingredients (the **pantry**), including optional quantities and expiry dates;
2. matches the pantry against a recipe database and ranks recipes by **ingredient availability**;
3. shows exactly which ingredients are missing and helps buy them (**shopping list**);
4. keeps the pantry up to date after cooking and shopping.

## 2. Functional requirements

| ID   | Requirement |
| ---- | ----------- |
| FR1  | A user can register, log in and log out (e-mail + password, JWT). |
| FR2  | A user can add, edit and remove pantry items: ingredient, optional quantity and unit, optional expiry date. |
| FR3  | The system suggests recipes ranked by the share of required ingredients the user owns. |
| FR4  | Each suggestion shows the match percentage, the missing ingredients, and the expiring ingredients it would use. |
| FR5  | Suggestions and the catalogue can be filtered by text, category, difficulty, maximum preparation time, tags and maximum number of missing ingredients. |
| FR6  | A recipe page shows ingredients (marked available/missing for a logged-in user), steps, and a servings scaler. |
| FR7  | A user can add the missing ingredients of a recipe to the shopping list. Duplicates are merged. |
| FR8  | A user can manage the shopping list manually, tick items off, and move bought items to the pantry. |
| FR9  | After cooking, the user can subtract the recipe's ingredient amounts from the pantry. |
| FR10 | A user can mark recipes as favorites and browse them. |
| FR11 | The UI and the recipe content are available in Polish and English, switchable at runtime. |

## 3. Non-functional requirements

- **Security:** passwords hashed with bcrypt; stateless JWT bearer tokens with expiry; every user-owned resource is checked against the token's user (other users' items return 404).
- **Portability:** SQLite by default, zero configuration. Because the app uses SQLAlchemy, switching to PostgreSQL only means changing `DATABASE_URL`.
- **Usability:** responsive layout (desktop → phone), keyboard-accessible ingredient autocomplete, light and dark themes.
- **Testability:** the matching algorithm is a pure function over model objects and has its own unit tests; the API is covered by integration tests against an in-memory database.

## 4. Architecture

```
┌──────────────────────┐   HTTP/JSON (+ Bearer token,   ┌─────────────────────────┐
│  React SPA (Vite)    │   Accept-Language: pl|en)      │  FastAPI                │
│  pages / components  │ ─────────────────────────────▶ │  routers → services     │
│  AuthContext, I18n   │ ◀───────────────────────────── │  SQLAlchemy ORM         │
└──────────────────────┘                                └───────────┬─────────────┘
                                                                    │
                                                              ┌─────▼─────┐
                                                              │  SQLite   │
                                                              └───────────┘
```

- **Client–server separation.** The frontend is a single-page application talking to a REST API. In development, Vite proxies `/api` to FastAPI, so the browser sees a single origin.
- **Layering in the backend.** Routers (HTTP, validation, authorization) → services (matching algorithm, serialization) → ORM models.
- **Localization.** Free text (ingredient names, recipe titles, descriptions, steps) is stored in `_pl`/`_en` columns, and the API returns the language named in `Accept-Language`. Fixed values (categories, tags, difficulty, units) travel as codes and are translated in the frontend, including Polish plural forms of units (`1 ząbek`, `2 ząbki`, `5 ząbków`) via `Intl.PluralRules`.

## 5. Data model

```
User 1───* PantryItem *───1 Ingredient 1───* RecipeIngredient *───1 Recipe *───* Tag
User 1───* ShoppingListItem *───1 Ingredient              ShoppingListItem *───0..1 Recipe
User *───* Recipe   (Favorite)
```

| Entity | Key fields |
| ------ | ---------- |
| `User` | email (unique), display_name, hashed_password |
| `Ingredient` | name_pl, name_en, category, default_unit, **is_staple** |
| `Recipe` | title/description/instructions in `_pl`/`_en`, prep_time_minutes, servings, difficulty, category |
| `RecipeIngredient` | recipe, ingredient, quantity, unit, **optional** |
| `PantryItem` | user, ingredient (unique per user), quantity, unit, **expires_at** |
| `ShoppingListItem` | user, ingredient, quantity, unit, checked, source recipe |
| `Favorite` | (user, recipe) composite key |
| `Tag` | code |

**Staples** (salt, pepper, sugar, oil, water, bay leaf, allspice, sweet paprika) are assumed to always be available. They never count as missing.

## 6. Matching algorithm

Implemented in `backend/app/services/matching.py`.

For recipe *r* and the user's set of owned ingredients *P*:

- *R(r)* = required ingredients of *r*: ingredients that are **not optional** and **not staples**
- **match(r) = |R(r) ∩ P| / |R(r)|** (equals 1 when *R(r)* is empty)
- **missing(r) = R(r) \ P**
- **expiring(r)** = ingredients of *r*, optional ones included, whose pantry item expires within *N* days (default 3, setting `EXPIRING_WITHIN_DAYS`), or has already expired

**Filtering:** recipes sharing no required ingredient with the pantry are dropped. The client may also set a minimum match (`min_match`, %) and a maximum number of missing ingredients (`max_missing`).

**Ranking** (lexicographic):

1. higher match ratio;
2. fewer missing ingredients (2/4 and 4/8 are both 50%, but one missing item is easier to buy than four);
3. more expiring ingredients used (reduces food waste);
4. shorter preparation time.

Complexity is *O(Σ|ingredients(r)|)* per request, which is linear in the size of the recipe–ingredient relation.

**Pantry update after cooking:** for each recipe ingredient (scaled by the chosen number of servings), the pantry quantity is reduced only if both quantities are known and the units are equal. Items reaching zero are removed. Different units (e.g. `pcs` vs `g`) are deliberately left untouched, because they cannot be converted reliably without per-ingredient density/weight data.

## 7. REST API

All paths are prefixed with `/api`. 🔒 means a Bearer token is required; 🔓 means a token is optional and adds personalisation. Interactive documentation is at `/docs`.

| Method | Path | Description |
| ------ | ---- | ----------- |
| POST | `/auth/register` | Create an account and return a token |
| POST | `/auth/login` | Log in and return a token |
| GET 🔒 | `/auth/me` | Current user |
| GET | `/ingredients?q=&category=` | Ingredient dictionary (localized, sorted) |
| GET 🔒 | `/pantry` | List pantry items |
| POST 🔒 | `/pantry` | Add an item (409 if already present) |
| PATCH 🔒 | `/pantry/{id}` | Update quantity/unit/expiry |
| DELETE 🔒 | `/pantry/{id}` | Remove an item |
| GET | `/recipes/meta` | Available categories, tags, difficulties |
| GET 🔓 | `/recipes?q=&category=&tag=&difficulty=&max_time=` | Catalogue |
| GET 🔒 | `/recipes/suggestions?…&min_match=&max_missing=` | Ranked suggestions with match info |
| GET 🔓 | `/recipes/{id}` | Recipe detail (+ availability per ingredient and match info) |
| POST 🔒 | `/recipes/{id}/cook?servings=` | Subtract ingredients from the pantry |
| GET 🔒 | `/favorites` | List favorites |
| PUT 🔒 | `/favorites/{recipe_id}` | Add a favorite (idempotent) |
| DELETE 🔒 | `/favorites/{recipe_id}` | Remove a favorite |
| GET 🔒 | `/shopping-list` | List items (unchecked first) |
| POST 🔒 | `/shopping-list` | Add an item (merged with an existing unchecked one) |
| POST 🔒 | `/shopping-list/from-recipe/{id}?servings=` | Add the recipe's missing ingredients |
| PATCH 🔒 | `/shopping-list/{id}` | Update / tick off an item |
| DELETE 🔒 | `/shopping-list/{id}` | Remove an item |
| POST 🔒 | `/shopping-list/checked/to-pantry` | Move ticked items into the pantry |
| DELETE 🔒 | `/shopping-list/checked` | Remove ticked items |

Errors use FastAPI's format `{"detail": "..."}`. Messages are localized according to `Accept-Language`.

## 8. Testing

`backend/tests/test_matching.py` covers the algorithm: full and partial match, staples and optional ingredients, ranking order, tie-breaking by expiring ingredients and time, filters, and the expiry window.

`backend/tests/test_api.py` covers the endpoints end to end against an in-memory SQLite database: auth and localized errors, authorization isolation between users, catalogue filters and Polish-letter search, pantry CRUD, suggestions, cooking, favorites, and the shopping list (merging duplicates, moving bought items to the pantry).

## 9. Possible extensions

- Unit conversion (g ↔ pcs ↔ ml) using per-ingredient conversion factors, so cooking can subtract every ingredient.
- Ingredient substitutes (e.g. sour cream ↔ plain yogurt) counted as partial matches.
- Weighted scoring, where the importance of an ingredient affects the match.
- Recipe photos, user-submitted recipes, ratings.
- Importing recipes from an external API, and a PostgreSQL deployment with Docker.

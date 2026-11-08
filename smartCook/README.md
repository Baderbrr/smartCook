# SmartCook

**Design and Implementation of a Smart Cooking Web Application Based on Ingredient Availability**

SmartCook suggests recipes based on what you already have at home. You keep a virtual pantry, and the app ranks recipes by how many of the required ingredients you own, preferring dishes that use up products close to their expiry date. Missing ingredients go to a shopping list with one click, and bought items move back into the pantry.

The UI and the recipe data are available in **Polish and English**.

| Layer    | Technology                                                    |
| -------- | ------------------------------------------------------------- |
| Backend  | Python 3.12, FastAPI, SQLAlchemy 2, SQLite, JWT (PyJWT), bcrypt |
| Frontend | React 18, React Router 6, Vite 5, plain CSS                   |
| Tests    | pytest, FastAPI TestClient                                    |

## Running locally

You need Python 3.11+ and Node.js 18+.

### 1. Backend (http://localhost:8000)

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

On first start the database (`backend/smartcook.db`) is created and seeded with 85 ingredients, 35 recipes and a demo account. Interactive API docs are at http://localhost:8000/docs.

### 2. Frontend (http://localhost:5173)

```bash
cd frontend
npm install
npm run dev
```

Vite forwards `/api/*` to the backend, so open http://localhost:5173 and log in with the demo account:

- **E-mail:** `demo@smartcook.pl`
- **Password:** `demo1234`

The demo pantry already contains some products, a few of them close to their expiry date.

### Tests

```bash
cd backend
pytest
```

### Resetting the database

```bash
cd backend
python -m app.seed --reset
```

## Project structure

```
backend/
  app/
    main.py            FastAPI app, CORS, router registration, startup seeding
    config.py          settings (env variables / .env)
    database.py        engine, session, declarative base
    models.py          ORM models
    schemas.py         Pydantic request/response models
    security.py        password hashing, JWT
    deps.py            auth dependencies
    i18n.py            Accept-Language handling, translated error messages
    routers/           auth, ingredients, pantry, recipes, favorites, shopping_list
    services/
      matching.py      recipe-matching and ranking algorithm
      serializers.py   ORM -> localized API schemas
    seed.py, seed_data.py
  tests/               unit tests (matching) + API tests
frontend/
  src/
    api.js             fetch wrapper (token, language, errors)
    auth.jsx, i18n.jsx React contexts
    translations.js    PL/EN strings, unit plural forms
    components/        Layout, RecipeCard, RecipeFilters, IngredientPicker...
    pages/             Suggestions, Pantry, Recipes, RecipeDetail, Favorites, ShoppingList, Login, Register
```

See [SPECIFICATION.md](SPECIFICATION.md) for requirements, architecture, data model, the matching algorithm and the API reference.

from tests.conftest import ingredient_id


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


# --- auth ---


def test_register_login_me(client):
    payload = {"email": "Anna@SmartCook.pl", "password": "secret123", "display_name": "Anna"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    # The same email (different case) cannot be registered twice.
    assert client.post("/api/auth/register", json=payload).status_code == 409

    res = client.post("/api/auth/login", json={"email": "anna@smartcook.pl", "password": "secret123"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["email"] == "anna@smartcook.pl"


def test_login_wrong_password_is_localized(client):
    body = {"email": "demo@smartcook.pl", "password": "wrong-password"}
    pl = client.post("/api/auth/login", json=body, headers={"Accept-Language": "pl"})
    en = client.post("/api/auth/login", json=body, headers={"Accept-Language": "en-US,en;q=0.9"})
    assert pl.status_code == en.status_code == 401
    assert pl.json()["detail"] == "Nieprawidłowy e-mail lub hasło"
    assert en.json()["detail"] == "Invalid email or password"


def test_protected_endpoints_require_token(client):
    assert client.get("/api/pantry").status_code == 401
    assert client.get("/api/recipes/suggestions").status_code == 401
    bad = {"Authorization": "Bearer not-a-token"}
    assert client.get("/api/pantry", headers=bad).status_code == 401


# --- catalogue ---


def test_recipes_are_localized(client):
    pl = client.get("/api/recipes", params={"q": "bigos"}, headers={"Accept-Language": "pl"}).json()
    en = client.get("/api/recipes", params={"q": "hunter"}, headers={"Accept-Language": "en"}).json()
    assert pl[0]["title"] == "Bigos"
    assert en[0]["title"] == "Bigos (hunter's stew)"
    assert pl[0]["id"] == en[0]["id"]


def test_recipe_filters(client):
    quick = client.get("/api/recipes", params={"max_time": 15}).json()
    assert quick and all(r["prep_time_minutes"] <= 15 for r in quick)
    veg = client.get("/api/recipes", params={"tag": ["vegetarian", "sweet"]}).json()
    assert veg and all({"vegetarian", "sweet"} <= set(r["tags"]) for r in veg)
    soups = client.get("/api/recipes", params={"category": "soup"}).json()
    assert soups and all(r["category"] == "soup" for r in soups)


def test_recipe_search_handles_polish_letters(client):
    res = client.get("/api/recipes", params={"q": "łosoś"}, headers={"Accept-Language": "pl"}).json()
    assert [r["title"] for r in res] == ["Łosoś pieczony z warzywami"]


def test_meta(client):
    meta = client.get("/api/recipes/meta").json()
    assert "soup" in meta["categories"]
    assert "vegetarian" in meta["tags"]
    assert meta["difficulties"] == ["easy", "medium", "hard"]


def test_recipe_detail_anonymous(client):
    recipe_id = client.get("/api/recipes").json()[0]["id"]
    detail = client.get(f"/api/recipes/{recipe_id}").json()
    assert detail["steps"]
    assert detail["match"] is None
    assert all(i["available"] is None for i in detail["ingredients"])
    assert client.get("/api/recipes/99999").status_code == 404


# --- pantry & suggestions ---


def test_pantry_crud(client, auth_headers):
    eggs = ingredient_id(client, "jajka")
    res = client.post("/api/pantry", json={"ingredient_id": eggs, "quantity": 6}, headers=auth_headers)
    assert res.status_code == 201
    item = res.json()
    assert item["unit"] == "pcs"  # falls back to the ingredient's default unit

    dup = client.post("/api/pantry", json={"ingredient_id": eggs}, headers=auth_headers)
    assert dup.status_code == 409

    upd = client.patch(
        f"/api/pantry/{item['id']}",
        json={"quantity": 4, "expires_at": "2030-01-01"},
        headers=auth_headers,
    )
    assert upd.json()["quantity"] == 4
    assert upd.json()["expires_at"] == "2030-01-01"

    assert client.delete(f"/api/pantry/{item['id']}", headers=auth_headers).status_code == 204
    assert client.get("/api/pantry", headers=auth_headers).json() == []


def test_cannot_touch_other_users_pantry(client, auth_headers):
    eggs = ingredient_id(client, "jajka")
    item = client.post("/api/pantry", json={"ingredient_id": eggs}, headers=auth_headers).json()
    other = client.post(
        "/api/auth/register",
        json={"email": "intruder@smartcook.pl", "password": "secret123", "display_name": "X"},
    ).json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    assert client.delete(f"/api/pantry/{item['id']}", headers=other_headers).status_code == 404


def test_suggestions_rank_by_pantry(client, auth_headers):
    for name in ("jajka", "masło", "szczypiorek"):
        client.post("/api/pantry", json={"ingredient_id": ingredient_id(client, name)}, headers=auth_headers)

    suggestions = client.get(
        "/api/recipes/suggestions", headers={**auth_headers, "Accept-Language": "pl"}
    ).json()
    assert suggestions[0]["title"] == "Jajecznica ze szczypiorkiem"
    assert suggestions[0]["match"]["match_percent"] == 100
    percents = [s["match"]["match_percent"] for s in suggestions]
    assert percents == sorted(percents, reverse=True)

    only_complete = client.get(
        "/api/recipes/suggestions", params={"max_missing": 0}, headers=auth_headers
    ).json()
    assert all(s["match"]["missing"] == [] for s in only_complete)


def test_cook_subtracts_from_pantry(client, auth_headers):
    recipe = client.get(
        "/api/recipes", params={"q": "jajecznica"}, headers={"Accept-Language": "pl"}
    ).json()[0]
    eggs = ingredient_id(client, "jajka")
    butter = ingredient_id(client, "masło")
    client.post("/api/pantry", json={"ingredient_id": eggs, "quantity": 6, "unit": "pcs"}, headers=auth_headers)
    client.post("/api/pantry", json={"ingredient_id": butter, "quantity": 15, "unit": "g"}, headers=auth_headers)

    res = client.post(f"/api/recipes/{recipe['id']}/cook", headers=auth_headers).json()
    assert [i["id"] for i in res["updated"]] == [eggs]
    assert [i["id"] for i in res["removed"]] == [butter]
    pantry = client.get("/api/pantry", headers=auth_headers).json()
    assert [(p["ingredient"]["id"], p["quantity"]) for p in pantry] == [(eggs, 2)]


# --- favorites ---


def test_favorites(client, auth_headers):
    recipe_id = client.get("/api/recipes").json()[0]["id"]
    assert client.put(f"/api/favorites/{recipe_id}", headers=auth_headers).status_code == 204
    assert client.put(f"/api/favorites/{recipe_id}", headers=auth_headers).status_code == 204
    favs = client.get("/api/favorites", headers=auth_headers).json()
    assert [f["id"] for f in favs] == [recipe_id]
    assert favs[0]["is_favorite"] is True

    detail = client.get(f"/api/recipes/{recipe_id}", headers=auth_headers).json()
    assert detail["is_favorite"] is True

    assert client.delete(f"/api/favorites/{recipe_id}", headers=auth_headers).status_code == 204
    assert client.get("/api/favorites", headers=auth_headers).json() == []


# --- shopping list ---


def test_shopping_list_from_recipe_and_to_pantry(client, auth_headers):
    recipe = client.get(
        "/api/recipes", params={"q": "jajecznica"}, headers={"Accept-Language": "pl"}
    ).json()[0]
    eggs = ingredient_id(client, "jajka")
    client.post("/api/pantry", json={"ingredient_id": eggs}, headers=auth_headers)

    items = client.post(f"/api/shopping-list/from-recipe/{recipe['id']}", headers=auth_headers).json()
    names = {i["ingredient"]["name"] for i in items}
    # Eggs are in the pantry, salt/pepper are staples -> only butter and chives are missing.
    assert names == {"masło", "szczypiorek"}
    assert all(i["recipe_id"] == recipe["id"] for i in items)

    # Adding the same recipe again merges quantities instead of duplicating rows.
    again = client.post(f"/api/shopping-list/from-recipe/{recipe['id']}", headers=auth_headers).json()
    assert len(again) == 2
    butter_item = next(i for i in again if i["ingredient"]["name"] == "masło")
    assert butter_item["quantity"] == 30

    client.patch(f"/api/shopping-list/{butter_item['id']}", json={"checked": True}, headers=auth_headers)
    pantry = client.post("/api/shopping-list/checked/to-pantry", headers=auth_headers).json()
    assert {p["ingredient"]["name"] for p in pantry} == {"jajka", "masło"}
    remaining = client.get("/api/shopping-list", headers=auth_headers).json()
    assert [i["ingredient"]["name"] for i in remaining] == ["szczypiorek"]


def test_shopping_list_manual_add_and_clear(client, auth_headers):
    milk = ingredient_id(client, "mleko")
    items = client.post(
        "/api/shopping-list", json={"ingredient_id": milk, "quantity": 500}, headers=auth_headers
    ).json()
    assert items[0]["unit"] == "ml"
    client.patch(f"/api/shopping-list/{items[0]['id']}", json={"checked": True}, headers=auth_headers)
    assert client.delete("/api/shopping-list/checked", headers=auth_headers).status_code == 204
    assert client.get("/api/shopping-list", headers=auth_headers).json() == []

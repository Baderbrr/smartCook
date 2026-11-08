import os
import uuid

# Must be set before the app (and its engine) is imported.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SEED_ON_STARTUP"] = "true"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    """Register a fresh user and return its Authorization header."""
    email = f"user-{uuid.uuid4().hex[:8]}@smartcook.pl"
    res = client.post(
        "/api/auth/register",
        json={"email": email, "password": "secret123", "display_name": "Tester"},
    )
    assert res.status_code == 201, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def ingredient_id(client, name_pl: str) -> int:
    res = client.get("/api/ingredients", params={"q": name_pl}, headers={"Accept-Language": "pl"})
    matches = [i for i in res.json() if i["name"] == name_pl]
    assert matches, f"ingredient {name_pl!r} not found"
    return matches[0]["id"]

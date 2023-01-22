from fastapi.testclient import TestClient
import pytest

ciao_feature = {
    "kind": "python",
    "definition": "from figo.decorator import feature\n"
    "@feature()\n"
    "async def ciao(ctx) -> str:\n"
    "   return 'expected result'",
    "name": "ciao",
}

ciao_feature_updated = {
    "kind": "python",
    "definition": "from figo.decorator import feature\n"
    "@feature()\n"
    "async def ciao(ctx) -> str:\n"
    "   return 'updated result'",
    "name": "ciao",
}


def test_add_property(client: TestClient):
    body = {"features": [ciao_feature]}
    response = client.patch("/features", json=body)
    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_delete_property(client: TestClient):
    body = {"features": [ciao_feature]}
    response = client.patch("/features", json=body)
    assert response.status_code == 200
    assert response.json()["count"] == 1
    path = f"/features/{ciao_feature['name']}"
    response = client.delete(path)

    assert response.status_code == 200
    assert response.json()["count"] == 0

    with pytest.raises(Exception):
        response = client.post("/calculate", json={"features": ["ciao"]})


def test_calculation(client: TestClient):
    body = {"features": [ciao_feature]}
    response = client.patch("/features", json=body)
    assert response.status_code == 200
    assert response.json()["count"] == 1

    response = client.post("/calculate", json={"features": ["ciao"]})
    assert response.json() == {"ciao": "expected result"}


def test_update_property(client: TestClient):
    test_add_property(client)

    body = {"features": [ciao_feature_updated]}
    response = client.patch("/features", json=body)

    response = client.post("/calculate", json={"features": ["ciao"]})
    assert response.json() == {"ciao": "updated result"}

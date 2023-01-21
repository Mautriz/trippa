from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from api.server import app as server_app


@pytest.fixture()
def app() -> FastAPI:
    return server_app


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)

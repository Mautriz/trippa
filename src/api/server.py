from functools import cache
import importlib
from pathlib import Path
from typing import Any
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from figo.base import AnyFeature

from figo.resolution import Figo

app = FastAPI()

BASE_FOLDER = Path(__file__).parent
FEATURES_FOLDER = BASE_FOLDER / "features"
FEATURES_MODULE = "api.features"


class UpsertFeaturePayload(BaseModel):
    name: str
    definition: str
    kind: str = "python"


class UpsertFeaturesPayload(BaseModel):
    features: list[UpsertFeaturePayload]


class CalculatePayload(BaseModel):
    input: dict[str, Any]
    ask: list[str]


class CountResponse(BaseModel):
    count: int


@cache
def resolver() -> Figo:
    return Figo([])


def resolver_dep() -> Figo:
    return resolver()


def create_feature(feature_meta: UpsertFeaturePayload) -> None:
    FEATURE_PATH = FEATURES_FOLDER / f"{feature_meta.name}.py"
    FEATURE_PATH.write_text(feature_meta.definition)


def import_feature(feature_name: str) -> AnyFeature:
    feature_module = importlib.import_module(f"api.features.{feature_name}")
    feature_module = importlib.reload(feature_module)
    return getattr(feature_module, feature_name)


@app.patch("/features")
async def upsert_features(
    body: UpsertFeaturesPayload, figo: Figo = Depends(resolver_dep)
) -> CountResponse:
    for f in body.features:
        create_feature(f)

    new_features = [import_feature(f.name) for f in body.features]
    figo.upsert_features(new_features)

    return CountResponse(count=len(figo.features))


@app.delete("/features/{id}")
async def delete_feature(id: str, figo: Figo = Depends(resolver_dep)) -> CountResponse:
    figo.remove_features([figo.features[id]])

    return CountResponse(count=len(figo.features))


class CalculateBody(BaseModel):
    features: list[str]


@app.post("/calculate")
async def calculate_features(
    body: CalculateBody,
    figo: Figo = Depends(resolver_dep),
) -> dict[str, Any]:
    res = figo.start()
    result = await res.resolve_many([figo.features[f] for f in body.features])
    return result

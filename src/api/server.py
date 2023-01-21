from functools import cache
from pathlib import Path
from typing import Any
from fastapi import Depends, FastAPI
from pydantic import BaseModel

from figo.resolution import Figo

app = FastAPI()


BASE_FOLDER = Path(__file__).parent
FEATURES_FOLDER = BASE_FOLDER / "features"
FEATURES_MODULE = "api.features"


class UpsertFeaturePayload(BaseModel):
    kind: str
    name: str
    definition: str


class CalculatePayload(BaseModel):
    input: dict[str, Any]
    ask: list[str]


@cache
def resolver() -> Figo:
    return Figo([])


def resolver_dep() -> Figo:
    return resolver()


def create_feature(feature_meta: UpsertFeaturePayload) -> None:
    FEATURE_PATH = FEATURES_FOLDER / f"{feature_meta.name}.py"
    FEATURE_PATH.write_text(feature_meta.definition)


def import_feature(feature_meta: UpsertFeaturePayload) -> None:
    ...


@app.patch("/features")
async def upsert_features(
    features: list[UpsertFeaturePayload], res: Figo = Depends(resolver_dep)
) -> None:
    for f in features:
        create_feature(f)
        import_feature(f)

    res.upsert_features(features)
    return None


@app.delete("/features/:id")
async def delete_feature(id: str, figo: Figo = Depends(resolver_dep)) -> None:
    figo.remove_features([figo.features[id]])
    return None


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

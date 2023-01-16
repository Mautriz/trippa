import pandas as pd
import pytest

from figo.resolution import Figo
from tests.batch_features import other_feature, other_row_feature, uuids


@pytest.mark.asyncio
async def test_batch_calculation(figo: Figo):

    inputs = pd.DataFrame({"uuids": ["rotondo", "marco", "franco"]})
    result = (
        await figo.start().input_batch(inputs).resolve_batch([other_feature])
    ).to_pandas()

    assert result["uuids"].to_list() == ["rotondo", "marco", "franco"]
    assert result["other_feature"].to_list() == [
        "rotondorotondo",
        "marcomarco",
        "francofranco",
    ]


@pytest.mark.asyncio
async def test_batch_row_calculation(figo: Figo):
    inputs = pd.DataFrame({"uuids": ["rotondo", "marco", "franco"]})
    result = (
        await figo.start().input_batch(inputs).resolve_batch([other_row_feature])
    ).to_pandas()

    assert result["uuids"].to_list() == ["rotondo", "marco", "franco"]
    assert result["other_row_feature"].to_list() == [
        "roberto rotondo",
        "roberto marco",
        "roberto franco",
    ]


@pytest.mark.asyncio
async def test_batch_input(figo: Figo):

    inputs = pd.DataFrame({"uuids": ["rotondo", "marco", "franco"]})
    result = (await figo.start().input_batch(inputs).resolve_batch([uuids])).to_pandas()

    assert result["uuids"].to_list() == ["rotondo", "marco", "franco"]

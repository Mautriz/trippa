from datetime import datetime
from typing import Any, Mapping

import pandas as pd
import pytest

from figo.base import AnyFeature
from figo.resolution import Figo
from tests.batch_features import (
    date_series,
    end_date,
    other_feature,
    other_row_feature,
    start_date,
    uuids,
)


@pytest.mark.asyncio
async def test_batch_source(figo: Figo):
    start = datetime(2000, 1, 1)
    end = datetime(2000, 1, 15)

    inputs: Mapping[AnyFeature, Any] = {
        start_date: start,
        end_date: end,
    }

    result = await figo.start().input(inputs).resolve_batch([date_series])

    assert result["date_series"].to_list() == pd.date_range(start, end).to_list()


@pytest.mark.asyncio
async def test_batch_calculation(figo: Figo):
    inputs = pd.DataFrame({"uuids": ["rotondo", "marco", "franco"]})
    result = await figo.start().input_batch(inputs).resolve_batch([other_feature])

    assert result["other_feature"].to_list() == [
        "rotondorotondo",
        "marcomarco",
        "francofranco",
    ]


@pytest.mark.asyncio
async def test_batch_row_calculation(figo: Figo):
    inputs = pd.DataFrame({"uuids": ["rotondo", "marco", "franco"]})
    result = await figo.start().input_batch(inputs).resolve_batch([other_row_feature])

    assert result["other_row_feature"].to_list() == [
        "roberto rotondo",
        "roberto marco",
        "roberto franco",
    ]


@pytest.mark.asyncio
async def test_batch_input(figo: Figo):

    inputs = pd.DataFrame({"uuids": ["rotondo", "marco", "franco"]})
    result = await figo.start().input_batch(inputs).resolve_batch([uuids])

    assert result["uuids"].to_list() == ["rotondo", "marco", "franco"]

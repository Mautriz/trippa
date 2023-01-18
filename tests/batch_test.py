from datetime import datetime
from typing import Any, Mapping

import pandas as pd
import pytest

from figo.base import AnyFeature
from figo.resolution import Figo
from tests.batch_features import (
    aggregate_feature,
    date_series,
    end_date,
    other_feature,
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
async def test_batch_input(figo: Figo):

    inputs = pd.DataFrame({"uuids": ["rotondo", "marco", "franco"]})
    result = await figo.start().input_batch(inputs).resolve_batch([uuids])

    assert result["uuids"].to_list() == ["rotondo", "marco", "franco"]


@pytest.mark.asyncio
async def test_aggregate_function(figo: Figo):
    start = datetime(2000, 1, 1)
    end = datetime(2000, 1, 15)

    inputs: Mapping[AnyFeature, Any] = {
        start_date: start,
        end_date: end,
    }

    result = await figo.start().input(inputs).resolve(aggregate_feature)

    assert result == 15

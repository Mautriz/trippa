from asyncio import sleep
from datetime import datetime
from typing import AsyncIterable

import pandas as pd

from figo.decorator import input_feature
from figo.variants import batch_feature, batch_generator


@batch_feature()
def uuids() -> pd.Series:
    ...


@batch_feature()
async def other_feature(uuids: pd.Series) -> pd.Series:
    await sleep(0.2)
    return uuids + uuids


# test 2


@input_feature()
def start_date() -> datetime:
    ...


@input_feature()
def end_date() -> datetime:
    ...


@batch_generator()
async def date_series(
    start_date: datetime, end_date: datetime
) -> AsyncIterable[pd.Series]:
    yield pd.date_range(start_date, end_date).to_series()

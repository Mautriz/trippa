from datetime import datetime
from typing import AsyncIterable

import pandas as pd

from figo.decorator import input_feature
from figo.variants import batch_feature, batch_row_feature, batch_source


@batch_feature()
def uuids() -> pd.Series:
    ...


@batch_feature()
def other_feature(uuids: pd.Series) -> pd.Series:
    return uuids + uuids


@batch_row_feature()
def other_row_feature(uuids: str) -> str:
    return f"roberto {uuids}"


# test 2


@input_feature()
def start_date() -> datetime:
    ...


@input_feature()
def end_date() -> datetime:
    ...


@batch_source()
async def date_series(
    start_date: datetime, end_date: datetime
) -> AsyncIterable[pd.Series]:
    yield pd.date_range(start_date, end_date).to_series()

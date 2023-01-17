from asyncio import sleep
from datetime import datetime
from typing import AsyncIterable

import pandas as pd

from figo.base import Info
from figo.decorator import input_feature
from figo.variants import batch_feature, batch_generator


@batch_feature()
async def uuids(ctx: Info) -> pd.Series:
    ...


@batch_feature()
async def other_feature(ctx: Info) -> pd.Series:
    uuids_ = await ctx.resolve(uuids)
    await sleep(0.2)
    return uuids_ + uuids_


# test 2


@input_feature()
def start_date() -> datetime:
    ...


@input_feature()
def end_date() -> datetime:
    ...


@batch_generator()
async def date_series(ctx: Info) -> AsyncIterable[pd.Series]:
    start_date_, end_date_ = await ctx.resolve(start_date), await ctx.resolve(end_date)
    yield pd.date_range(start_date_, end_date_).to_series()

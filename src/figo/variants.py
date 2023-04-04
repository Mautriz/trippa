from dataclasses import dataclass
from typing import Any, AsyncIterable, Awaitable, Callable

import modin.pandas as md
import pandas as pd

from figo.base import BaseFeature, Info


class BatchFeature(BaseFeature[pd.Series]):
    resolver: Callable[[Info[Any]], Awaitable[pd.Series]]


@dataclass
class BatchGenerator(BaseFeature):
    resolver: Callable[[Info[Any]], AsyncIterable[pd.Series]]

    def __hash__(self) -> int:
        return hash(self.name)


@dataclass
class batch_generator:
    def __call__(
        self, resolver: Callable[[Info[Any]], AsyncIterable[pd.Series]]
    ) -> BatchGenerator:
        return BatchGenerator(resolver.__name__, resolver=resolver)


class batch_feature:
    def __call__(
        self, resolver: Callable[[Info[Any]], Awaitable[pd.Series]]
    ) -> BatchFeature:
        return BatchFeature(name=resolver.__name__, resolver=resolver)


def create_sql_feature(query: str) -> BaseFeature[md.DataFrame]:
    return md.read_csv(query)


def create_csv_feature(path: str) -> BaseFeature[md.DataFrame]:
    return md.read_csv(path)


def create_parquet_feature(path: str) -> BaseFeature[md.DataFrame]:
    return md.read_parquet(path)

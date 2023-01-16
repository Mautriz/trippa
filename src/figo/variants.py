from dataclasses import dataclass
from typing import AsyncIterable, Callable, Generator, Iterable

import pandas as pd

from figo.base import BaseFeature
from utils.types import T


class Feature(BaseFeature):
    ...


class BatchFeature(BaseFeature[pd.Series]):
    resolver: Callable[..., pd.Series]


class BatchRowFeature(BaseFeature[T]):
    resolver: Callable[..., T]


@dataclass
class BatchSource(BaseFeature):
    join_key: str | None
    resolver: Callable[..., AsyncIterable[pd.Series]]

    def __hash__(self) -> int:
        return hash(self.name)


@dataclass
class batch_source:
    join_key: str | None = None

    def __call__(
        self, resolver: Callable[..., AsyncIterable[pd.Series]]
    ) -> BatchSource:
        return BatchSource(resolver.__name__, resolver=resolver, join_key=self.join_key)


class batch_row_feature:
    def __call__(self, resolver: Callable[..., T]) -> BatchRowFeature[T]:
        return BatchRowFeature[T](name=resolver.__name__, resolver=resolver)


class batch_feature:
    def __call__(self, resolver: Callable[..., pd.Series]) -> BatchFeature:
        return BatchFeature(name=resolver.__name__, resolver=resolver)

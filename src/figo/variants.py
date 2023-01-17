from dataclasses import dataclass
from typing import AsyncIterable, Awaitable, Callable

import pandas as pd

from figo.base import BaseFeature


class Feature(BaseFeature):
    ...


class BatchFeature(BaseFeature[pd.Series]):
    resolver: Callable[..., pd.Series] | Callable[..., Awaitable[pd.Series]]


@dataclass
class BatchGenerator(BaseFeature):
    resolver: Callable[..., AsyncIterable[pd.Series]]

    def __hash__(self) -> int:
        return hash(self.name)


@dataclass
class batch_generator:
    def __call__(
        self, resolver: Callable[..., AsyncIterable[pd.Series]]
    ) -> BatchGenerator:
        return BatchGenerator(resolver.__name__, resolver=resolver)


class batch_feature:
    def __call__(
        self, resolver: Callable[..., pd.Series] | Callable[..., Awaitable[pd.Series]]
    ) -> BatchFeature:
        return BatchFeature(name=resolver.__name__, resolver=resolver)

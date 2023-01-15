from dataclasses import dataclass
from typing import Callable

import pandas as pd

from figo.feature import Feature
from utils.types import T


class BatchFeature(Feature[pd.Series]):
    resolver: Callable[..., pd.Series]


class BatchRowFeature(Feature[T]):
    resolver: Callable[..., T]


class batch_row_feature:
    def __call__(self, resolver: Callable[..., T]) -> BatchRowFeature[T]:
        return BatchRowFeature[T](name=resolver.__name__, resolver=resolver)


class batch_feature:
    def __call__(self, resolver: Callable[..., pd.Series]) -> BatchFeature:
        return BatchFeature(name=resolver.__name__, resolver=resolver)

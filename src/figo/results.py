from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic

from figo.utils.types import T


@dataclass(frozen=True)
class ResultSuccess(Generic[T]):
    value: T


@dataclass(frozen=True)
class ResultFailure:
    error: Any


FeatureResult = ResultSuccess[T] | ResultFailure

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic

from utils.types import T


@dataclass(frozen=True)
class SuccessResult(Generic[T]):
    value: T


@dataclass(frozen=True)
class ResultFailure:
    error: Any


FeatureResult = SuccessResult[T] | ResultFailure

"""Resolution results wrappers, to handle exception in a more controlled way."""


from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic

from figo.utils.types import T


@dataclass(frozen=True)
class ResultSuccess(Generic[T]):
    """Wraps a feature result value."""

    value: T


@dataclass(frozen=True)
class ResultFailure:
    """Wraps an exception happened during feature resolution."""

    error: Any


FeatureResult = ResultSuccess[T] | ResultFailure

"""
Decorators to create features from resolver functions
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable

from figo.errors import MissingInputException
from figo.utils.types import T

from .base import BaseFeature, Info


@dataclass(frozen=True)
class feature:
    meta: Any = None
    """Any metadata you want to add that might be eventually retrieved."""

    def __call__(
        self,
        resolver: Callable[[Info[Any]], Awaitable[T]],
    ) -> BaseFeature[T]:
        return BaseFeature[T](name=resolver.__name__, resolver=resolver)


class RaiseOnMissing(Enum):
    TOKEN = ""


@dataclass(frozen=True)
class input_feature:
    default_value: Any | RaiseOnMissing = RaiseOnMissing.TOKEN

    def __call__(
        self,
        resolver: Callable[[], T],
    ) -> BaseFeature[T]:
        feature_name = resolver.__name__

        def raiser(ctx: Info[Any]) -> T:
            if self.default_value != RaiseOnMissing.TOKEN:
                return self.default_value
            raise MissingInputException(feature_name)

        return BaseFeature[T](
            name=feature_name,
            resolver=raiser,
        )

"""
Decorators to create features from resolver functions
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Awaitable, Callable, overload

from figo.errors import MissingInputException
from utils.types import T

from .base import Feature


class feature:
    @overload
    def __call__(
        self,
        resolver: Callable[..., Awaitable[T]],
    ) -> Feature[T]:
        ...

    @overload
    def __call__(self, resolver: Callable[..., T]) -> Feature[T]:
        ...

    def __call__(
        self,
        resolver: Callable[..., Any],
    ) -> Feature[Any]:
        feature_name = resolver.__name__

        return Feature[T](
            name=feature_name,
            resolver=resolver,
        )


class RaiseOnMissing(Enum):
    TOKEN = ""


class input_feature:
    default_value: Any | RaiseOnMissing = RaiseOnMissing.TOKEN

    def __call__(
        self,
        resolver: Callable[[], T],
    ) -> Feature[T]:
        feature_name = resolver.__name__

        def raiser() -> T:
            if self.default_value != RaiseOnMissing.TOKEN:
                return self.default_value
            raise MissingInputException(feature_name)

        return Feature[T](
            name=feature_name,
            resolver=raiser,
        )

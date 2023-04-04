"""
Decorators to create features from resolver functions
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, cast, overload

from figo.exceptions import MissingInputException
from figo.utils.types import T

from .base import BaseFeature, Info


@dataclass(frozen=True)
class feature:
    """
    Helper decorator to create feature definitions easily.

    Wraps a function and creates a BaseFeature from it.

    Ex:
    ```python
    @feature()
    async def ciao(ctx: Info) -> str:
        first_ = await ctx.resolve(first)
        return f"{first_}ciao"
    ```
    """

    meta: Any = None
    """Any metadata you want to add that might be eventually retrieved."""

    @overload
    def __call__(
        self,
        resolver: Callable[[Info[Any]], Awaitable[T]],
    ) -> BaseFeature[T]:
        ...

    @overload
    def __call__(
        self,
        resolver: Callable[[Info[Any]], T],
    ) -> BaseFeature[T]:
        ...

    def __call__(
        self,
        resolver: Callable[[Info[Any]], Any],
    ) -> BaseFeature[Any]:
        return BaseFeature[Any](name=resolver.__name__, resolver=resolver)


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
                return cast(T, self.default_value)
            raise MissingInputException(feature_name)

        return BaseFeature[T](
            name=feature_name,
            resolver=raiser,
        )

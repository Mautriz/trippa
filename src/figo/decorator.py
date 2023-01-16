"""
Decorators to create features from resolver functions
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, overload

from figo.errors import MissingInputException
from utils.types import T

from .base import AnyFeature, BaseFeature


@dataclass(frozen=True)
class feature:
    @overload
    def __call__(
        self,
        resolver: Callable[..., Awaitable[T]],
    ) -> BaseFeature[T]:
        ...

    @overload
    def __call__(self, resolver: Callable[..., T]) -> BaseFeature[T]:
        ...

    def __call__(
        self,
        resolver: Callable[..., Any],
    ) -> BaseFeature[Any]:
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

        def raiser() -> T:
            if self.default_value != RaiseOnMissing.TOKEN:
                return self.default_value
            raise MissingInputException(feature_name)

        return BaseFeature[T](
            name=feature_name,
            resolver=raiser,
        )


@dataclass
class feature_group:
    feature_names: list[str]

    def __call__(self, resolver: Callable[..., Any]) -> list[AnyFeature]:
        return [
            self._create_feature(resolver, feature) for feature in self.feature_names
        ]

    @staticmethod
    def _create_feature(resolver: Callable[..., Any], feature_name: str) -> AnyFeature:
        # resolver
        ...

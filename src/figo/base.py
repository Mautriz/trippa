"""
Basic building blocks for feature resolution.
"""

from __future__ import annotations

import dataclasses
import inspect
from functools import cached_property
from typing import Any, Awaitable, Callable, Generic, Type, cast

from figo.utils.types import T, V


class Info(Generic[V]):
    """
    Info is used during feature resolution to access other features
    or a generic context given by the client.
    """

    def __init__(self, ctx: V, resolve: Callable[[AnyFeature], Awaitable[Any]]) -> None:
        self.ctx = ctx
        self._resolve = resolve

    async def resolve(self, feature: BaseFeature[T]) -> T:
        return await self._resolve(feature)  # type: ignore


@dataclasses.dataclass
class BaseFeature(Generic[T]):  # pylint: disable=too-many-instance-attributes
    """
    BaseFeature represent the definition of a feature.

    Contains all the required data and metadata to describe a feature.
    """

    name: str
    resolver: Callable[[Info[Any]], Awaitable[T] | T]

    def __hash__(self) -> int:
        return self.name.__hash__()

    def __str__(self) -> str:
        return self.name

    @cached_property
    def description(self) -> str:
        return (self.resolver.__doc__ or "").strip()

    @cached_property
    def type(self) -> Type[T]:
        return cast(
            Type[T],
            self._signature.return_annotation,
        )

    @cached_property
    def _signature(self) -> inspect.Signature:
        return inspect.signature(self.resolver, eval_str=True)


AnyFeature = BaseFeature[Any]

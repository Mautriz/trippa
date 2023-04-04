from __future__ import annotations

import asyncio
import dataclasses
import inspect
from functools import cached_property
from typing import Any, Awaitable, Callable, Generic, Sequence

import modin.pandas as md

from utils.types import T, V


class Info(Generic[V]):
    def __init__(
        self,
        ctx: V,
        resolve: Callable[[AnyFeature], Awaitable[Any]],
        frame: Callable[[], md.DataFrame],
    ) -> None:
        self.ctx = ctx
        self._resolve = resolve
        self._frame = frame
        self.env: dict[str, str] = {}

    async def resolve(self, feature: BaseFeature[T]) -> T:
        return await self._resolve(feature)

    async def frame(self, deps: Sequence[AnyFeature]) -> md.DataFrame:
        await asyncio.gather(*[self.resolve(f) for f in deps])
        return self._frame()


@dataclasses.dataclass
class BaseFeature(Generic[T]):  # pylint: disable=too-many-instance-attributes
    name: str
    resolver: Callable[[Info[Any]], Awaitable[T] | T]
    additional_deps: list[str] = dataclasses.field(default_factory=list)

    def __hash__(self) -> int:
        return self.name.__hash__()

    def __str__(self) -> str:
        return self.name

    @cached_property
    def args_names(self) -> list[str]:
        return list(self._signature.parameters.keys())

    @cached_property
    def description(self) -> str:
        return (self.resolver.__doc__ or "").strip()

    @cached_property
    def _signature(self) -> inspect.Signature:
        return inspect.signature(self.resolver, eval_str=True)


AnyFeature = BaseFeature[Any]

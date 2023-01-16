from __future__ import annotations

import dataclasses
import inspect
from functools import cached_property
from typing import Any, Awaitable, Callable, Generic

from utils.types import T


@dataclasses.dataclass
class BaseFeature(Generic[T]):  # pylint: disable=too-many-instance-attributes
    name: str
    resolver: Callable[..., Awaitable[T] | T]

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

    # @cached_property
    # def type(self) -> Type[T]:
    #     return cast(
    #         Type[T],
    #         self._signature.return_annotation,
    #     )

    @cached_property
    def _signature(self) -> inspect.Signature:
        return inspect.signature(self.resolver, eval_str=True)


AnyFeature = BaseFeature[Any]

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic

from utils.types import T

# @dataclass
# class EntityResults:
#     _results: dict[str, Any] = dataclasses.field(default_factory=dict)

#     def __getitem__(self, __key: Feature[T]) -> Awaitable[FeatureResult[T]]:
#         return cast(
#             Awaitable[FeatureResult[T]],
#             self._tasks[__key],
#         )

#     def get(self, __key: Feature[T]) -> Awaitable[FeatureResult[T]] | None:
#         return self._tasks.get(__key)

#     def __setitem__(
#         self,
#         __key: Feature[T] | str,
#         item: FeatureResult[T],
#     ) -> None:
#         self._tasks[__key] = item


@dataclass(frozen=True)
class ResultSuccess(Generic[T]):
    value: T


@dataclass(frozen=True)
class ResultFailure:
    error: Any


FeatureResult = ResultSuccess[T] | ResultFailure

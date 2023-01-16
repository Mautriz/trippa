import dataclasses
from dataclasses import dataclass
from typing import Any, Awaitable, cast

from figo.base import AnyFeature, Feature
from figo.results import FeatureResult
from utils.types import T


@dataclass
class EntityTasks:
    _tasks: dict[AnyFeature, Any] = dataclasses.field(default_factory=dict)

    def __getitem__(self, __key: Feature[T]) -> Awaitable[FeatureResult[T]]:
        return cast(
            Awaitable[FeatureResult[T]],
            self._tasks[__key],
        )

    def get(self, __key: Feature[T]) -> Awaitable[FeatureResult[T]] | None:
        return self._tasks.get(__key)

    def __setitem__(
        self,
        __key: Feature[T],
        item: Awaitable[FeatureResult[T]],
    ) -> None:
        self._tasks[__key] = item

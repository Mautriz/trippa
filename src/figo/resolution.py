from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from logging import getLogger
from typing import Any, ClassVar, Mapping, Sequence, Type

from typing_extensions import Self

from figo.dependencies import find_deps
from figo.tasks import EntityTasks
from figo.utils.asyncio import maybe_await
from figo.utils.types import T

from .base import AnyFeature, BaseFeature, Info
from .results import FeatureResult, ResultFailure, ResultSuccess

logger = getLogger(__name__)


@dataclass
class Resolution:
    features: Mapping[str, AnyFeature]
    ctx: Any
    _inputs: dict[str, FeatureResult[Any]] = field(default_factory=dict)
    _tasks: EntityTasks = field(default_factory=EntityTasks)

    def input(self, inputs: Mapping[AnyFeature, Any] | Mapping[str, Any]) -> Self:
        # Set results from inputs
        parsed_input: dict[str, FeatureResult[Any]] = {
            f.name if isinstance(f, BaseFeature) else f: ResultSuccess(v)
            for f, v in inputs.items()
        }
        self._inputs = self._inputs | parsed_input
        return self

    async def resolve_many(self, features: Sequence[AnyFeature]) -> dict[str, Any]:
        results = await asyncio.gather(*[self.resolve(f) for f in features])
        return {f.name: results[i] for i, f in enumerate(features)}

    async def safe_resolve_many(
        self, features: Sequence[AnyFeature]
    ) -> dict[str, FeatureResult[Any]]:
        results: Sequence[FeatureResult] = await asyncio.gather(
            *[self.safe_resolve(f) for f in features]
        )
        return {f.name: results[i] for i, f in enumerate(features)}

    async def resolve(
        self,
        feature: BaseFeature[T],
    ) -> T:
        result = await self.safe_resolve(feature)
        if isinstance(result, ResultFailure):
            raise result.error
        return result.value

    async def safe_resolve(self, feature: BaseFeature[T]) -> FeatureResult[T]:
        if result := self._inputs.get(feature.name):
            return result

        if not self._tasks.get(feature):
            self._tasks[feature] = asyncio.create_task(self._safe_resolve(feature))

        return await self._tasks[feature]

    async def _safe_resolve(
        self,
        feature: BaseFeature[T],
    ) -> FeatureResult[T]:
        try:
            return ResultSuccess(await self._instance_resolver(feature))
        except Exception as err:
            return ResultFailure(err)

    async def _instance_resolver(self, feature: BaseFeature[T]) -> T:
        return await maybe_await(feature.resolver(self.info()))

    def info(self) -> Info[Any]:
        return Info(self.ctx, self.resolve)


class Figo:
    resolution_class: ClassVar[Type[Resolution]] = Resolution

    features: Mapping[str, AnyFeature]

    def __init__(self, features: Sequence[AnyFeature]) -> None:
        self.features = {f.name: f for f in features}

    def find_deps(self, feature: AnyFeature) -> set[AnyFeature]:
        return find_deps(feature, self.features)

    @classmethod
    def from_modules(cls, modules: list[Any]) -> Self:
        return cls(cls._get_features_from_modules(modules))

    @staticmethod
    def _get_features_from_modules(modules: list[Any]) -> list[AnyFeature]:
        return [
            feature
            for module in modules
            for feature in module.__dict__.values()
            if isinstance(feature, BaseFeature)
        ]

    def start(self, ctx: Any = None) -> Resolution:
        return Resolution(self.features, ctx)

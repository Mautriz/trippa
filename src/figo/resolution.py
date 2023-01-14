from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from logging import getLogger
from typing import Any

from typing_extensions import Self

from figo.tasks import EntityTasks
from utils.asyncio import maybe_await
from utils.types import T

from .base import AnyFeature, Feature
from .results import FeatureResult, ResultFailure, ResultSuccess

logger = getLogger(__name__)


class Figo:
    features: dict[str, AnyFeature]

    @classmethod
    def from_modules(cls, modules: list[Any]) -> Self:
        features = [
            feature
            for module in modules
            for feature in module.__dict__.values()
            if isinstance(feature, Feature)
        ]

        return cls(features)

    def __init__(self, features: list[AnyFeature]) -> None:
        self.features = {f.name: f for f in features}

    def start(self) -> Resolution:
        return Resolution(self.features)


@dataclass
class Resolution:
    features: dict[str, AnyFeature]
    _tasks: EntityTasks = field(default_factory=EntityTasks)
    _results: dict[str, Any] = field(default_factory=dict)

    def inputs(self, inputs: dict[AnyFeature | str, Any]) -> Self:
        # Set results from inputs
        parsed_input = {
            f.name if isinstance(f, Feature) else f: v for f, v in inputs.items()
        }
        self._results = parsed_input | self._results

        return self

    async def resolve_many(self, features: list[AnyFeature]) -> dict[str, Any]:
        return {f.name: await self.resolve(f) for f in features}

    async def safe_resolve_many(
        self, features: list[AnyFeature]
    ) -> dict[str, FeatureResult[Any]]:
        return {f.name: await self.safe_resolve(f) for f in features}

    async def resolve(
        self,
        feature: Feature[T],
    ) -> T:
        result = await self.safe_resolve(feature)
        if isinstance(result, ResultFailure):
            raise result.error
        return result.value

    async def safe_resolve(self, feature: Feature[T]) -> FeatureResult[T]:
        if result := self._results.get(feature.name):
            return ResultSuccess(result)

        if not self._tasks.get(feature):
            self._tasks[feature] = asyncio.create_task(self._safe_resolve(feature))

        return await self._tasks[feature]

    async def _safe_resolve(
        self,
        feature: Feature[T],
    ) -> FeatureResult[T]:
        try:
            feature_kwargs = {
                f_name: await self.resolve(self.features[f_name])
                for f_name in feature.args_names
            }
            task = maybe_await(feature.resolver(**feature_kwargs))
            result = await task
            self._results[feature.name] = result
            return ResultSuccess(result)

        except Exception as err:
            return ResultFailure(err)

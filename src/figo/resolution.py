from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from logging import getLogger
from typing import Any, ClassVar, Type, TypeVar, cast


import pandas as pd
import ray.data
from typing_extensions import Self

from figo.batch_feature import BatchFeature, BatchRowFeature
from figo.errors import UnknownFeature
from figo.tasks import EntityTasks
from utils.asyncio import maybe_await
from utils.types import T

from .feature import AnyFeature, Feature
from .results import FeatureResult, ResultFailure, ResultSuccess

logger = getLogger(__name__)


@dataclass
class Resolution:
    features: dict[str, AnyFeature]
    _batch_result: ray.data.Dataset = field(init=False)
    _tasks: EntityTasks = field(default_factory=EntityTasks)
    _results: dict[str, FeatureResult[Any]] = field(default_factory=dict)

    def inputs(self, inputs: dict[AnyFeature | str, Any]) -> Self:
        # Set results from inputs
        parsed_input: dict[str, FeatureResult[Any]] = {
            f.name if isinstance(f, Feature) else f: ResultSuccess(v)
            for f, v in inputs.items()
        }
        self._results = self._results | parsed_input  # type: ignore
        return self

    def batch_inputs(self, inputs: pd.DataFrame) -> Self:
        self._batch_result = ray.data.from_pandas(inputs)
        return self

    async def resolve_batch(self, features: list[AnyFeature]) -> ray.data.Dataset:
        await self.resolve_many(features)
        return self._batch_result

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
            return result

        if not self._tasks.get(feature):
            self._tasks[feature] = asyncio.create_task(self._safe_resolve(feature))  # type: ignore

        return await self._tasks[feature]

    async def _safe_resolve(
        self,
        feature: Feature[T],
    ) -> FeatureResult[T]:
        try:
            fn_kwargs = await self._resolve_deps(feature)
            # if isinstance(feature, BatchFeature):
            #     self._batch_result = self._batch_add_column(feature)
            #     return cast(Any, ResultSuccess(None))

            # get resolution arguments

            task = maybe_await(feature.resolver(**fn_kwargs))
            result = ResultSuccess(await task)
            self._results[feature.name] = result
            return result

        except Exception as err:
            result = ResultFailure(err)
            self._results[feature.name] = result
            return result

    def _batch_add_column(self, feature: BatchFeature) -> ray.data.Dataset:
        def _wrapped_resolver(data: pd.DataFrame) -> pd.Series:
            fn_kwargs = {arg: data[arg] for arg in feature.args_names}
            return feature.resolver(**fn_kwargs)

        return self._batch_result.add_column(feature.name, _wrapped_resolver)

    async def _resolve_deps(self, feature: Feature) -> dict[str, Any]:
        await asyncio.gather(
            *[self.safe_resolve(self.features[f_name]) for f_name in feature.args_names]
        )
        as_kwargs: dict[str, Any] = {}
        for f in feature.args_names:
            arg_feature = self.features[f]
            match arg_feature:
                case BatchFeature() | BatchRowFeature():
                    as_kwargs[arg_feature.name] = "ciao"
                case Feature():
                    result = self._results[arg_feature.name]
                    if isinstance(result, ResultFailure):
                        raise result.error
                    as_kwargs[arg_feature.name] = result.value

        return as_kwargs

    # def _


class Figo:
    resolution_class: ClassVar[Type[Resolution]] = Resolution

    features: dict[str, AnyFeature]

    def __init__(self, features: list[AnyFeature]) -> None:
        self.features = {f.name: f for f in features}

        # Safe checks
        for f in features:
            for dep in f.args_names:
                if dep not in self.features:
                    raise UnknownFeature(f.name, dep)

    @classmethod
    def from_modules(cls, modules: list[Any]) -> Self:
        return cls(cls._get_features_from_modules(modules))

    @staticmethod
    def _get_features_from_modules(modules: list[Any]) -> list[AnyFeature]:
        return [
            feature
            for module in modules
            for feature in module.__dict__.values()
            if isinstance(feature, Feature)
        ]

    def start(self) -> Resolution:
        return Resolution(self.features)

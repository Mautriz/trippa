from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from logging import getLogger
from typing import Any, ClassVar, Mapping, Sequence, Type, cast

import modin.pandas as md
import pandas as pd
import ray
from typing_extensions import Self

from figo.dag_solver import find_deps
from figo.tasks import EntityTasks
from figo.variants import BatchFeature, BatchGenerator
from utils.types import T

from .base import AnyFeature, BaseFeature, Info
from .results import FeatureResult, ResultFailure, ResultSuccess

logger = getLogger(__name__)

FRAME = "frame"


@dataclass
class Resolution:
    features: dict[str, AnyFeature]
    ctx: Any
    _frame: md.DataFrame = field(default=None)  # type: ignore
    _inputs: dict[str, FeatureResult[Any]] = field(default_factory=dict)
    _tasks: EntityTasks = field(default_factory=EntityTasks)

    def input(self, inputs: Mapping[AnyFeature, Any] | Mapping[str, Any]) -> Self:
        # Set results from inputs
        parsed_input: dict[str, FeatureResult[Any]] = {
            f.name if isinstance(f, BaseFeature) else f: ResultSuccess(v)
            for f, v in inputs.items()
        }
        self._inputs = self._inputs | parsed_input  # type: ignore
        return self

    def input_batch(self, inputs: pd.DataFrame) -> Self:
        self._inputs = {
            str(col): ResultSuccess(md.Series(inputs[col])) for col in inputs.columns
        }
        return self

    async def resolve_batch(self, features: Sequence[AnyFeature]) -> md.DataFrame:
        results = await asyncio.gather(*[self.resolve(f) for f in features])
        return md.DataFrame({f.name: results[i] for i, f in enumerate(features)})

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
            self._tasks[feature] = asyncio.create_task(self._safe_resolve(feature))  # type: ignore

        return await self._tasks[feature]

    async def _safe_resolve(
        self,
        feature: BaseFeature[T],
    ) -> FeatureResult[T]:
        try:
            if isinstance(feature, BatchGenerator):
                result = await self._batch_generator_resolver(feature)
                return cast(Any, ResultSuccess(result))

            if isinstance(feature, BatchFeature):
                result = await self._batch_feature_resolver(feature)
                return cast(Any, ResultSuccess(result))

            if isinstance(feature, BaseFeature):
                result = ResultSuccess(await self._instance_resolver(feature))
                return result

        except Exception as err:
            result = ResultFailure(err)
            return result

    async def _batch_feature_resolver(self, feature: BatchFeature) -> md.Series:
        result = cast(md.Series, await feature.resolver(self.info()))
        self.frame_add_column(feature.name, result)
        return result

    async def _instance_resolver(self, feature: BaseFeature[T]) -> T:
        return await feature.resolver(self.info())

    async def _batch_generator_resolver(self, feature: BatchGenerator) -> md.Series:
        result = md.Series()

        async for df in feature.resolver(self.info()):
            result = md.concat([md.Series(df), result])

        if result.empty:
            raise Exception(
                f"Unable to create a dataset for feture {feature.name}, function is not yielding anything"
            )
        self.frame_add_column(feature.name, result)
        return result

    def info(self) -> Info[Any]:
        return Info(self.ctx, self.resolve, self.frame)

    def frame(self) -> md.DataFrame:
        return self._frame

    def frame_add_column(self, name: str, col: md.Series) -> None:
        if self._frame is None:
            self._frame = md.DataFrame({name: col})
        self._frame[name] = col


class Figo:
    resolution_class: ClassVar[Type[Resolution]] = Resolution

    features: dict[str, AnyFeature]

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
        ray.init(  # type: ignore
            runtime_env={"env_vars": {"__MODIN_AUTOIMPORT_PANDAS__": "1"}},
            ignore_reinit_error=True,
        )
        return Resolution(self.features, ctx)

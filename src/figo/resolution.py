from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from logging import getLogger
from typing import Any, ClassVar, Mapping, Sequence, Type, cast

import modin.pandas as md
import pandas as pd
import ray
from typing_extensions import Self

from figo.errors import UnknownFeature
from figo.tasks import EntityTasks
from figo.variants import BatchFeature, BatchRowFeature, BatchSource
from utils.asyncio import maybe_await
from utils.types import T

from .base import AnyFeature, BaseFeature
from .results import FeatureResult, ResultFailure, ResultSuccess

ray.init(  # type: ignore
    runtime_env={"env_vars": {"__MODIN_AUTOIMPORT_PANDAS__": "1"}},
    ignore_reinit_error=True,
)

logger = getLogger(__name__)


@dataclass
class Resolution:
    features: dict[str, AnyFeature]
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
            if isinstance(feature, BatchSource):
                result = await self._batch_source_resolver(feature)
                return cast(Any, ResultSuccess(result))

            if isinstance(feature, BatchFeature):
                result = await self._batch_feature_resolver(feature)
                return cast(Any, ResultSuccess(result))

            if isinstance(feature, BatchRowFeature):
                result = await self._batch_row_resolver(feature)
                return cast(Any, ResultSuccess(result))

            if isinstance(feature, BaseFeature):
                result = ResultSuccess(await self._instance_resolver(feature))
                return result

        except Exception as err:
            result = ResultFailure(err)
            return result

    async def _batch_source_resolver(self, feature: BatchSource) -> md.Series:
        kwargs = await self.resolve_many([self.features[f] for f in feature.args_names])
        result = md.Series()

        async for df in feature.resolver(**kwargs):
            result = md.concat([md.Series(df), result])

        if result.empty:
            raise Exception(
                f"Unable to create a dataset for feture {feature.name}, function is not yielding anything"
            )

        return result

    async def _batch_row_resolver(self, feature: BatchRowFeature) -> md.Series:
        kwargs = await self.resolve_many([self.features[f] for f in feature.args_names])
        batch_features_names = [
            name for name, v in kwargs.items() if isinstance(v, md.Series)
        ]
        instance_kwargs = {
            name: v for name, v in kwargs.items() if not isinstance(v, md.Series)
        }
        frame = md.DataFrame(
            {name: v for name, v in kwargs.items() if isinstance(v, md.Series)}
        )

        def _row_wrapped_resolver(row):
            kwargs = {
                f_name: row[f_name] for f_name in batch_features_names
            } | instance_kwargs
            return feature.resolver(**kwargs)

        return cast(md.Series, frame.apply(_row_wrapped_resolver, axis=1))

    async def _batch_feature_resolver(self, feature: BatchFeature) -> md.Series:
        kwargs = await self.resolve_many([self.features[f] for f in feature.args_names])
        return cast(md.Series, await maybe_await(feature.resolver(**kwargs)))

    async def _instance_resolver(self, feature: BaseFeature[T]) -> T:
        kwargs = await self.resolve_many([self.features[f] for f in feature.args_names])
        return await maybe_await(feature.resolver(**kwargs))


class Figo:
    resolution_class: ClassVar[Type[Resolution]] = Resolution

    features: dict[str, AnyFeature]

    def __init__(self, features: Sequence[AnyFeature]) -> None:
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
            if isinstance(feature, BaseFeature)
        ]

    def start(self) -> Resolution:
        return Resolution(self.features)

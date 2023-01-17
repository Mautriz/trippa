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

ray.init(
    runtime_env={"env_vars": {"__MODIN_AUTOIMPORT_PANDAS__": "1"}},
    ignore_reinit_error=True,
)

logger = getLogger(__name__)


@dataclass
class Resolution:
    features: dict[str, AnyFeature]
    _batch: md.DataFrame = field(init=False, default=None)
    _results: dict[str, FeatureResult[Any]] = field(default_factory=dict)
    _tasks: EntityTasks = field(default_factory=EntityTasks)

    def input(self, inputs: Mapping[AnyFeature, Any] | Mapping[str, Any]) -> Self:
        # Set results from inputs
        parsed_input: dict[str, FeatureResult[Any]] = {
            f.name if isinstance(f, BaseFeature) else f: ResultSuccess(v)
            for f, v in inputs.items()
        }
        self._results = self._results | parsed_input  # type: ignore
        return self

    def input_batch(self, inputs: pd.DataFrame) -> Self:
        self.input({self.features[k]: None for k in inputs.columns.to_list()})
        self._batch = md.DataFrame(inputs)
        return self

    async def resolve_batch(self, features: Sequence[AnyFeature]) -> md.DataFrame:
        await self.resolve_many(features)
        return self._batch

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
        if result := self._results.get(feature.name):
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
                self._batch = await self._batch_source_resolver(feature)
                return cast(Any, ResultSuccess(None))

            if isinstance(feature, BatchFeature):
                self._batch = await self._batch_feature_resolver(feature)
                return cast(Any, ResultSuccess(None))

            if isinstance(feature, BatchRowFeature):
                self._batch = await self._batch_row_resolver(feature)
                return cast(Any, ResultSuccess(None))

            if isinstance(feature, BaseFeature):
                result = await self._instance_resolver(feature)
                self._results[feature.name] = result
                return result

        except Exception as err:
            result = ResultFailure(err)
            self._results[feature.name] = result
            return result

    async def _batch_source_resolver(self, feature: BatchSource) -> md.DataFrame:
        instance, batch = self._get_partitioned_features(feature.args_names)
        instance_kwargs = await self.resolve_many(instance)
        await self.resolve_many(batch)

        result: md.Series = md.Series()

        async for df in feature.resolver(**instance_kwargs):
            result = md.concat([md.Series(df), result])

        if result.empty:
            raise Exception(
                f"Unable to create a dataset for feture {feature.name}, function is not yielding anything"
            )

        if self._batch is not None:
            self._batch[feature.name] = result
        else:
            self._batch = md.DataFrame({feature.name: result})

        return self._batch

    async def _batch_row_resolver(self, feature: BatchRowFeature) -> md.DataFrame:
        instance, batch = self._get_partitioned_features(feature.args_names)
        instance_kwargs = await self.resolve_many(instance)
        await self.resolve_many(batch)
        feature_names = tuple(f.name for f in batch)

        def _row_wrapped_resolver(row):
            kwargs = {f_name: row[f_name] for f_name in feature_names} | instance_kwargs
            return feature.resolver(**kwargs)

        result = self._batch.apply(_row_wrapped_resolver, axis=1)
        self._batch[feature.name] = result
        return self._batch

    async def _batch_feature_resolver(self, feature: BatchFeature) -> md.DataFrame:
        instance, batch = self._get_partitioned_features(feature.args_names)
        instance_kwargs = await self.resolve_many(instance)
        await self.resolve_many(batch)

        data = self._batch
        feature_names = tuple(f.name for f in batch)

        kwargs = {f_name: data[f_name] for f_name in feature_names} | instance_kwargs
        data[feature.name] = feature.resolver(**kwargs)
        return data

    async def _instance_resolver(self, feature: BaseFeature) -> FeatureResult:
        instance, _ = self._get_partitioned_features(feature.args_names)
        fn_kwargs = await self.resolve_many(instance)
        task = maybe_await(feature.resolver(**fn_kwargs))
        return ResultSuccess(await task)

    def _get_partitioned_features(
        self, feature_names: list[str]
    ) -> tuple[Sequence[BaseFeature], Sequence[BatchFeature | BatchRowFeature]]:
        features = [self.features[name] for name in feature_names]

        batch = [
            f
            for f in features
            if isinstance(f, BatchFeature) or isinstance(f, BatchRowFeature)
        ]

        instance = [
            f
            for f in features
            if not isinstance(f, BatchFeature) and not isinstance(f, BatchRowFeature)
        ]

        return instance, batch


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

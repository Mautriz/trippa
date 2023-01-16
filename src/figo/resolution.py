from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from logging import getLogger
from typing import Any, ClassVar, Mapping, Sequence, Type, cast

import pandas as pd
import ray.data
from typing_extensions import Self

from figo.errors import UnknownFeature
from figo.tasks import EntityTasks
from figo.variants import BatchFeature, BatchRowFeature, BatchSource
from utils.asyncio import maybe_await
from utils.types import T

from .base import AnyFeature, BaseFeature
from .results import FeatureResult, ResultFailure, ResultSuccess

logger = getLogger(__name__)


@dataclass
class Resolution:
    features: dict[str, AnyFeature]
    _results: dict[str, FeatureResult[Any]] = field(default_factory=dict)
    _batch_result: ray.data.Dataset = field(init=False)
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
        self._batch_result = ray.data.from_pandas(inputs)
        return self

    async def resolve_batch(self, features: Sequence[AnyFeature]) -> ray.data.Dataset:
        await self.resolve_many(features)
        return self._batch_result

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
                self._batch_result = await self._batch_source_resolver(feature)
                return cast(Any, ResultSuccess(None))

            if isinstance(feature, BatchFeature):
                self._batch_result = await self._batch_feature_resolver(feature)
                return cast(Any, ResultSuccess(None))

            if isinstance(feature, BatchRowFeature):
                self._batch_result = await self._batch_row_resolver(feature)
                return cast(Any, ResultSuccess(None))

            if isinstance(feature, BaseFeature):
                result = await self._instance_resolver(feature)
                self._results[feature.name] = result
                return result

        except Exception as err:
            result = ResultFailure(err)
            self._results[feature.name] = result
            return result

    async def _batch_source_resolver(self, feature: BatchSource) -> ray.data.Dataset:
        instance, batch = self._get_partitioned_features(feature.args_names)
        instance_kwargs = await self.resolve_many(instance)
        await self.resolve_many(batch)

        dataset: ray.data.Dataset | None = None

        async for df in feature.resolver(**instance_kwargs):
            new_dataset = ray.data.from_pandas(pd.DataFrame({feature.name: df}))
            dataset = dataset.union([new_dataset]) if dataset else new_dataset

        if not dataset:
            raise Exception(
                f"Unable to create a dataset for feture {feature.name}, function is not yielding anything"
            )

        return dataset

    async def _batch_row_resolver(self, feature: BatchRowFeature) -> ray.data.Dataset:
        instance, batch = self._get_partitioned_features(feature.args_names)
        instance_kwargs = await self.resolve_many(instance)
        await self.resolve_many(batch)

        def _wrapped_resolver(
            data: pd.DataFrame | Any,
            *args,
        ) -> pd.DataFrame:
            col_name, instance_kwargs, feature_names = args

            def _row_wrapped_resolver(row):
                batch_kwargs = {f_name: row[f_name] for f_name in feature_names}
                return feature.resolver(**(batch_kwargs | instance_kwargs))

            data[col_name] = data.apply(_row_wrapped_resolver, axis=1)
            return data

        return self._batch_result.map_batches(
            _wrapped_resolver,
            fn_args=(
                feature.name,
                instance_kwargs,
                tuple(f.name for f in batch),
            ),
        )

    async def _batch_feature_resolver(self, feature: BatchFeature) -> ray.data.Dataset:
        instance, batch = self._get_partitioned_features(feature.args_names)
        instance_kwargs = await self.resolve_many(instance)
        await self.resolve_many(batch)

        def _wrapped_resolver(
            data: pd.DataFrame | Any,
            *args,
        ) -> pd.DataFrame:
            col_name, instance_kwargs, feature_names = args
            batch_kwargs = {f_name: data[f_name] for f_name in feature_names}
            data[col_name] = feature.resolver(**(batch_kwargs | instance_kwargs))
            return data

        return self._batch_result.map_batches(
            _wrapped_resolver,
            fn_args=(
                feature.name,
                instance_kwargs,
                tuple(f.name for f in batch),
            ),
        )

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

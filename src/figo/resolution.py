from __future__ import annotations

import asyncio
import dataclasses
from collections import defaultdict
from dataclasses import dataclass
from logging import getLogger
from typing import Any, Awaitable, Generic, cast

from utils.asyncio import maybe_await
from utils.types import T, V

from .base import Feature, Info
from .entity import EntityKey
from .results import FeatureResult, ResultFailure, SuccessResult

logger = getLogger(__name__)


@dataclass
class EntityResults:
    results: dict[Feature[Any], Any] = dataclasses.field(default_factory=dict)

    def __getitem__(self, __key: Feature[T]) -> Awaitable[FeatureResult[T]]:
        return cast(
            Awaitable[FeatureResult[T]],
            self.results[__key],
        )

    def get(self, __key: Feature[T]) -> Awaitable[FeatureResult[T]] | None:
        return self.results.get(__key)

    def __setitem__(
        self,
        __key: Feature[T],
        item: Awaitable[FeatureResult[T]],
    ) -> None:
        self.results[__key] = item


@dataclass()
class Figo(Generic[V]):
    ctx: V
    results: defaultdict[EntityKey, EntityResults] = dataclasses.field(
        default_factory=lambda: defaultdict(EntityResults)
    )

    async def resolve(
        self,
        feature: Feature[T],
        entity_key: EntityKey,
    ) -> T:
        result = await self.safe_resolve(feature, entity_key)
        if isinstance(result, ResultFailure):
            raise result.error
        return result.value

    async def safe_resolve(
        self,
        feature: Feature[T],
        entity_key: EntityKey,
    ) -> FeatureResult[T]:
        entity_results = self.results[entity_key]

        if not entity_results.get(feature):
            entity_results[feature] = asyncio.create_task(
                self._safe_resolve(feature, entity_key)
            )
        return await entity_results[feature]

    async def _safe_resolve(
        self,
        feature: Feature[T],
        entity_key: EntityKey,
    ) -> FeatureResult[T]:
        try:
            task = maybe_await(
                feature.resolver(
                    Info(
                        self.ctx,
                        entity_key,
                        self.resolve,
                    )
                )
            )
            return SuccessResult(await task)
        except Exception as err:
            return ResultFailure(err)

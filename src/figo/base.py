from __future__ import annotations

import dataclasses
from typing import Any, Awaitable, Callable, Generic, Protocol, Type, cast

from utils.types import T, V

from .entity import EntityId, EntityKey, EntityName


class FeatureResolver(Protocol, Generic[T]):
    async def __call__(
        self,
        feature: Feature[T],
        entity_key: EntityKey,
    ) -> T:
        ...


class Info(Generic[V]):
    def __init__(
        self,
        ctx: V,
        entity_key: EntityKey,
        resolve: FeatureResolver[Any],
    ) -> None:
        self.ctx = ctx
        self.entity_key = entity_key
        self._resolve = resolve

    @property
    def entity_name(self) -> EntityName:
        return self.entity_key[0]

    @property
    def entity_id(self) -> EntityId:
        return self.entity_key[1]

    async def resolve(
        self,
        feature: Feature[T],
        entity_key: EntityKey | None = None,
    ) -> T:
        return cast(
            T,
            await self._resolve(
                feature,
                entity_key or self.entity_key,
            ),
        )


@dataclasses.dataclass
class Feature(Generic[T]):  # pylint: disable=too-many-instance-attributes
    name: str
    description: str
    type: Type[T]
    resolver: Callable[[Info[Any]], Awaitable[T] | T]

    def __hash__(self) -> int:
        return self.name.__hash__()

    def __str__(self) -> str:
        return self.name


AnyFeature = Feature[Any]

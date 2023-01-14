"""
Decorators to create features from resolver functions
"""

from __future__ import annotations

from inspect import signature
from typing import Any, Awaitable, Callable, Type, cast, overload

from utils.types import T

from .base import Feature, Info


@overload
def feature(
    resolver: Callable[[Info[Any]], Awaitable[T]],
) -> Feature[T]:
    ...


@overload
def feature(resolver: Callable[[Info[Any]], T]) -> Feature[T]:
    ...


def feature(
    resolver: Callable[[Info[Any]], Any],
) -> Feature[Any]:
    feature_name = resolver.__name__
    resolver_signature = signature(resolver, eval_str=True)
    feature_type = cast(
        Type[T],
        resolver_signature.return_annotation,
    )

    return Feature[T](
        name=feature_name,
        description=(resolver.__doc__ or "").strip(),
        type=feature_type,
        resolver=resolver,
    )

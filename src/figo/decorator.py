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
    resolver: Callable[[Info[Any]], Awaitable[T] | T],
) -> Feature[T]:
    feature_name = resolver.__name__
    resolver_signature = signature(resolver, eval_str=True)
    feature_type = cast(Type[T], resolver_signature.return_annotation)

    return Feature[T](
        name=feature_name,
        description=_get_documentation(resolver),
        type=feature_type,
        resolver=resolver,
    )


def _get_documentation(resolver: Callable[..., Any]) -> str:
    return (resolver.__doc__ or "").strip()

import asyncio
from typing import Awaitable, cast

from .types import T


async def maybe_await(
    value: Awaitable[T] | T,
) -> T:
    if asyncio.iscoroutine(value):
        return await cast(Awaitable[T], value)
    return cast(T, value)

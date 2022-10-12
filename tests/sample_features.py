from typing import Any

from figo import feature
from figo.base import Info


@feature
def first(info: Info[Any]) -> str:
    return "first" + str(info.entity_key)


@feature
async def ciao(info: Info[Any]) -> str:
    first_ = await info.resolve(first)
    second_ = await info.resolve(first, ("boh", "ciaoo"))

    await info.resolve(age, ("person", "contractor"))
    return first_ + second_


@feature
def age(info: Info[Any]) -> int:
    return len(info.entity_key)

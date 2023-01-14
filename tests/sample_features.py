from figo import feature
from figo.decorator import input_feature


@input_feature()
def uuid() -> str:
    """uuid of the entity"""
    ...


@feature()
def first(uuid: str) -> str:
    return "first" + uuid


@feature()
async def ciao(first: str) -> str:
    return first + "ciao"

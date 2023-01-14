from figo import feature
from figo.decorator import input_feature


@input_feature()
def uuid() -> str:
    """uuid of the entity"""
    ...


@input_feature()
def missing_input() -> int:
    """uuid of the entity"""
    ...


@feature()
def using_missing_input(missing_input: int) -> int:
    """uuid of the entity"""
    return missing_input


@feature()
def first(uuid: str) -> str:
    return "first" + uuid


@feature()
async def ciao(first: str) -> str:
    return first + "ciao"

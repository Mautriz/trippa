from figo import feature
from figo.base import Info
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
async def using_missing_input(ctx: Info) -> int:
    """uuid of the entity"""
    return await ctx.resolve(missing_input)


@feature()
async def first(ctx: Info) -> str:
    return "first" + await ctx.resolve(uuid)


@feature()
async def ciao(ctx: Info) -> str:
    return await ctx.resolve(first) + "ciao"

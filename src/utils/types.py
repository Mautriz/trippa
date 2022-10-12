from __future__ import annotations

import typing
from enum import Enum
from inspect import isclass
from types import UnionType
from typing import Any, Optional, Tuple, Type, TypeGuard, TypeVar, Union

from pydantic import BaseModel

T = TypeVar("T", bound=Any)
V = TypeVar("V", bound=Any)

AnyType = type | UnionType


def decompose_generic_type(
    typ: AnyType,
) -> Tuple[type, Tuple[type, ...]]:
    """
    Split a type into its origin and generic arguments, if any.

    int => (int, ())
    int | str => (Union, (int, str))
    Optional[int] => (Union, (int, None.__class__))
    dict[str, int] => (dict, (str, int))
    list[Optional[int]] => (list, (Optional[int],))
    """
    origin = typing.get_origin(typ)

    # Note: A|B returns UnionType so we coherce it back to typing.Union
    if origin == UnionType:
        origin = Union

    return (origin or typ), typing.get_args(typ)  # type: ignore


def is_optional(typ: AnyType) -> TypeGuard[Optional[AnyType]]:
    """
    Returns True if the type admits None.
    """

    origin, args = decompose_generic_type(typ)

    # Optionals are represented as unions
    if origin != Union:  # type: ignore
        return False

    # A Union to be optional needs to have at least one None type
    return any(arg == None.__class__ for arg in args)


def get_optional_annotation(typ: Optional[AnyType]) -> AnyType:
    """
    Returns the type wrapped inside the optional annotation.
    """
    non_none_types = tuple(arg for arg in typing.get_args(typ) if arg != None.__class__)

    return Union[non_none_types] if len(non_none_types) > 1 else non_none_types[0]  # type: ignore


def is_enum(typ: Type[Any]) -> TypeGuard[Type[Enum]]:
    return isclass(typ) and issubclass(typ, Enum)


def is_pydantic(typ: Type[Any]) -> TypeGuard[Type[BaseModel]]:
    return isclass(typ) and issubclass(typ, BaseModel)

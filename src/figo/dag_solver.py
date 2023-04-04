import ast
from ast import Attribute, Call, ImportFrom, Load, Module, Name, NodeVisitor, alias
from functools import lru_cache
from inspect import getsource, getsourcefile
from pathlib import Path
from typing import Any

from .base import AnyFeature


@lru_cache(maxsize=5)
def get_source_file_ast(path: Path) -> Module:
    source_text = path.read_text("utf-8")
    return ast.parse(source_text)


class DependencyVisitor(NodeVisitor):
    def __init__(self) -> None:
        self.dependencies = set[str]()

    def visit_Call(self, node: Call) -> Any:
        match node:  # noqa
            case Call(
                func=Attribute(
                    value=Name(id="ctx", ctx=Load()), attr="resolve", ctx=Load()
                ),
                args=[Name(id=feature_alias, ctx=Load())],
            ):
                self.dependencies.add(feature_alias)


class AliasVisitor(NodeVisitor):
    def __init__(self) -> None:
        self.alias_to_original = dict[str, str]()

    def visit_ImportFrom(self, node: ImportFrom) -> Any:
        match node:  # noqa
            case ImportFrom(
                names=[alias(name=name, asname=str(asname))],
            ):
                self.alias_to_original[name] = asname


def find_deps(
    feature: AnyFeature, available_features: dict[str, AnyFeature]
) -> set[AnyFeature]:
    final_deps = set[AnyFeature]()

    source_file = getsourcefile(feature.resolver)
    source_function = getsource(feature.resolver)

    if not source_file:
        raise Exception(f"No source file? Strange stuff.")

    source_ast = get_source_file_ast(Path(source_file))

    alias_visitor = AliasVisitor()
    alias_visitor.visit(source_ast)

    dependency_visitor = DependencyVisitor()
    dependency_visitor.visit(ast.parse(source_function))

    for feature_alias in dependency_visitor.dependencies:
        original_name = alias_visitor.alias_to_original.get(
            feature_alias, feature_alias
        )
        final_deps.add(available_features[original_name])

    return final_deps

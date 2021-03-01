import re
from dataclasses import dataclass, replace
from typing import Any, Dict, Generator, Optional, OrderedDict, Type, cast

from docstring_parser import parse as parse_docstring
from parso.grammar import load_grammar
from parso.python.tree import (
    Class,
    Function,
    Module,
    Name,
    Param,
    PythonNode,
    Scope,
    String,
)
from schema import Optional as OptionalItem, Schema

from .base import BaseGenerator, markdown_block, markdown_heading, markdown_paragraph

__all__ = ["ParsoGenerator"]


@dataclass
class ParsoGeneratorContext:
    filepath: str
    symbol: Optional[str]
    parent: Optional[Scope]
    depth: int
    deep: bool
    options: Dict[str, Any]

    @property
    def parent_name(self):
        try:
            return self.parent.name.value
        except AttributeError:
            return None

    def set_parent(self, parent):
        return replace(self, parent=parent, depth=self.depth + 1)


class ParsoGenerator(BaseGenerator):
    name = "parso"
    options_schema = Schema(
        {
            OptionalItem("version", default=None): str,
            OptionalItem("encoding", default="utf-8"): str,
            OptionalItem("depth", default=2): int,
            OptionalItem("deep", default=True): bool,
            OptionalItem(
                "methods", default={"undocumented": True, "private": False}
            ): Schema(
                {
                    OptionalItem("undocumented", default=True): bool,
                    OptionalItem("private", default=False): bool,
                }
            ),
        }
    )

    def generate(self, filepath, symbol, options):
        grammar = load_grammar(version=options["version"])
        with open(filepath, encoding=options["encoding"]) as f:
            parser = grammar.parse(f.read())
            module: Module = parser.get_root_node()

        if symbol is not None:
            root_node = find_symbol(module, symbol)
        else:
            root_node = module

        context = ParsoGeneratorContext(
            filepath,
            symbol,
            parent=None,
            depth=options["depth"],
            deep=options["deep"],
            options=options,
        )
        return self._generate_doc(root_node, context)

    def _generate_doc(self, node: Scope, context: ParsoGeneratorContext):
        if isnode(node, Module):
            yield from self._generate_module_doc(cast(Module, node), context)
        elif isnode(node, Class):
            yield from self._generate_class_doc(cast(Class, node), context)
        elif isnode(node, Function):
            yield from self._generate_func_doc(cast(Function, node), context)

    def _generate_module_doc(self, module_node: Module, context: ParsoGeneratorContext):
        yield markdown_heading(f"`{context.filepath}`", level=context.depth)

        doc_node = cast(Optional[String], module_node.get_doc_node())
        if doc_node:
            doc = parse_docstring(doc_node._get_payload())
            yield markdown_paragraph(doc.short_description)
            yield markdown_paragraph(doc.long_description)

        if context.deep:
            for child_node in iter_children(module_node):
                yield from self._generate_doc(
                    child_node, context.set_parent(module_node)
                )

    def _generate_class_doc(self, class_node: Class, context: ParsoGeneratorContext):
        yield markdown_heading(f"`{class_node.name.value}`", level=context.depth)

        doc_node = cast(Optional[String], class_node.get_doc_node())
        if doc_node:
            doc = parse_docstring(doc_node._get_payload())
            yield markdown_paragraph(doc.short_description)
            yield markdown_paragraph(doc.long_description)

        if context.deep:
            for child_node in iter_children(class_node):
                yield from self._generate_doc(
                    child_node, context.set_parent(class_node)
                )

    def _generate_func_doc(self, func_node: Function, context: ParsoGeneratorContext):
        if not context.options["methods"]["undocumented"]:
            if func_node.get_doc_node() is None:
                return

        if not context.options["methods"]["private"]:
            if re.match(r"^_[^_]+?$", func_node.name.value):
                return

        if isnode(context.parent, Class):
            is_static = any(
                re.search("(staticmethod|classmethod)", decorator_node.get_code())
                for decorator_node in func_node.get_decorators()
            )
            prefix = context.parent_name + ("." if is_static else "#")
        else:
            prefix = ""

        param_nodes: OrderedDict[str, Param] = OrderedDict(
            [
                (param_node.name.value, param_node)
                for idx, param_node in enumerate(func_node.get_params())
                if not (idx == 0 and param_node.name.value in ("self", "cls"))
            ]
        )

        doc_node = cast(Optional[String], func_node.get_doc_node())
        if doc_node:
            doc = parse_docstring(doc_node._get_payload())
            param_docs = {param_doc.arg_name: param_doc for param_doc in doc.params}
        else:
            doc = None
            param_docs = {}

        yield markdown_heading(
            "`{prefix}{title}({params})`\n".format(
                prefix=prefix,
                title=func_node.name.value,
                params="".join(
                    param_node.get_code() for param_node in param_nodes.values()
                ).strip(),
            ),
            level=context.depth,
        )

        if doc:
            yield markdown_paragraph(doc.short_description)

        if param_nodes:
            yield markdown_heading("Arguments", level=context.depth + 1)
            with markdown_block() as block:
                block.writeln("| Name | Type | Description | Default |")
                block.writeln("| ---- | ---- | ----------- | ------- |")
                for param_name, param_node in param_nodes.items():
                    param_doc = param_docs.get(param_name)
                    block.writeln(
                        "| {name} | {type} | {description} | {default} |".format(
                            name=param_name,
                            type=(
                                getattr(param_doc, "type_name", None)
                                or get_code(param_node.annotation)
                                or "-"
                            ),
                            description=getattr(param_doc, "description", "-"),
                            default=(
                                getattr(param_doc, "default", None)
                                or get_code(param_node.default)
                                or "-"
                            ),
                        )
                    )
                yield block.build()

        yield markdown_heading("Returns", level=context.depth + 1)
        with markdown_block() as block:
            if doc:
                returns_doc = doc.returns
            else:
                returns_doc = None

            block.writeln("| Type | Description |")
            block.writeln("| ---- | ----------- |")
            block.writeln(
                "| {type} | {description} |".format(
                    type=(
                        getattr(returns_doc, "type_name", None)
                        or get_code(func_node.annotation)
                        or "-"
                    ),
                    description=getattr(returns_doc, "description", None) or "-",
                )
            )
            yield block.build()

        if doc and doc.long_description:
            yield markdown_heading("Details", level=context.depth + 1)
            yield markdown_paragraph(doc.long_description)


def find_symbol(module: Optional[Module], path: str) -> Optional[Scope]:
    current_node = cast(Optional[Scope], module)

    for part in path.split("."):
        child: Scope
        for child in iter_children(current_node):
            name: Optional[Name] = getattr(child, "name", None)
            if name is not None and name.value == part:
                current_node = child
                break
        else:
            return None

    return current_node


def iter_children(node: Optional[Scope]) -> Generator[Scope, None, None]:
    if node is None:
        return

    for child in node.children:
        if type(child) is PythonNode:
            yield from iter_children(child)
        else:
            yield child


def get_code(node: Optional[Scope]):
    if node is None:
        return None

    return node.get_code()


def isnode(node: Optional[Scope], node_cls: Type[Scope]):
    if node is None:
        return False

    return node.type == node_cls.type

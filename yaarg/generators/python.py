from typing import Optional

import schema
from parso.grammar import load_grammar
from parso.python.tree import Module, Name, PythonNode, Scope

from .base import BaseGenerator


class PythonGenerator(BaseGenerator):
    name = "python"
    options_schema = schema.Schema(
        {
            schema.Optional("version", default=None): str,
            schema.Optional("encoding", default="utf-8"): str,
        }
    )

    def generate(self, filepath, symbol, options):
        grammar = load_grammar(version=options["version"])
        with open(filepath, encoding=options["encoding"]) as f:
            parser = grammar.parse(f.read())
            module: Module = parser.get_root_node()

        if symbol is not None:
            node = get_symbol(module, symbol)
        else:
            node = module

        print(node.get_doc_node())
        return ""


def get_symbol(module: Module, path: str) -> Optional[Scope]:
    current_node: Scope = module

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


def iter_children(node: Scope):
    for child in node.children:
        if type(child) is PythonNode:
            yield from iter_children(child)
        else:
            yield child

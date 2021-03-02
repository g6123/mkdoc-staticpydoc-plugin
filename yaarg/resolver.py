from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Dict, Sequence, Tuple, Type

from mkdocs.config import Config as MKDocsConfig

from yaarg.generators.base import BaseGenerator

__all__ = ["Resolver", "ResolverConfig", "ResolverError"]


@dataclass
class ResolverRule:
    glob: str
    generator: str
    options: dict


class ResolverError(Exception):
    pass


class Resolver:
    """
    Initializes an appropriate generator instance for the given filepath.
    """

    rules: Sequence[ResolverRule]
    generator_caches: Dict[str, BaseGenerator]

    def __init__(self, rules: Sequence[ResolverRule], mkdocs: MKDocsConfig):
        self.rules = rules
        self.generator_caches = {}
        self.mkdocs = mkdocs

    def resolve(self, filepath: Path, options: dict) -> Tuple[BaseGenerator, dict]:
        options = options.copy()
        generator_path = options.pop("generator", None)

        if generator_path is None:
            for rule in self.rules:
                if self.match(filepath, rule, options):
                    generator_path = rule.generator
                    options.update(rule.options)
                    break
            else:
                raise ResolverError(filepath)

        if generator_path not in self.generator_caches:
            generator_cls: Type[BaseGenerator] = import_string(generator_path)
            self.generator_caches[generator_path] = generator_cls(self.mkdocs)

        generator = self.generator_caches[generator_path]
        options = generator.validate_options(options)
        return generator, options

    def match(self, filepath: Path, rule: ResolverRule, options: dict) -> bool:
        return filepath.match(rule.glob)


def import_string(path):
    module_name, obj_name = path.rsplit(":", 1)
    module = import_module(module_name)
    try:
        return getattr(module, obj_name)
    except AttributeError:
        raise ImportError(path)

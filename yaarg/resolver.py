import sys
from fnmatch import fnmatch
from importlib import import_module
from pathlib import Path
from typing import Sequence, Tuple, Type

from yaarg.generators.base import BaseGenerator

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict


class ResolverConfig(TypedDict):
    glob: str
    generator: str
    options: dict


class ResolverError(Exception):
    pass


class Resolver:
    def __init__(self, configs: Sequence[ResolverConfig]):
        self.configs = configs

    def resolve(self, filepath: Path, options: dict) -> Tuple[BaseGenerator, dict]:
        options = options.copy()
        generator_path = options.pop("generator", None)

        if generator_path is None:
            for config in self.configs:
                if self.match(filepath, config, options):
                    generator_path = config["generator"]
                    options.update(config["options"])
                    break
            else:
                raise ResolverError(filepath)

        generator_cls: Type[BaseGenerator] = import_string(generator_path)
        generator = generator_cls()
        options = generator.validate_options(options)

        return generator, options

    def match(self, filepath: Path, config: ResolverConfig, options: dict) -> bool:
        return fnmatch(str(filepath), config["glob"])


def import_string(path):
    module_name, obj_name = path.rsplit(".", 1)
    module = import_module(module_name)
    try:
        return getattr(module, obj_name)
    except AttributeError:
        raise ImportError(path)

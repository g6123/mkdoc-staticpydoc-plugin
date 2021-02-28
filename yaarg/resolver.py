import sys
from fnmatch import fnmatch
from importlib import import_module
from pathlib import Path
from typing import Dict, Sequence, Tuple, Type

from yaarg.generators.base import BaseGenerator

if sys.version_info >= (3, 8):
    from typing import TypedDict
else:
    from typing_extensions import TypedDict

__all__ = ["Resolver", "ResolverConfig", "ResolverError"]


class ResolverConfig(TypedDict):
    glob: str
    generator: str
    options: dict


class ResolverError(Exception):
    pass


class Resolver:
    """
    Initializes an appropriate generator instance for the given filepath.
    """

    _configs: Sequence[ResolverConfig]
    _generator_caches: Dict[str, BaseGenerator]

    def __init__(self, configs: Sequence[ResolverConfig]):
        self._configs = configs
        self._generator_caches = {}

    def resolve(self, filepath: Path, options: dict) -> Tuple[BaseGenerator, dict]:
        options = options.copy()
        generator_path = options.pop("generator", None)

        if generator_path is None:
            for config in self._configs:
                if self.match(filepath, config, options):
                    generator_path = config["generator"]
                    options.update(config["options"])
                    break
            else:
                raise ResolverError(filepath)

        if generator_path in self._generator_caches:
            generator = self._generator_caches[generator_path]
        else:
            generator_cls: Type[BaseGenerator] = import_string(generator_path)
            generator = self._generator_caches[generator_path] = generator_cls()

        options = generator.validate_options(options)
        return generator, options

    def match(self, filepath: Path, config: ResolverConfig, options: dict) -> bool:
        return fnmatch(str(filepath), config["glob"])


def import_string(path):
    module_name, obj_name = path.rsplit(":", 1)
    module = import_module(module_name)
    try:
        return getattr(module, obj_name)
    except AttributeError:
        raise ImportError(path)

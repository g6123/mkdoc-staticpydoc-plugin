from itertools import chain

from mkdocs.config import Config
from mkdocs.config.config_options import ConfigItems, Type
from mkdocs.plugins import BasePlugin

from yaarg.markdown import YaargExtension
from yaarg.resolver import Resolver, ResolverRule


class YaargPlugin(BasePlugin):
    config_scheme = (
        (
            "resolver",
            ConfigItems(
                ("glob", Type(str)),
                ("generator", Type(str)),
                ("options", Type(dict, default={})),
            ),
        ),
    )
    default_resolver_configs = (
        {
            "glob": "*.py",
            "generator": "yaarg.generators.parso:ParsoGenerator",
            "options": {},
        },
        {
            "glob": "*.[jt]s?",
            "generator": "yaarg.generators.jsdoc:JSDocGenerator",
            "options": {},
        },
    )

    def load_config(self, options, config_file_path=None):
        result = super().load_config(options, config_file_path)
        self.config["resolver"] = list(
            ResolverRule(**config)
            for config in chain(self.config["resolver"], self.default_resolver_configs)
        )
        return result

    def on_config(self, config: Config, **kwargs) -> Config:
        resolver = Resolver(rules=self.config["resolver"], mkdocs=config)
        extension = YaargExtension(resolver, mkdocs=config)
        config["markdown_extensions"].append(extension)
        return config

from mkdocs.config import Config
from mkdocs.config.config_options import ConfigItems, Type
from mkdocs.plugins import BasePlugin

from yaarg.markdown import YaargExtension
from yaarg.resolver import Resolver


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
            "generator": "yaarg.generators.parso.ParsoGenerator",
            "options": {},
        },
        {
            "glob": "*.[jt]s?",
            "generator": "yaarg.generators.jsdoc.JSDocGenerator",
            "options": {},
        },
    )

    def load_config(self, options, config_file_path=None):
        result = super().load_config(options, config_file_path)
        self.config["resolver"] = Resolver(
            tuple(self.config["resolver"]) + self.default_resolver_configs
        )
        return result

    def on_config(self, config: Config, **kwargs) -> Config:
        config["markdown_extensions"].append(
            YaargExtension(resolver=self.config["resolver"])
        )
        return config

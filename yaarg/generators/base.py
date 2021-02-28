from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from schema import Schema


class BaseGenerator(ABC):
    """
    Base class for the all yaarg generators.
    """
    options_schema = Schema({})

    def validate_options(self, options: dict) -> dict:
        """
        Validates generator options.
        The result is used as `options` parameter for `generate()` method.

        Args:
            options (dict): Raw options from markdown

        Returns:
            dict: Validated options
        """
        return self.options_schema.validate(options)

    @abstractmethod
    def generate(self, filepath: Path, symbol: Optional[str], options: dict) -> str:
        """
        Reads the source code and generates markdown contents

        Args:
            filepath (Path): Path to the source code
            symbol (Optional[str]): Symbol name
            options (dict): Generator options. See also `validate_options()`.

        Returns:
            str: Markdown contents
        """
        pass

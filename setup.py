import os
import re
from collections import defaultdict

from setuptools import find_packages, setup


def resolve(filename):
    return os.path.join(os.path.dirname(__file__), filename)


with open(resolve("yaarg/__init__.py")) as f:
    version_pattern = re.compile(r'__version__ = [\'"](.+?)[\'"]')
    version_match = re.search(version_pattern, f.read())
    assert version_match is not None
    version = version_match.group(1)


with open(resolve("requirements/base.txt")) as f:
    install_requires = list(map(str.strip, f.readlines()))


with open(resolve("requirements/extra.txt")) as f:
    extras_pattern = re.compile(r"^(.+?)\s*#\s*extra\s*=\s*(.+?)$")
    extra_requires = defaultdict(list)

    for line in f:
        match = re.match(extras_pattern, line)
        if match is not None:
            extra_requires[match.group(2)].append(match.group(1))

setup(
    name="mkdocs-yaarg-plugin",
    version=version,
    url="https://github.com/g6123/mkdocs-yaarg-plugin",
    license="MIT",
    description="Yet Another API Reference Generator plugin for MKDocs.",
    author="g6123",
    author_email="gg6123@naver.com",
    packages=find_packages(exclude=("tests",)),
    install_requires=install_requires,
    extras_require=extra_requires,
    python_requires=">=3.6",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
    ],
    entry_points={
        "mkdocs.plugins": [
            "yaarg = yaarg:YaargPlugin",
        ]
    },
)

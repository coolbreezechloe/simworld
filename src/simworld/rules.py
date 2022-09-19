from dataclasses import dataclass
import pathlib
import json
from typing import Callable


TileIndex = int
Direction = str
Rule = Callable

@dataclass
class Rules():
    """This class is a handy tool for dealing with tilesets in 2D games"""
    rules: dict[TileIndex, list[tuple[Direction, Rule]]]
    name: str


def load_rules(search_locations: list[pathlib.Path]) -> list[Rules]:
    """Returns a Rules objects derived from the input files

    The function takes a list of Path objects representing individual rules
    files for a format:

    NNNN-rules.json

    Where NNNN is the name of the corresponding tileset.

    """
    result = list()
    for path in search_locations:
        if path.name.endswith('-rules.json'):
            rules = json.load(open(path.absolute()))
            result.append(Rules(rules, path.name.split('-')[0]))
    return result

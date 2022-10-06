from dataclasses import dataclass
import pathlib
import json
from typing import Callable


TileIndex = int
Direction = str
AvailableOptions = set[TileIndex]

@dataclass
class Rules():
    """This class is a handy tool for dealing with tilesets in 2D games"""
    rules: dict[TileIndex, dict[Direction,  AvailableOptions]]
    name: str
    author: str
    error_tile: TileIndex
    file_name: str
    width: int
    height: int

    def __post_init__(self):
        for k in list(self.rules.keys()):
            # In the JSON dictionary keys must be strings but in our model
            # we let the keys be their integer values.
            r = self.rules[k]
            self.rules[int(k)] = r
            del self.rules[k]
            for d in r.keys():
                # in JSON there is no concept of a set structure, only lists
                 # so we must manually convert.
                r[d] = set(r[d])

    def get_rule_by_index(self, index: TileIndex) -> dict[Direction, AvailableOptions]:
        return self.rules.get(index, dict())


def load_rules(rule_file: pathlib.Path) -> Rules:
    """Returns a Rules objects derived from the input file
    """
    rule_spec = json.load(open(rule_file.absolute()))
    name = rule_spec['Name']
    author = rule_spec['Author']
    error_tile = rule_spec['ErrorTile']
    file_name = rule_spec['FileName']
    rules = rule_spec['Rules']
    width = rule_spec['TileWidth']
    height = rule_spec['TileHeight']

    return Rules(rules, name, author, error_tile, file_name, width, height)

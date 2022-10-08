from dataclasses import dataclass
import pathlib
import json
from typing import Callable


TileIndex = int
Direction = str
AvailableOptions = set[TileIndex]
TileDefinition = dict


@dataclass
class Rules():
    """This class is a handy tool for dealing with tilesets in 2D games"""
    name: str
    author: str
    file_name: str
    tile_width: int
    tile_height: int
    error_tile: TileIndex
    tiles: dict[TileIndex, TileDefinition]

    def __post_init__(self):
        result = dict()
        for d in self.tiles:
            i = d['Index']  # type: ignore
            result[i] = d
            for dir, items in result[i]['Rules'].items():
                result[i]['Rules'][dir] = set(items)
        self.tiles = result

    def get_rule_by_index(self, index: TileIndex) -> dict[Direction, AvailableOptions]:
        return self.tiles.get(index, dict())


def load_rules(rule_file: pathlib.Path) -> Rules:
    """Returns a Rules objects derived from the input file
    """
    rule_spec = json.load(open(rule_file.absolute()))
    name = rule_spec['Name']
    author = rule_spec['Author']
    file_name = rule_spec['FileName']
    tile_width = rule_spec['TileWidth']
    tile_height = rule_spec['TileHeight']
    error_tile = rule_spec['ErrorTile']
    tiles = rule_spec['Tiles']

    rules = Rules(name, author, file_name, tile_width, tile_height, error_tile, tiles)
    return rules

# simworld Copyright (C) 2024 Chloe Beelby
from dataclasses import dataclass, field
import pathlib
import json


TileIndex = int
Direction = str
AvailableOptions = set[TileIndex]

@dataclass
class TileDefinition():
    """Container for information about a single tile"""
    name: str
    index: int
    rules: dict[Direction, AvailableOptions]

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
    all_indexes: set[TileIndex] = field(init=False)

    def __post_init__(self):
        result = dict()
        all_indexes = set()
        for td in self.tiles:
            index = int(td['Index']) # type: ignore
            all_indexes.add(index)
            td = TileDefinition(td['Name'], td['Index'], td['Rules']) # type: ignore
            for direction, items in td.rules.items():
                td.rules[direction] = set(items)
            result[index] = td
        self.tiles = result
        self.all_indexes = all_indexes

    def get_rule_by_index(self, index: TileIndex) -> dict[Direction, AvailableOptions]:
        result = self.tiles[index]
        return result.rules


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

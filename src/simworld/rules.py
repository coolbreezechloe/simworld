# simworld Copyright (C) 2024 Chloe Beelby
from dataclasses import dataclass, field
import pathlib
import json


TileName = str
TileIndex = int
Direction = str
AvailableOptions = set[TileIndex]


@dataclass
class TileDefinition():
    """Container for information about a single tile"""
    name: TileName
    index: TileIndex
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
        self.all_indexes = set(self.tiles.keys())

    def get_rule_by_index(self, index: TileIndex) -> dict[Direction, AvailableOptions]:
        result = self.tiles[index]
        return result.rules


def load_rules_from_json(rule_file: pathlib.Path) -> Rules:
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

    result = dict()
    for td in tiles:
        tile_index = int(td['Index']) # type: ignore
        tile_name = str(td['Name']) # type: ignore
        tile_rules = td['Rules'] # type: ignore
        if tile_rules is None:
            tile_rules = dict()
        td = TileDefinition(tile_name, tile_index, tile_rules)
        for direction, items in td.rules.items():
            # Because JSON does not have a concept of a set, the rules are stored as lists
            # this re-casts them to a set, which also removes duplicates if there are any
            td.rules[direction] = set(items)
        result[tile_index] = td
    
    tiles = result

    rules = Rules(name, author, file_name, tile_width, tile_height, error_tile, tiles)
    return rules

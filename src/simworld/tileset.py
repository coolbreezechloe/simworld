from dataclasses import dataclass
import pathlib
import pygame as pg
from pygame import Surface
from simworld.rules import TileIndex, Rules

Row = int
Column = int
Tile = Surface
Coordinate = tuple[Column, Row]

@dataclass
class TileSet():
    """This class is a handy tool for dealing with tilesets in 2D games"""
    tiles: dict[Coordinate, Tile]
    tile_width: int
    tile_height: int
    cols: int
    rows: int
    name: str

    def get_tile_by_index(self, index: TileIndex) -> Tile:
        """Get a tile from the complete set of tiles using a 1-based index

        For example if the source file contained 100 tiles (perhaps arranged
        into 10 rows of 10) then you could access them by counting left-to-right
        and top-to-bottom. This is an alternative to selecting a tile by its
        location using something like tiles[(col, row)]
        """

        if index < 1 or index > len(self.tiles):
            raise ValueError(f"Index of {index} is out of bounds (1-{len(self.tiles)})")

        column = ((index - 1) % self.cols)
        row = ((index - 1) // self.cols)
        return self.tiles[(column, row)]

def load_tileset(file_location: pathlib.Path, rule_set: Rules) -> TileSet:
    """Returns a TileSet object based on the supplied RuleSet
    """
    name = rule_set.name
    width = rule_set.width
    height = rule_set.height
    return split_tiles(pg.image.load(file_location), width, height, name)

def split_tiles(tileset: Surface, tile_width: int, tile_height: int, name: str) -> TileSet:
    """Split a surface into subsurfaces for each tile in the set

    This function assumes you have one large surface which is a representation
    of a grid of small tiles that you want to be able to address individually.
    This function will take the original surface along with the tile size and
    a name for the tileset and parse the image into a series of subsurfaces
    indexed by their location (column, row) in the source image.
    """
    tiles = dict()
    width, height = tileset.get_size()
    rows = int(height / tile_height)
    cols = int(width / tile_width)
    for c in range(cols):
        for r in range(rows):
            tiles[(c, r)] = tileset.subsurface(
                c*tile_width, r*tile_height, tile_width, tile_height)
    t = TileSet(tiles, tile_width, tile_height, cols, rows, name)
    return t


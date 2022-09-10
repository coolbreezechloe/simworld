from dataclasses import dataclass
import pathlib
import pygame as pg
from pygame import Surface

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

    def get_tile_by_index(self, index: int) -> Tile:
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

def load_tilesets(search_locations: list[pathlib.Path]) -> list[TileSet]:
    """Returns a list of TileSet objects derived from the input files

    The function takes a list of Path objects representing individual PNG
    files with a name of the format:

    NNNN-WWWxHHH.PNG

    Where NNNN is the name of the image, WWW and HHH are the width and
    height of the individual tiles (in pixels) contained in the image.

    The function will return a list of all such files found in the folder
    in the form of TileSet entries which will include relevant details like
    the source file name, the images themselves, and the size of the images.
    """
    result = list()
    for path in search_locations:
        name, size = path.name.split('-')
        width, height = [int(x) for x in size.strip('.png').split('x')]
        t = split_tiles(pg.image.load(path), width, height, name)
        result.append(t)
    return result

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


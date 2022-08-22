from dataclasses import dataclass
import pathlib
import pygame as pg
from pygame import Surface

TileSetName = str
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

    def get_tile_by_index(self, index: int) -> Tile:
        """Index into the complete set of tiles using a single 1-based interger value"""

        if index < 1 or index > len(self.tiles):
            raise ValueError(f"Index of {index} is out of bounds (1-{len(self.tiles)})")
        
        column = (index % self.cols) - 1
        row = (index // self.cols) - 1
        return self.tiles[(column, row)]

def get_tilesets() -> dict[TileSetName, TileSet]:
    """Returns a dictionary which maps png files to their data
    
    The function searches the directory this file is in for all PNG
    files and assumes that such files have a name in the format

    NNNN-WWWxHHH.PNG

    Where NNNN is the name of the image, WWW and HHH are the width and
    height of the individual tiles (in pixels) contained in the image.

    The function will return a map with the keys being TileMapName values
    corresponding to the NNNN part of the file. In this map the keys are
    a TileMap representing the data in the file.
    """
    tilemaps = dict()
    for p in pathlib.Path(__file__).parent.glob('*.png'):
        name, size = p.name.split('-')
        width, height = [int(x) for x in size.strip('.png').split('x')]
        tilemaps[name] = split_tiles(pg.image.load(p), width, height)        
    return tilemaps    

def split_tiles(tilemap: Surface, tile_width: int, tile_height: int) -> TileSet:
    """Given a Surface and a tile size it will split the surface into a subsurfaces for each tile"""
    tiles = dict()
    width, height = tilemap.get_size()
    rows = int(height / tile_height)
    cols = int(width / tile_width)    
    for c in range(cols):
        for r in range(rows):
            tiles[(c, r)] = tilemap.subsurface(c*tile_width, r*tile_height, tile_width, tile_height)
    t = TileSet(tiles, tile_width, tile_height, cols, rows)
    return t

def show_all():
    from simworld.tilemapbrowser import TileMapBrowser
    for _, tilemap in get_tilesets().items():
        t = TileMapBrowser(tilemap)
        t.run()


if __name__ == '__main__':
    show_all()
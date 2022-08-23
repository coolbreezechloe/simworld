import sys
import pygame as pg
from pygame.time import Clock

from simworld.tilemap import TileSet, get_tilesets

class TileSetBrowser():
    def __init__(self, tileset: TileSet):
        self.tileset = tileset
        self.width = 800
        self.height = 600
        self._setup_pygame()

    def _setup_pygame(self):
        r = pg.init()
        print(f"pg.init() returned {r}")
        surface = pg.display.set_mode((self.width, self.height), flags=pg.RESIZABLE | pg.SCALED)
        print(f"created surface: {surface}")
        pg.display.set_caption(self.tileset.name)
        self.surface = surface    

    def run(self): 
        clock = Clock()       
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT: sys.exit()

            _black = (0, 0, 0)
            self.surface.fill(_black)
            for r in range(self.tileset.rows):
                for c in range(self.tileset.cols):                    
                    tile = self.tileset.tiles[(c, r)]
                    rec = tile.get_rect()
                    rec = rec.move([int(c*self.tileset.tile_width), int(r*self.tileset.tile_height)])
                    self.surface.blit(tile, rec)
            clock.tick(60)
            pg.display.flip()

def show_all():
    for tileset in get_tilesets():
        t = TileSetBrowser(tileset)
        t.run()


if __name__ == '__main__':
    show_all()
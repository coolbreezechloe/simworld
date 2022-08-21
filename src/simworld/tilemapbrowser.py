import random
import sys
import math
import pygame as pg
from pygame.time import Clock

from simworld.tilemap import TileSet

class TileMapBrowser():
    def __init__(self, tilemap: TileSet):
        self.tilemap = tilemap
        self.width = 800
        self.height = 600
        self._setup_pygame()

    def _setup_pygame(self):
        r = pg.init()
        print(f"pg.init() returned {r}")
        surface = pg.display.set_mode((self.width, self.height), flags=pg.RESIZABLE | pg.SCALED)
        print(f"created surface: {surface}")
        self.surface = surface    

    def run(self): 
        clock = Clock()       
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT: sys.exit()

            _black = (0, 0, 0)
            self.surface.fill(_black)
            for r in range(self.tilemap.rows):
                for c in range(self.tilemap.cols):                    
                    tile = self.tilemap.tiles[(c, r)]
                    rec = tile.get_rect()
                    rec = rec.move([int(c*self.tilemap.tile_width), int(r*self.tilemap.tile_height)])
                    self.surface.blit(tile, rec)
            clock.tick(60)
            pg.display.flip()
                            
    

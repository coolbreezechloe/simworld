import pygame as pg
from pygame.time import Clock
import logging

from simworld.tileset import TileSet, get_tilesets

log = logging.getLogger(__name__)

class TileSetBrowser():
    def __init__(self, tileset: TileSet):
        self.tileset = tileset
        self.width = 800
        self.height = 600
        self._setup_pygame()
        self._setup_state()

    def _setup_pygame(self):
        r = pg.init()
        log.info(f"pg.init() returned {r}")
        surface = pg.display.set_mode((self.width, self.height))
        log.info(f"created surface: {surface}")
        pg.display.set_caption(self.tileset.name)
        self.surface = surface

    def _setup_state(self):
        self.quit = False
        self.view_x = 0
        self.view_x_delta = 0
        self.view_y = 0
        self.view_y_delta = 0
        self.view_width = 10
        self.view_height = 10
        self.selected_col = self.view_width // 2
        self.selected_row = self.view_height // 2

    def _handle_events(self) -> None:
        while not self.quit:
            events = pg.event.get()
            if not events:
                return
            for event in events:
                log.debug(f'next event is {event}')
                if event.type == pg.QUIT:
                    self.quit = True
                    break
                elif event.type == pg.KEYDOWN:
                    self._handle_keydown(event.key)

    def _handle_keydown(self, key) -> None:
        if key == pg.K_LEFT and self.view_x > 0:
            self.view_x = self.view_x - 1
        elif key == pg.K_RIGHT and self.view_x < self.tileset.cols - self.view_width:
            self.view_x = self.view_x + 1
        elif key == pg.K_UP and self.view_y > 0:
            self.view_y = self.view_y - 1
        elif key == pg.K_DOWN and self.view_y < self.tileset.rows - self.view_height:
            self.view_y = self.view_y + 1
        elif key == pg.K_ESCAPE:
            self.view_x = 0
            self.view_y = 0
        elif key == pg.K_q:
            self.quit = True

    def _update_screen(self):
        _black = (0, 0, 0)
        _white = (255, 255, 255)
        self.surface.fill(_black)
        rows = min(self.view_height, self.tileset.rows)
        cols = min(self.view_width, self.tileset.cols)
        for r in range(rows):
            for c in range(cols):
                tile = self.tileset.tiles[(self.view_x + c, self.view_y + r)]
                rec = tile.get_rect()
                rec = rec.move([int(c*self.tileset.tile_width), int(r*self.tileset.tile_height)])
                self.surface.blit(tile, rec)
        x0 = int(self.selected_col * self.tileset.tile_width)
        y0 = int(self.selected_row * self.tileset.tile_height)
        pg.draw.rect(self.surface, _white, (x0, y0, self.tileset.tile_width, self.tileset.tile_height), width=1)

    def run(self):
        clock = Clock()
        while self.quit is False:
            self._update_screen()
            clock.tick(60)
            pg.display.flip()
            self._handle_events()
        log.debug('Quitting')


def show_all():
    for tileset in get_tilesets():
        t = TileSetBrowser(tileset)
        t.run()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    show_all()
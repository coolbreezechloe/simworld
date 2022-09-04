import pygame as pg
import pygame.freetype
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
        pygame.freetype.init()
        r = pg.init()
        log.debug(f"pg.init() returned {r}")
        surface = pg.display.set_mode((self.width, self.height))
        log.debug(f"created surface: {surface}")
        pg.display.set_caption(f"TileSet Browser : {self.tileset.name}")
        self.surface = surface

    def _setup_state(self):
        self.quit = False
        self.view_x = 0
        self.view_x_delta = 0
        self.view_y = 0
        self.view_y_delta = 0
        self.view_width = 10
        self.view_height = 10
        self.selected_tile = None
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
        if key == pg.K_LEFT or key == pg.K_a:
            if self.view_x > 0:
                self.view_x = self.view_x - 1
        elif key == pg.K_RIGHT or key == pg.K_d:
            if self.view_x < self.tileset.cols - self.view_width:
                self.view_x = self.view_x + 1
        elif key == pg.K_UP or key == pg.K_w:
            if self.view_y > 0:
                self.view_y = self.view_y - 1
        elif key == pg.K_DOWN or key == pg.K_s:
            if self.view_y < self.tileset.rows - self.view_height:
                self.view_y = self.view_y + 1
        elif key == pg.K_g:
            self.view_x = 0
            self.view_y = 0
        elif key == pg.K_j:
            if self.selected_row < self.view_height - 1:
                self.selected_row = self.selected_row + 1
            elif self.selected_row == self.view_height - 1 and self.view_y < self.tileset.rows - self.view_height:
                self.view_y = self.view_y + 1
        elif key == pg.K_k:
            if self.selected_row > 0:
                self.selected_row = self.selected_row - 1
            elif self.selected_row == 0 and self.view_y > 0:
                self.view_y = self.view_y - 1
        elif key == pg.K_l:
            if self.selected_col < self.view_width - 1:
                self.selected_col = self.selected_col + 1
            elif self.selected_col == self.view_width - 1 and self.view_x < self.tileset.cols - self.view_width:
                self.view_x = self.view_x + 1
        elif key == pg.K_h:
            if self.selected_col > 0:
                self.selected_col = self.selected_col - 1
            elif self.selected_col == 0 and self.view_x > 0:
                self.view_x = self.view_x - 1
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
                if r == self.selected_row and c == self.selected_col:
                    self.selected_tile = (self.view_x + self.selected_col, self.view_y + self.selected_row)
                    rec2 = tile.get_rect().move([int(self.view_width*self.tileset.tile_width + self.tileset.tile_width), 0])
                    tile2 = pg.transform.scale(tile, (rec.width*2, rec.height*2))
                    self.surface.blit(tile2, rec2)
                    rec4 = rec2.move([int(self.tileset.tile_width * 2 + self.tileset.tile_width), 0])
                    tile4 = pg.transform.scale(tile, (rec.width*4, rec.height*4))
                    self.surface.blit(tile4, rec4)
        x0 = int(self.selected_col * self.tileset.tile_width)
        y0 = int(self.selected_row * self.tileset.tile_height)
        pg.draw.rect(self.surface, _white, (x0, y0, self.tileset.tile_width, self.tileset.tile_height), width=1)
        font = pygame.freetype.Font(None, size=25)
        if self.selected_tile:
            font.render_to(self.surface,
            (self.tileset.tile_width*self.view_width + self.tileset.tile_width, self.tileset.tile_height*self.view_height + self.tileset.tile_height),
            f"Selected Tile = {self.selected_tile}",
            fgcolor=_white)

    def run(self):
        clock = Clock()
        while self.quit is False:
            self._update_screen()
            pg.display.flip()
            clock.tick(60)
            self._handle_events()
        log.debug('Quitting')


def show_all():
    for tileset in get_tilesets():
        t = TileSetBrowser(tileset)
        t.run()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    show_all()
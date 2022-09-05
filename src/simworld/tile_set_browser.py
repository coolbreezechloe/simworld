import pygame
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
        r = pygame.init()
        log.debug(f"pygame.init() returned {r}")
        surface = pygame.display.set_mode((self.width, self.height))
        log.debug(f"created surface: {surface}")
        pygame.display.set_caption(f"TileSet Browser : {self.tileset.name}")
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
        self.tile_width = self.tileset.tile_width
        self.tile_height = self.tileset.tile_height

    def _handle_events(self) -> None:
        while not self.quit:
            events = pygame.event.get()
            if not events:
                return
            for event in events:
                log.debug(f'next event is {event}')
                if event.type == pygame.QUIT:
                    self.quit = True
                    break
                elif event.type == pygame.KEYDOWN:
                    self._handle_keydown(event.key)

    def _handle_keydown(self, key) -> None:
        if key == pygame.K_LEFT or key == pygame.K_a:
            if self.view_x > 0:
                self.view_x = self.view_x - 1
        elif key == pygame.K_RIGHT or key == pygame.K_d:
            if self.view_x < self.tileset.cols - self.view_width:
                self.view_x = self.view_x + 1
        elif key == pygame.K_UP or key == pygame.K_w:
            if self.view_y > 0:
                self.view_y = self.view_y - 1
        elif key == pygame.K_DOWN or key == pygame.K_s:
            if self.view_y < self.tileset.rows - self.view_height:
                self.view_y = self.view_y + 1
        elif key == pygame.K_g:
            self.view_x = 0
            self.view_y = 0
            self.selected_row = 0
            self.selected_col = 0
        elif key == pygame.K_j:
            if self.selected_row < self.view_height - 1:
                self.selected_row = self.selected_row + 1
            elif self.selected_row == self.view_height - 1 and self.view_y < self.tileset.rows - self.view_height:
                self.view_y = self.view_y + 1
        elif key == pygame.K_k:
            if self.selected_row > 0:
                self.selected_row = self.selected_row - 1
            elif self.selected_row == 0 and self.view_y > 0:
                self.view_y = self.view_y - 1
        elif key == pygame.K_l:
            if self.selected_col < self.view_width - 1:
                self.selected_col = self.selected_col + 1
            elif self.selected_col == self.view_width - 1 and self.view_x < self.tileset.cols - self.view_width:
                self.view_x = self.view_x + 1
        elif key == pygame.K_h:
            if self.selected_col > 0:
                self.selected_col = self.selected_col - 1
            elif self.selected_col == 0 and self.view_x > 0:
                self.view_x = self.view_x - 1
        elif key == pygame.K_q:
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
                rec = rec.move([int(c*self.tile_width),
                               int(r*self.tile_height)])
                self.surface.blit(tile, rec)
                if r == self.selected_row and c == self.selected_col:
                    self.selected_tile = (
                        self.view_x + self.selected_col, self.view_y + self.selected_row)
                    rec2 = tile.get_rect().move(
                        [int(self.view_width*self.tile_width + self.tile_width), 0])
                    tile2 = pygame.transform.scale(
                        tile, (rec.width*2, rec.height*2))
                    self.surface.blit(tile2, rec2)
                    rec4 = rec2.move(
                        [int(self.tile_width * 2 + self.tile_width), 0])
                    tile4 = pygame.transform.scale(
                        tile, (rec.width*4, rec.height*4))
                    self.surface.blit(tile4, rec4)
        x0 = int(self.selected_col * self.tile_width)
        y0 = int(self.selected_row * self.tile_height)
        pygame.draw.rect(self.surface, _white, (x0, y0,
                         self.tile_width, self.tile_height), width=1)
        font = pygame.freetype.SysFont(None, size=25)
        if self.selected_tile:
            font.render_to(self.surface,
                           (self.tile_width*self.view_width + self.tile_width,
                            self.tile_height*self.view_height + self.tile_height),
                           f"Selected Tile = {self.selected_tile}",
                           fgcolor=_white)

    def run(self):
        clock = Clock()
        while self.quit is False:
            self._update_screen()
            pygame.display.flip()
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

# simworld Copyright (C) 2024 Chloe Beelby
from email.mime import base
import pathlib
import pygame
import pygame.freetype
from pygame.time import Clock
import logging

from simworld.tileset import Coordinate, TileSet, load_tileset
from simworld.rules import load_rules_from_json

log = logging.getLogger(__name__)

_black = (0, 0, 0)
_white = (255, 255, 255)


class TilesetBrowser():
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
        self.view_width = 5
        self.view_height = 5
        self.selected_tile: Coordinate = (0, 0)
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
                    if not event.unicode:
                        self._handle_keydown(event.key)
                elif event.type == pygame.TEXTINPUT:
                    self._handle_textinput(event.text)
    
    def _handle_textinput(self, text):
        if text == 'k':
            if self.selected_row > 0:
                self.selected_row = self.selected_row - 1
            elif self.selected_row == 0 and self.view_y > 0:
                self.view_y = self.view_y - 1
        elif text == 'q':
            self.quit = True
        elif text == 'g':
            self.view_x = 0
            self.view_y = 0
            self.selected_row = 0
            self.selected_col = 0
        elif text == 'j':
            if self.selected_row < self.view_height - 1:
                self.selected_row = self.selected_row + 1
            elif (self.selected_row == self.view_height - 1 and
                  self.view_y < self.tileset.rows - self.view_height):
                self.view_y = self.view_y + 1
        elif text == 'k':
            if self.selected_row > 0:
                self.selected_row = self.selected_row - 1
            elif self.selected_row == 0 and self.view_y > 0:
                self.view_y = self.view_y - 1
        elif text == 'l':
            if self.selected_col < self.view_width - 1:
                self.selected_col = self.selected_col + 1
            elif (self.selected_col == self.view_width - 1 and
                  self.view_x < self.tileset.cols - self.view_width):
                self.view_x = self.view_x + 1
        elif text == 'h':
            if self.selected_col > 0:
                self.selected_col = self.selected_col - 1
            elif self.selected_col == 0 and self.view_x > 0:
                self.view_x = self.view_x - 1
        elif text == 'a':
            if self.view_x > 0:
                self.view_x = self.view_x - 1
        elif text == 'd':
            if self.view_x < self.tileset.cols - self.view_width:
                self.view_x = self.view_x + 1
        elif text == 'w':
            if self.view_y > 0:
                self.view_y = self.view_y - 1
        elif text == 's':
            if self.view_y < self.tileset.rows - self.view_height:
                self.view_y = self.view_y + 1
        

    def _handle_keydown(self, key) -> None:
        if key == pygame.K_LEFT:
            if self.view_x > 0:
                self.view_x = self.view_x - 1
        elif key == pygame.K_RIGHT:
            if self.view_x < self.tileset.cols - self.view_width:
                self.view_x = self.view_x + 1
        elif key == pygame.K_UP:
            if self.view_y > 0:
                self.view_y = self.view_y - 1
        elif key == pygame.K_DOWN:
            if self.view_y < self.tileset.rows - self.view_height:
                self.view_y = self.view_y + 1

    def _update_screen(self) -> None:
        self.surface.fill(_black)
        self._draw_view_area()

    def _draw_view_area(self) -> None:
        x = 10
        y = 10

        p = self._get_preview_surface()
        pr = p.get_rect().move(x, y)
        self.surface.blit(p, pr)

        d = self._get_double_surface()
        dr = d.get_rect().move(pr.topright).move(self.tile_width, 0)
        self.surface.blit(d, dr)

        q = self._get_quad_surface()
        qr = q.get_rect().move(dr.topright).move(self.tile_width, 0)
        self.surface.blit(q, qr)

        t, tr = self._get_selected_tile_surface()
        tr = tr.move(pr.bottomleft).move(0, self.tile_height)
        self.surface.blit(t, tr)
        pygame.draw.rect(self.surface, _white, tr, width=1)

    def _get_preview_surface(self) -> pygame.Surface:
        rows = min(self.view_height, self.tileset.rows)
        cols = min(self.view_width, self.tileset.cols)
        surface = pygame.Surface(
            (cols*self.tileset.tile_width, rows*self.tileset.tile_height))
        for r in range(rows):
            for c in range(cols):
                tile = self.tileset.tiles[(self.view_x + c, self.view_y + r)]
                rec = tile.get_rect()
                rec = rec.move([int(c*self.tile_width),
                               int(r*self.tile_height)])
                surface.blit(tile, rec)
                if r == self.selected_row and c == self.selected_col:
                    self.selected_tile = (
                        self.view_x + self.selected_col, self.view_y + self.selected_row)

        x0 = int(self.selected_col * self.tile_width)
        y0 = int(self.selected_row * self.tile_height)
        pygame.draw.rect(
            surface, _white, (x0, y0, self.tile_width, self.tile_height), width=1)
        pygame.draw.rect(
            surface, _white, (0, 0, surface.get_width(), surface.get_height()), width=1)
        return surface

    def _get_double_surface(self) -> pygame.Surface:
        surface = pygame.Surface((self.tile_width*2, self.tile_height*2))
        tile = self.tileset.tiles[self.selected_tile]
        tile2 = pygame.transform.scale(tile, (self.tile_width*2, self.tile_height*2))
        surface.blit(tile2, (0, 0))
        pygame.draw.rect(surface, _white, (0, 0, surface.get_width(), surface.get_height()), width=1)
        return surface
    
    def _get_quarter_surface(self) -> pygame.Surface:
        surface = pygame.Surface((self.tile_width*4, self.tile_height*4))
        tile = self.tileset.tiles[self.selected_tile]
        tile14 = pygame.transform.scale(tile, (self.tile_width*0.25, self.tile_height*0.25))
        surface.blit(tile14, (0, 0))
        pygame.draw.rect(surface, _white, (0, 0, surface.get_width(), surface.get_height()), width=1)
        return surface

    def _get_quad_surface(self) -> pygame.Surface:
        surface = pygame.Surface((self.tile_width*4, self.tile_height*4))
        tile = self.tileset.tiles[self.selected_tile]
        tile = pygame.transform.scale(tile, (self.tile_width*4, self.tile_height*4))
        surface.blit(tile, (0, 0))
        pygame.draw.rect(surface, _white, (0, 0, surface.get_width(), surface.get_height()), width=1)
        return surface

    def _get_selected_tile_surface(self) -> tuple[pygame.surface.Surface, pygame.rect.Rect]:
        font = pygame.freetype.SysFont(pygame.font.get_default_font(), size=25)
        index = 1 + self.selected_col + self.view_x + (self.selected_row + self.view_y) * self.tileset.cols
        surface, rect = font.render(f"Selected Tile = {self.selected_tile}, Tile Index = {index}", fgcolor=_white)
        return surface, rect

    def run(self):
        clock = Clock()
        while self.quit is False:
            self._update_screen()
            pygame.display.flip()
            clock.tick(60)
            self._handle_events()
        log.debug('Quitting')


def show_all():
    base_folder = pathlib.Path(__file__).parent.parent.parent / "assets"
    for r in pathlib.Path(base_folder / "rules").glob('*-rules.json'):
        rules = load_rules_from_json(r)
        tileset = load_tileset(base_folder / "tilesets" / rules.file_name, rules)
        TilesetBrowser(tileset).run()


if __name__ == '__main__':  # pragma: nocover
    logging.basicConfig(
        level=logging.DEBUG,
        style='{',
        format='{asctime}|{levelname}|{filename}:{lineno}|{message}',
        force=True
    )
    show_all()

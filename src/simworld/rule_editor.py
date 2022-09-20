import pathlib
import pygame
import pygame.freetype
from pygame.time import Clock
import logging
import random

from simworld.tileset import TileSet
from simworld.rules import Rules, load_rules
from simworld.tileset_browser import load_tilesets

log = logging.getLogger(__name__)

_black = (0, 0, 0)
_white = (255, 255, 255)


class ProbabilitySpace():
    def __init__(self, tileset: TileSet, rules: Rules):
        self.tileset = tileset
        self.width = 800
        self.height = 600
        self.rules = rules
        self._setup_pygame()
        self._setup_state()

    def _setup_pygame(self):
        pygame.freetype.init()
        r = pygame.init()
        log.debug(f"pygame.init() returned {r}")
        surface = pygame.display.set_mode((self.width, self.height))
        log.debug(f"created surface: {surface}")
        pygame.display.set_caption(
            f"Probability Space Reducer : {self.tileset.name}")
        self.surface = surface

    def _setup_state(self):
        self.current_state = dict()
        self.quit = False
        self.view_x = 0
        self.view_y = 0
        self.map_width = 100
        self.map_height = 100
        self.tile_width = self.tileset.tile_width
        self.tile_height = self.tileset.tile_height
        self.view_width = self.width // self.tile_width
        self.view_height = self.height // self.tile_height
        self._create_random_state()

    def _create_random_state(self) -> None:
        for c in range(self.map_width):
            for r in range(self.map_height):
                initial_state = [self.tileset.get_tile_by_index(
                    i) for i in [66, 98, 25, 75, 130, 97, 99, 161, 162, 163, 130]]
                self.current_state[(c, r)] = initial_state

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
        def left():
            if self.view_x > 0:
                self.view_x = self.view_x - 1

        def right():
            if self.view_x < self.map_width - self.view_width:
                self.view_x = self.view_x + 1

        def up():
            if self.view_y > 0:
                self.view_y = self.view_y - 1

        def down():
            if self.view_y < self.map_height - self.view_height:
                self.view_y = self.view_y + 1

        def origin():
            self.view_x = 0
            self.view_y = 0

        def quit():
            self.quit = True

        actions = {
            pygame.K_LEFT: left,
            pygame.K_a: left,
            pygame.K_h: left,
            pygame.K_j: down,
            pygame.K_RIGHT: right,
            pygame.K_d: right,
            pygame.K_l: right,
            pygame.K_UP: up,
            pygame.K_w: up,
            pygame.K_k: up,
            pygame.K_DOWN: down,
            pygame.K_s: down,
            pygame.K_g: origin,
            pygame.K_q: quit
        }

        if key in actions:
            actions[key]()

    def _update_screen(self) -> None:
        self.surface.fill(_black)
        self._draw_view_area()

    def _draw_view_area(self) -> None:
        surface = self._get_game_surface()
        rect = surface.get_rect()
        self.surface.blit(surface, rect)
        pygame.draw.rect(self.surface, _white, (0, 0, rect.width, rect.height), width=1)

    def _get_game_surface(self) -> pygame.Surface:
        rows = self.view_height
        cols = self.view_width
        surface = pygame.Surface(
            (cols*self.tileset.tile_width, rows*self.tileset.tile_height))
        for r in range(rows):
            for c in range(cols):
                pspace = self.current_state[(self.view_x + c, self.view_y + r)]
                if len(pspace) == 1:
                    tile = pspace[0]
                    rec = tile[0].get_rect()
                else:
                    font = pygame.freetype.SysFont(None, size=12)
                    tile, rec = font.render(f"|S|={len(pspace)}", fgcolor=_white)
                rec = rec.move([int(c*self.tile_width + 2), int(r*self.tile_height + 2)])
                surface.blit(tile, rec)

        pygame.draw.rect(
            surface, _white, (0, 0, surface.get_width(), surface.get_height()), width=1)
        return surface

    def run(self):
        clock = Clock()
        while self.quit is False:
            self._update_screen()
            pygame.display.flip()
            clock.tick(60)
            self._handle_events()
        log.debug('Quitting')


def show_all():
    tilesets = load_tilesets(pathlib.Path(pathlib.Path(__file__).parent.parent.parent / "assets").glob('*.png'))
    for rules in load_rules(pathlib.Path(pathlib.Path(__file__).parent.parent.parent / "assets").glob('*-rules.json')):
        tileset = list(filter(lambda _r: _r.name == rules.name, tilesets))[0]
        t = ProbabilitySpace(tileset, rules)
        t.run()


if __name__ == '__main__':  # pragma: nocover
    logging.basicConfig(
        level=logging.DEBUG,
        style='{',
        format='{asctime}:{levelname}:{filename}:{lineno}:{message}'
    )
    show_all()

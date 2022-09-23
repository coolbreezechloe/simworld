from copy import deepcopy
import pathlib
import pygame
import pygame.freetype
from pygame.time import Clock
import logging
import random

from simworld.tileset import TileSet, Tile, Coordinate
from simworld.rules import Rules, load_rules, TileIndex
from simworld.tileset_browser import load_tilesets

log = logging.getLogger(__name__)

_black = (0, 0, 0)
_white = (255, 255, 255)

WorldState = dict[Coordinate, list[TileIndex]]

class RuleEditor():
    def __init__(self, tileset: TileSet, rule_set: Rules):
        self.tileset = tileset
        self.width = 800
        self.height = 600
        self.rule_set = rule_set
        self._setup_pygame()
        self._setup_state()

    def _setup_pygame(self):
        pygame.freetype.init()
        r = pygame.init()
        log.debug(f"pygame.init() returned {r}")
        surface = pygame.display.set_mode((self.width, self.height))
        log.debug(f"created surface: {surface}")
        pygame.display.set_caption(
            f"Rule Editor Reducer : {self.tileset.name}")
        self.surface = surface

    def _setup_state(self):
        self.current_state: WorldState = dict()
        self.quit = False
        self.view_x = 0
        self.view_y = 0
        self.down_at = (0, 0)
        self.up_at = (0, 0)
        self.selected_row = 0
        self.selected_col = 0
        self.dirty = True
        self.map_width = 100
        self.map_height = 100
        self.tile_width = self.tileset.tile_width
        self.tile_height = self.tileset.tile_height
        self.view_width = self.width // self.tile_width
        self.view_height = self.height // self.tile_height
        self.original_state: WorldState = None
        self._create_random_state()

    def _create_random_state(self) -> None:
        for c in range(self.map_width):
            for r in range(self.map_height):
                initial_state = list([65, 66, 67, 97, 98, 99, 129, 130, 131, 161, 162, 163, 130, 368, 429])
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
                elif event.type == pygame.MOUSEMOTION:
                    x, y = event.pos
                    if not self.selected_col == x // self.tile_width or not self.selected_row == y // self.tile_height:
                        self.selected_col = x // self.tile_width
                        self.selected_row = y // self.tile_height
                        self.dirty = True
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    x, y = event.pos
                    self.down_at = ((x // self.tile_width) + self.view_x, (y // self.tile_height) + self.view_y)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    x, y = event.pos
                    self.up_at = ((x // self.tile_width) + self.view_x, (y // self.tile_height) + self.view_y)
                    if self.up_at == self.down_at:
                        self._handle_click(*self.up_at)

    def _handle_click(self, x: int, y: int) -> None:
        options = self.current_state[(x, y)]
        if len(options) == 1:
            return
        random.shuffle(options)
        for o in options:
            if self._fix(x, y, o):
                log.debug(f'Fixed the value {o} at ({x}, {y})')
                log.debug(f'Current state: {self.current_state}')
                return
        log.error(f'No valid options for ({x}, {y}) in {self.current_state[(x, y)]}')
        self.current_state[(x, y)] = [368]
        

    def _fix(self, x: int, y: int, choice: TileIndex, top: bool = True) -> bool:
        """Attempt to reduce the entropy to zero (fix) a given choice at a given location (x, y)

        This function will propogate the rules for the given choice and if the choice is valid
        will return True and update the internal state. If the choice breaks a rule the function
        returns False and the state is not modified"""
        result = True
        if top:
            self.original_state = deepcopy(self.current_state)

        self.current_state[(x, y)] = [choice]
        self.dirty = True
        rules = self.rule_set.rules.get(str(choice), [])
        for direction in rules:
            relative = {'Up': (0, -1), 'Down': (0, 1), 'Left': (-1, 0), 'Right': (1, 0)}
            xd, yd = relative[direction]
            x2 = x + xd
            y2 = y + yd
            if x2 >= 0 and y2 >= 0 and x2 < self.map_width and y2 < self.map_height:
                other = set(self.current_state[(x2, y2)])
                allowed = set(rules[direction])
                allow_any = bool(len(allowed) == 1 and list(allowed)[0] == 0)
                if allow_any:
                    continue
                u = allowed.intersection(other)
                if len(u) == 0:
                    result = False
                    break
                elif len(u) == 1 and not u == other:
                    result = self._fix(x2, y2, u.pop(), False)
                    break
                elif not u == other:
                    self.current_state[(x2, y2)] = list(u)


        if top and not result:
            self.current_state = self.original_state
            self.original_state = None
            self.dirty = False
        elif top and result:
            self.original_state = None
        return result

    def _handle_keydown(self, key) -> None:
        def left():
            if self.view_x > 0:
                self.view_x = self.view_x - 1
                self.dirty = True

        def right():
            if self.view_x < self.map_width - self.view_width:
                self.view_x = self.view_x + 1
                self.dirty = True

        def up():
            if self.view_y > 0:
                self.view_y = self.view_y - 1
                self.dirty = True

        def down():
            if self.view_y < self.map_height - self.view_height:
                self.view_y = self.view_y + 1
                self.dirty = True

        def origin():
            self.view_x = 0
            self.view_y = 0
            self.dirty = True

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
        surface = self._get_game_surface()
        rect = surface.get_rect()
        self.surface.blit(surface, rect)
        pygame.draw.rect(self.surface, _white, (0, 0, rect.width, rect.height), width=1)

    def _get_game_surface(self) -> pygame.Surface:
        rows = self.view_height
        cols = self.view_width
        surface = pygame.Surface((cols*self.tileset.tile_width, rows*self.tileset.tile_height))
        for r in range(rows):
            for c in range(cols):
                options = self.current_state[(self.view_x + c, self.view_y + r)]
                if len(options) == 1:
                    tile = self.tileset.get_tile_by_index(options[0])
                    rec = tile.get_rect()
                else:
                    font = pygame.freetype.SysFont(None, size=15)
                    tile, rec = font.render(f"{len(options)}", fgcolor=_white)
                rec = rec.move([int(c*self.tile_width), int(r*self.tile_height)])
                surface.blit(tile, rec)
        pygame.draw.rect(surface, _white, (self.selected_col*self.tile_width, self.selected_row *
                         self.tile_height, self.tile_width, self.tile_height), width=1)
        pygame.draw.rect(
            surface, _white, (0, 0, surface.get_width(), surface.get_height()), width=1)
        return surface

    def run(self):
        clock = Clock()
        while self.quit is False:
            if self.dirty:
                self._update_screen()
                self.dirty = False
                pygame.display.flip()
                clock.tick(60)
            self._handle_events()
        log.debug('Quitting')


def show_all():
    tilesets = load_tilesets(pathlib.Path(pathlib.Path(__file__).parent.parent.parent / "assets").glob('*.png'))
    for rules in load_rules(pathlib.Path(pathlib.Path(__file__).parent.parent.parent / "assets").glob('*-rules.json')):
        tileset = list(filter(lambda _r: _r.name == rules.name, tilesets))[0]
        t = RuleEditor(tileset, rules)
        t.run()


if __name__ == '__main__':  # pragma: nocover
    logging.basicConfig(
        level=logging.DEBUG,
        style='{',
        format='{asctime}:{levelname}:{filename}:{lineno}:{message}'
    )
    show_all()

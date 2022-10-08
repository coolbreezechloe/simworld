from dataclasses import dataclass, field
import pathlib
import pygame
import pygame.freetype
from pygame.time import Clock

import logging
import random

from simworld.tileset import TileSet, Coordinate, load_tileset
from simworld.rules import Rules, load_rules, TileIndex, AvailableOptions


log = logging.getLogger(__name__)

_black = (0, 0, 0)
_white = (255, 255, 255)

ProbabilitySpace = dict[Coordinate, AvailableOptions]


@dataclass
class GlobalState():
    error_tile: TileIndex
    map_width: int
    map_height: int
    rule_set: Rules
    down_at: Coordinate = (0, 0)
    up_at: Coordinate = (0, 0)
    selected_row: int = 0
    selected_col: int = 0
    dirty: bool = True
    current_state: ProbabilitySpace = field(init=False)

    def __post_init__(self):
        self.current_state = dict()
        self.reset_state()

    def reset_state(self) -> None:
        for c in range(self.map_width):
            for r in range(self.map_height):
                self.current_state[(c, r)] = self.rule_set.all_indexes

    def get_state_by_coordinate(self, x: int, y: int) -> AvailableOptions:
        return self.current_state.get((x, y), set())

    def fix(self, x: int, y: int, choice: TileIndex) -> bool:
        """Attempt to reduce the entropy to zero (fix) a given choice at a given location (x, y)

        This function will propogate the rules for the given choice and if the choice is valid
        will return True and update the internal state. If the choice breaks a rule or would lead
        to an invalid state the function returns False and the state is not modified"""
        self.dirty = True
        original_state = dict(self.current_state)
        result = self._fix(x, y, choice)
        if not result:
            self.current_state = original_state
            self.dirty = False
        return result

    def fill_at_random(self):
        while True:
            lowest_cells = list()
            lowest_value = None
            for (col, row) in self.current_state:
                c = len(self.current_state[(col, row)])
                if c == 1:
                    continue
                if lowest_value is None or c < lowest_value:
                    lowest_value = c
                    lowest_cells = list()
                    lowest_cells.append((col, row))
                elif c == lowest_value:
                    lowest_cells.append((col, row))
            if lowest_value:
                # TODO: the next line is not needed and greatly affects results
                # should support multiple selection strategies.
                random.shuffle(lowest_cells)
                for col, row in lowest_cells:
                    self._fix_at_random(col, row)
            else:
                break

    def clear_errors(self):
        for (col, row) in self.current_state:
            o = list(self.current_state[(col, row)])
            if len(o) == 1 and o[0] == self.error_tile:
                self.current_state[(col, row)] = self.rule_set.all_indexes
                self.dirty = True

    def _fix(self, x: int, y: int, choice: TileIndex) -> bool:
        self.current_state[(x, y)] = {choice}
        result = False
        rules = self.rule_set.get_rule_by_index(choice)
        for direction in rules:
            relative = {'Up': (0, -1), 'Down': (0, 1), 'Left': (-1, 0), 'Right': (1, 0)}
            if not direction in relative.keys():
                log.warn(f'Unhandled direction {direction}')
                continue
            xd, yd = relative[direction]
            x2 = x + xd
            y2 = y + yd
            if x2 >= 0 and y2 >= 0 and x2 < self.map_width and y2 < self.map_height:
                other = self.current_state[(x2, y2)]
                allowed = rules[direction]
                allow_any = bool(len(allowed) == 1 and list(allowed)[0] == 0)
                if allow_any:
                    continue
                u = allowed.intersection(other)
                if len(u) == 0:
                    result = False
                    break
                elif len(u) == 1 and not u == other:
                    result = self._fix(x2, y2, u.pop())
                    break
                elif not u == other:
                    self.current_state[(x2, y2)] = u
        return result

    def _fix_at_random(self, x: int, y: int) -> None:
        options = list(self.current_state[(x, y)])
        if len(options) == 1:
            return
        random.shuffle(options)
        for o in options:
            if self.fix(x, y, o):
                log.debug(f'Fixed {o} at ({x}, {y})')
                return
        log.error(f'No valid options for ({x}, {y})')
        self.current_state[(x, y)] = set([self.error_tile])


class RuleEditor():
    def __init__(self, tileset: TileSet, rule_set: Rules):
        self.tileset = tileset
        self.width = 250
        self.height = 250
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
            f"Rule Editor : {self.tileset.name}")
        self.surface = surface

    def _setup_state(self):
        self.global_state = GlobalState(map_width=20, map_height=20, error_tile=368, rule_set=self.rule_set)
        self.global_state.reset_state()
        self.view_x = 0
        self.view_y = 0
        self.down_at = (0, 0)
        self.up_at = (0, 0)
        self.selected_row = 0
        self.selected_col = 0
        self.dirty = True
        self.quit = False
        self.tile_width = self.tileset.tile_width
        self.tile_height = self.tileset.tile_height
        self.view_width = self.width // self.tile_width
        self.view_height = self.height // self.tile_height

    def _handle_events(self) -> None:
        while not self.quit:
            events = pygame.event.get()
            if not events:
                return
            for event in events:
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
                else:
                    log.debug(f'Unhandled event: {event}')

    def _handle_click(self, x: int, y: int) -> None:
        self.global_state._fix_at_random(x, y)

    def _handle_keydown(self, key) -> None:
        def left():
            if self.view_x > 0:
                self.view_x = self.view_x - 1
                self.dirty = True

        def right():
            if self.view_x < self.global_state.map_width - self.view_width:
                self.view_x = self.view_x + 1
                self.dirty = True

        def up():
            if self.view_y > 0:
                self.view_y = self.view_y - 1
                self.dirty = True

        def down():
            if self.view_y < self.global_state.map_height - self.view_height:
                self.view_y = self.view_y + 1
                self.dirty = True

        def origin():
            self.view_x = 0
            self.view_y = 0
            self.dirty = True

        def quit():
            self.quit = True

        def refresh():
            self.global_state.reset_state()
            self.dirty = True

        def finish():
            self.global_state.fill_at_random()
            self.dirty = True

        def clear():
            self.global_state.clear_errors()
            self.dirty = True

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
            pygame.K_q: quit,
            pygame.K_F5: refresh,
            pygame.K_r: refresh,
            pygame.K_f: finish,
            pygame.K_c: clear
        }

        if key in actions:
            handler = actions[key]
            handler()

    def _update_screen(self) -> None:
        self.surface.fill(_black)
        surface = self._get_game_surface()
        rect = surface.get_rect()
        self.surface.blit(surface, rect)
        pygame.draw.rect(self.surface, _white, (0, 0, rect.width, rect.height), width=1)

    def _get_game_surface(self) -> pygame.Surface:
        rows = min(self.view_height, self.global_state.map_height)
        cols = min(self.view_width, self.global_state.map_width)
        surface = pygame.Surface((cols*self.tileset.tile_width, rows*self.tileset.tile_height))
        for r in range(rows):
            for c in range(cols):
                options = list(self.global_state.get_state_by_coordinate(self.view_x + c, self.view_y + r))
                if len(options) == 1:
                    tile = self.tileset.get_tile_by_index(options[0])
                    rec = tile.get_rect()
                else:
                    font = pygame.freetype.SysFont(pygame.font.get_default_font(), size=15)
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
    base_folder = pathlib.Path(__file__).parent.parent.parent / "assets"
    for f in (base_folder / "rules").glob('*.json'):
        rules = load_rules(f)
        tileset = load_tileset(base_folder / "tilesets" / rules.file_name, rules)
        t = RuleEditor(tileset, rules)
        t.run()


if __name__ == '__main__':  # pragma: nocover
    logging.basicConfig(
        level=logging.DEBUG,
        style='{',
        format='{asctime}:{levelname}:{filename}:{lineno}:{message}'
    )
    show_all()

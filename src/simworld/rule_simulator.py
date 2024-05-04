# simworld Copyright (C) 2024 Chloe Beelby
from dataclasses import dataclass, field
import pathlib
from turtle import left
import pygame
import pygame.freetype
from pygame.time import Clock
import json
import logging
import random

from simworld.tileset import TileSet, Coordinate, load_tileset
from simworld.rules import Direction, Rules, TileDefinition, load_rules, TileIndex, AvailableOptions


log = logging.getLogger(__name__)

_black = (0, 0, 0)
_white = (255, 255, 255)

ProbabilitySpace = dict[Coordinate, AvailableOptions]
Offset = tuple[int, int]


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
        will return True and update the internal state. If the choice breaks a rule or would result
        in an invalid state the function returns False and the state is not modified"""
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
        result = True
        rules = self.rule_set.get_rule_by_index(choice)
        if len(rules) == 1 and '*' in rules:
            rules = {
                'Up': set(rules['*']),
                'Down': set(rules['*']),
                'Left': set(rules['*']),
                'Right': set(rules['*'])
            }
        relative: dict[Direction, Offset] = {
            'Up': (0, -1),
            'Down': (0, 1),
            'Left': (-1, 0),
            'Right': (1, 0)
        }
        for direction in rules:
            if not direction in relative:
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


class RuleSimulator():
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
            f"Rule Editor : {self.tileset.name}")
        self.surface = surface

    def _setup_state(self):
        self.global_state = GlobalState(map_width=24, map_height=20, error_tile=368, rule_set=self.rule_set)
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
                    if not self.selected_col == (x // self.tile_width):
                        self.selected_col = (x // self.tile_width)
                        self.dirty = True
                    if not self.selected_row == (y // self.tile_height):
                        self.selected_row = (y // self.tile_height)
                        self.dirty = True
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.down_at = self._get_coordinates(*event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.up_at = self._get_coordinates(*event.pos)
                    if self.up_at == self.down_at:
                        self.global_state._fix_at_random(*self.up_at)
                else:
                    log.debug(f'Unhandled event: {event}')

    def _get_coordinates(self, x: int, y: int) -> tuple[int, int]:
        return (
            (x // self.tile_width) + self.view_x,
            (y // self.tile_height) + self.view_y
        )

    def _key_left(self):
        if self.view_x > 0:
            self.view_x = self.view_x - 1
            self.dirty = True

    def _key_right(self):
        if self.view_x < self.global_state.map_width - self.view_width:
            self.view_x = self.view_x + 1
            self.dirty = True

    def _key_up(self):
        if self.view_y > 0:
            self.view_y = self.view_y - 1
            self.dirty = True

    def _key_down(self):
        if self.view_y < self.global_state.map_height - self.view_height:
            self.view_y = self.view_y + 1
            self.dirty = True

    def _key_origin(self):
        self.view_x = 0
        self.view_y = 0
        self.dirty = True

    def _key_quit(self):
        self.quit = True

    def _key_refresh(self):
        self.global_state.reset_state()
        self.dirty = True

    def _key_finish(self):
        self.global_state.fill_at_random()
        self.dirty = True

    def _key_clear(self):
        self.global_state.clear_errors()
        self.dirty = True

    def _handle_keydown(self, key) -> None:
        actions = {
            pygame.K_LEFT: self._key_left,
            pygame.K_a: self._key_left,
            pygame.K_h: self._key_left,
            pygame.K_j: self._key_down,
            pygame.K_RIGHT: self._key_right,
            pygame.K_d: self._key_right,
            pygame.K_l: self._key_right,
            pygame.K_UP: self._key_up,
            pygame.K_w: self._key_up,
            pygame.K_k: self._key_up,
            pygame.K_DOWN: self._key_down,
            pygame.K_s: self._key_down,
            pygame.K_g: self._key_origin,
            pygame.K_q: self._key_quit,
            pygame.K_F5: self._key_refresh,
            pygame.K_r: self._key_refresh,
            pygame.K_f: self._key_finish,
            pygame.K_c: self._key_clear,
            pygame.K_t: self._make_rules
        }

        if key in actions:
            handler = actions[key]
            handler()

    def _get_edges(self, surface):
        width, height = surface.get_size()
        top_edge = []
        bottom_edge = []
        left_edge = []
        right_edge = []
        for x in range(width):
            color = surface.get_at((x, 0))
            top_edge.append(f"({color.r},{color.g},{color.b},{color.a})")
            color = surface.get_at((x, height - 1))
            bottom_edge.append(f"({color.r},{color.g},{color.b},{color.a})")

        for y in range(height):
            color = surface.get_at((0, y))
            left_edge.append(f"({color.r},{color.g},{color.b},{color.a})")
            color = surface.get_at((width - 1, y))
            right_edge.append(f"({color.r},{color.g},{color.b},{color.a})")

        return top_edge, bottom_edge, left_edge, right_edge

    def _make_rules(self) -> None:
        """Infer a ruleset from the pixels in the tiles themselves
        
        The purpose of this function is to infer a ruleset automatically from the pixels in the
        tiles themselves under the assumption that the colors on the edges must match in order for
        the tiles to be allowed to touch. Currently must be 100% match, but that could be factored
        into an input variable.
        """
        unique_edges = {}
        for (x, y), surface in self.tileset.tiles.items():
            tile_index = (y * self.tileset.cols) + (x + 1)

            top_edge, bottom_edge, left_edge, right_edge = self._get_edges(surface)

            id_str = ('L', str.join(', ', left_edge))
            tiles = unique_edges.setdefault(id_str, set())
            tiles.update((tile_index,))
            unique_edges[id_str] = tiles

            id_str = ('R', str.join(', ', right_edge))
            tiles = unique_edges.setdefault(id_str, set())
            tiles.update((tile_index,))
            unique_edges[id_str] = tiles

            id_str = ('T', str.join(', ', top_edge))
            tiles = unique_edges.setdefault(id_str, set())
            tiles.update((tile_index,))
            unique_edges[id_str] = tiles

            id_str = ('B', str.join(', ', bottom_edge))
            tiles = unique_edges.setdefault(id_str, set())
            tiles.update((tile_index,))
            unique_edges[id_str] = tiles

        result = []
        for (x, y), surface in self.tileset.tiles.items():

            tile_index = (y * self.tileset.rows) + (x + 1)

            surface = self.tileset.get_tile_by_index(tile_index)

            top_edge, bottom_edge, left_edge, right_edge = self._get_edges(surface)

            id_str = ('B', str.join(', ', top_edge))
            up_rules = unique_edges.get(id_str, set())

            id_str = ('T', str.join(', ', bottom_edge))
            down_rules = unique_edges.get(id_str, set())

            id_str = ('R', str.join(', ', left_edge))
            left_rules = unique_edges.get(id_str, set())

            id_str = ('L', str.join(', ', right_edge))
            right_rules = unique_edges.get(id_str, set())

            rules = {
                'Up': up_rules,
                'Down': down_rules,
                'Left': left_rules,
                'Right': right_rules
            }
            tile_definition = TileDefinition(f"Tile-Index:{tile_index}", tile_index, rules)
            
            self.global_state.rule_set.tiles[tile_index] = tile_definition
        
        log.debug(f"Tiles: {json.dumps(result)}")

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
        t = RuleSimulator(tileset, rules)
        t.run()


if __name__ == '__main__':  # pragma: nocover
    logging.basicConfig(
        level=logging.DEBUG,
        style='{',
        format='{asctime}|{levelname}|{filename}|{lineno}|{message}'
    )
    show_all()

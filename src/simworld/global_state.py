from dataclasses import dataclass, field
import random
import logging

from simworld.rules import AvailableOptions, Rules, TileIndex
from simworld.tileset import Coordinate


ProbabilitySpace = dict[Coordinate, AvailableOptions]


@dataclass
class GlobalState:
    map_width: int
    map_height: int
    rule_set: Rules
    down_at: Coordinate = (0, 0)
    up_at: Coordinate = (0, 0)
    selected_row: int = 0
    selected_col: int = 0
    dirty: bool = True
    options_at: ProbabilitySpace = field(init=False)

    def __post_init__(self):
        self.options_at = dict()
        self.reset_state()

    def reset_state(self) -> None:
        for c in range(self.map_width):
            for r in range(self.map_height):
                self.options_at[(c, r)] = self.rule_set.all_indexes

    def get_state_by_coordinate(self, x: int, y: int) -> AvailableOptions:
        return self.options_at.get((x, y), set())

    def fix(self, x: int, y: int, choice: TileIndex) -> bool:
        """Attempt to reduce possible options to one (1) at a specific location

        This function will propogate the rules for the given choice and if the
        choice is valid will return True and update the internal state. If the
        choice breaks a rule or would result in an invalid state the function
        returns False and the state is not modified"""
        self.dirty = True
        original_state = dict(self.options_at)
        result = self._fix(x, y, choice)
        if not result:
            self.options_at = original_state
            self.dirty = False
        return result

    def fill_at_random(self):
        while True:
            lowest_cells = list()
            lowest_value = None
            for col, row in self.options_at:
                c = len(self.options_at[(col, row)])
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
        for col, row in self.options_at:
            o = list(self.options_at[(col, row)])
            if len(o) == 1 and o[0] == self.rule_set.error_tile:
                self.options_at[(col, row)] = self.rule_set.all_indexes
                self.dirty = True

    def _fix(self, x: int, y: int, choice: TileIndex) -> bool:
        self.options_at[(x, y)] = {choice}
        result = True
        rules = self.rule_set.get_rule_by_index(choice)
        relative = {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}
        for direction in rules:
            if not direction in relative:
                logging.warn(f"Unhandled direction {direction}")
                continue
            xd, yd = relative[direction]
            x2 = x + xd
            y2 = y + yd
            if x2 >= 0 and y2 >= 0 and x2 < self.map_width and y2 < self.map_height:
                other = self.options_at[(x2, y2)]
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
                    self.options_at[(x2, y2)] = u
        return result

    def _fix_at_random(self, x: int, y: int) -> None:
        if x < 0 or y < 0 or x >= self.map_width or y >= self.map_height:
            return
        options = list(self.options_at[(x, y)])
        if len(options) == 1:
            return
        random.shuffle(options)
        for o in options:
            if self.fix(x, y, o):
                logging.debug(f"Fixed {o} at ({x}, {y})")
                return
        logging.error(f"No valid options for ({x}, {y})")
        self.options_at[(x, y)] = set([self.rule_set.error_tile])

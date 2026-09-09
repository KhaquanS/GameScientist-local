from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from gamescientist.core.manifest import safe_pack_file
from gamescientist.core.protocol import Observation, StepResult
from gamescientist_hidden_grid.evaluator import terminal_reward
from gamescientist_hidden_grid.observations import Position, render_grid


MOVES: dict[str, Position] = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}


def _position(value: object, label: str) -> Position:
    if not isinstance(value, list) or len(value) != 2 or not all(
        isinstance(item, int) for item in value
    ):
        raise ValueError(f"{label} must be a pair of integers")
    return value[0], value[1]


class HiddenGridEnvironment:
    def __init__(self, pack_root: Path, config_path: str, step_budget: int) -> None:
        path = safe_pack_file(pack_root, config_path)
        value = json.loads(path.read_text(encoding="utf-8"))
        expected = {"rows", "columns", "player_start", "target", "traps", "symbols"}
        if set(value) != expected:
            raise ValueError("hidden-grid configuration has unknown or missing fields")
        self.rows = int(value["rows"])
        self.columns = int(value["columns"])
        self.player_start = _position(value["player_start"], "player_start")
        self.target = _position(value["target"], "target")
        self.traps = frozenset(_position(item, "trap") for item in value["traps"])
        self.symbols = dict(value["symbols"])
        self.step_budget = step_budget
        self._validate()
        self.player = self.player_start
        self.step_count = 0
        self.status = "running"

    def _validate(self) -> None:
        if self.rows < 1 or self.columns < 1:
            raise ValueError("grid dimensions must be positive")
        expected_symbols = {"player", "target", "trap", "empty"}
        if set(self.symbols) != expected_symbols:
            raise ValueError("grid symbols have unknown or missing fields")
        if any(len(symbol) != 1 for symbol in self.symbols.values()):
            raise ValueError("each grid symbol must contain exactly one character")
        if len(set(self.symbols.values())) != len(self.symbols):
            raise ValueError("grid symbols must be unique")
        positions = {self.player_start, self.target, *self.traps}
        if len(positions) != 2 + len(self.traps):
            raise ValueError("player, target, and trap positions must not overlap")
        for row, column in positions:
            if not (0 <= row < self.rows and 0 <= column < self.columns):
                raise ValueError("game position is outside the grid")

    def _observation(self) -> Observation:
        return Observation(
            grid=render_grid(
                self.rows,
                self.columns,
                self.player,
                self.target,
                self.traps,
                self.symbols,
            ),
            step_count=self.step_count,
            remaining_steps=max(0, self.step_budget - self.step_count),
            terminal=self.status != "running",
        )

    def reset(self, seed: Optional[int] = None) -> Observation:
        del seed  # This first deterministic game has one fixed layout.
        self.player = self.player_start
        self.step_count = 0
        self.status = "running"
        return self._observation()

    def step(self, action: str) -> StepResult:
        if self.status != "running":
            raise RuntimeError("episode has already terminated")
        if action not in MOVES:
            raise ValueError(f"unsupported action: {action!r}")
        row_delta, column_delta = MOVES[action]
        proposed = (self.player[0] + row_delta, self.player[1] + column_delta)
        if 0 <= proposed[0] < self.rows and 0 <= proposed[1] < self.columns:
            self.player = proposed
        self.step_count += 1

        if self.player == self.target:
            self.status = "won"
        elif self.player in self.traps:
            self.status = "trap"
        elif self.step_count >= self.step_budget:
            self.status = "timeout"

        reward = None if self.status == "running" else terminal_reward(self.status)
        return StepResult(self._observation(), self.status, reward)

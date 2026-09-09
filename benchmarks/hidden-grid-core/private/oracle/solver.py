from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Optional


MOVES = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}


def solve(config_path: Path) -> Optional[list[str]]:
    """Return a shortest safe path for benchmark-author validation only."""

    value = json.loads(config_path.read_text(encoding="utf-8"))
    rows = value["rows"]
    columns = value["columns"]
    start = tuple(value["player_start"])
    target = tuple(value["target"])
    traps = {tuple(position) for position in value["traps"]}
    queue = deque([(start, [])])
    visited = {start}
    while queue:
        position, path = queue.popleft()
        if position == target:
            return path
        for action, (row_delta, column_delta) in MOVES.items():
            candidate = (position[0] + row_delta, position[1] + column_delta)
            if not (0 <= candidate[0] < rows and 0 <= candidate[1] < columns):
                continue
            if candidate in traps or candidate in visited:
                continue
            visited.add(candidate)
            queue.append((candidate, [*path, action]))
    return None

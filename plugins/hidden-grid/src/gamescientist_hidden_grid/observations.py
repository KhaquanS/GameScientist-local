from __future__ import annotations


Position = tuple[int, int]


def render_grid(
    rows: int,
    columns: int,
    player: Position,
    target: Position,
    traps: frozenset[Position],
    symbols: dict[str, str],
) -> tuple[str, ...]:
    rendered: list[str] = []
    for row in range(rows):
        cells: list[str] = []
        for column in range(columns):
            position = (row, column)
            if position == player:
                cells.append(symbols["player"])
            elif position == target:
                cells.append(symbols["target"])
            elif position in traps:
                cells.append(symbols["trap"])
            else:
                cells.append(symbols["empty"])
        rendered.append("".join(cells))
    return tuple(rendered)

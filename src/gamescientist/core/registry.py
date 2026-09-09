from __future__ import annotations

from importlib import metadata
from typing import Any, Iterable, Optional

from gamescientist.core.plugin import GamePlugin


ENTRY_POINT_GROUP = "gamescientist.games"


def _installed_entry_points() -> Iterable[Any]:
    available = metadata.entry_points()
    if hasattr(available, "select"):
        selected = available.select(group=ENTRY_POINT_GROUP)
    else:
        selected = available.get(ENTRY_POINT_GROUP, ())

    # Python 3.9 can report both editable source metadata and installed
    # dist-info metadata for the same logical entry point. Collapse only exact
    # duplicates here; discover_plugins still rejects distinct registrations
    # that compete for one name.
    unique: list[Any] = []
    seen: set[tuple[str, str]] = set()
    for entry_point in selected:
        key = (entry_point.name, entry_point.value)
        if key not in seen:
            seen.add(key)
            unique.append(entry_point)
    return unique


def discover_plugins(
    candidates: Optional[Iterable[Any]] = None,
) -> tuple[dict[str, GamePlugin], list[dict[str, str]]]:
    selected = list(candidates if candidates is not None else _installed_entry_points())
    grouped: dict[str, list[Any]] = {}
    for entry_point in selected:
        grouped.setdefault(entry_point.name, []).append(entry_point)

    plugins: dict[str, GamePlugin] = {}
    errors: list[dict[str, str]] = []
    for name, matches in sorted(grouped.items()):
        if len(matches) != 1:
            errors.append({"id": name, "message": "duplicate plugin entry points"})
            continue
        try:
            loaded = matches[0].load()
            plugin = loaded() if isinstance(loaded, type) else loaded
            if not isinstance(plugin, GamePlugin):
                raise TypeError("game plugin must inherit GamePlugin")
            if plugin.id != name:
                raise ValueError(f"entry point {name!r} loaded plugin {plugin.id!r}")
            if plugin.game_id in {value.game_id for value in plugins.values()}:
                raise ValueError(f"duplicate game plugin: {plugin.game_id}")
            plugins[name] = plugin
        except Exception as error:
            errors.append({"id": name, "message": str(error)})
    return plugins, errors

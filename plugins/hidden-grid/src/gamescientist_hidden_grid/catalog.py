from __future__ import annotations

import json
from pathlib import Path

from gamescientist.core.catalog import TaskCatalog, TaskSpec
from gamescientist.core.manifest import safe_pack_file


def load_catalog(pack_root: Path, catalog_path: str) -> TaskCatalog:
    path = safe_pack_file(pack_root, catalog_path)
    value = json.loads(path.read_text(encoding="utf-8"))
    expected = {"id", "version", "game", "tasks"}
    if set(value) != expected:
        raise ValueError("hidden-grid catalog has unknown or missing fields")
    tasks = []
    for raw in value["tasks"]:
        task_expected = {
            "id",
            "name",
            "summary",
            "actions",
            "step_budget",
            "private_config",
        }
        if set(raw) != task_expected:
            raise ValueError("hidden-grid task has unknown or missing fields")
        safe_pack_file(pack_root, raw["private_config"])
        tasks.append(
            TaskSpec(
                id=raw["id"],
                name=raw["name"],
                summary=raw["summary"],
                actions=tuple(raw["actions"]),
                step_budget=raw["step_budget"],
                private_config=raw["private_config"],
            )
        )
    return TaskCatalog(value["id"], value["version"], value["game"], tuple(tasks))

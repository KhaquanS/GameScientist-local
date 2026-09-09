from __future__ import annotations

from dataclasses import dataclass

from gamescientist.core.identity import validate_identifier


@dataclass(frozen=True)
class TaskSpec:
    id: str
    name: str
    summary: str
    actions: tuple[str, ...]
    step_budget: int
    private_config: str

    def __post_init__(self) -> None:
        validate_identifier(self.id, "task_id")
        if not self.name.strip() or not self.summary.strip():
            raise ValueError("task name and summary must not be blank")
        if not self.actions or len(set(self.actions)) != len(self.actions):
            raise ValueError("task actions must be non-empty and unique")
        if any(not action.strip() for action in self.actions):
            raise ValueError("task actions must not be blank")
        if self.step_budget < 1:
            raise ValueError("step budget must be positive")


@dataclass(frozen=True)
class TaskCatalog:
    id: str
    version: str
    game_id: str
    tasks: tuple[TaskSpec, ...]

    def __post_init__(self) -> None:
        validate_identifier(self.id, "catalog_id")
        validate_identifier(self.game_id, "game_id")
        identifiers = [task.id for task in self.tasks]
        if not identifiers or len(identifiers) != len(set(identifiers)):
            raise ValueError("catalog task IDs must be non-empty and unique")

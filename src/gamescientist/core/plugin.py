from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from gamescientist.core.catalog import TaskCatalog, TaskSpec
from gamescientist.core.identity import validate_identifier
from gamescientist.core.protocol import GameEnvironment


@dataclass(frozen=True)
class PluginDescriptor:
    id: str
    game_id: str
    name: str
    version: str

    def __post_init__(self) -> None:
        validate_identifier(self.id, "plugin_id")
        validate_identifier(self.game_id, "game_id")
        if not self.name.strip():
            raise ValueError("plugin name must not be blank")


@dataclass(frozen=True)
class BenchmarkContext:
    pack_root: Path
    state_dir: Path


class GamePlugin(ABC):
    descriptor: PluginDescriptor

    @property
    def id(self) -> str:
        return self.descriptor.id

    @property
    def game_id(self) -> str:
        return self.descriptor.game_id

    @abstractmethod
    def load_catalog(self, pack_root: Path, catalog_path: str) -> TaskCatalog:
        """Load this plugin's task catalog from a read-only pack."""

    @abstractmethod
    def create_environment(
        self, context: BenchmarkContext, task: TaskSpec
    ) -> GameEnvironment:
        """Create a fresh private environment for one task."""

    def public_task(self, task: TaskSpec) -> dict[str, object]:
        return {
            "id": task.id,
            "name": task.name,
            "summary": task.summary,
            "actions": list(task.actions),
            "stepBudget": task.step_budget,
        }

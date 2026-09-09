from __future__ import annotations

from pathlib import Path

from gamescientist.core.catalog import TaskCatalog, TaskSpec
from gamescientist.core.plugin import BenchmarkContext, GamePlugin, PluginDescriptor
from gamescientist.core.protocol import GameEnvironment
from gamescientist_hidden_grid.catalog import load_catalog
from gamescientist_hidden_grid.environment import HiddenGridEnvironment


class HiddenGridPlugin(GamePlugin):
    descriptor = PluginDescriptor(
        id="hidden-grid",
        game_id="hidden-grid",
        name="Hidden Grid",
        version="0.1.0",
    )

    def load_catalog(self, pack_root: Path, catalog_path: str) -> TaskCatalog:
        return load_catalog(pack_root, catalog_path)

    def create_environment(
        self, context: BenchmarkContext, task: TaskSpec
    ) -> GameEnvironment:
        return HiddenGridEnvironment(context.pack_root, task.private_config, task.step_budget)

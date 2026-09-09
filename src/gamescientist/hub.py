from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

from gamescientist.config import Settings
from gamescientist.core.catalog import TaskCatalog, TaskSpec
from gamescientist.core.evaluation import EvaluationReport
from gamescientist.core.identity import PackKey, TaskKey
from gamescientist.core.manifest import BenchmarkManifest, discover_manifest_paths
from gamescientist.core.plugin import BenchmarkContext, GamePlugin
from gamescientist.core.protocol import Observation
from gamescientist.core.registry import discover_plugins
from gamescientist.database import RunStore


@dataclass(frozen=True)
class LoadedPack:
    key: PackKey
    manifest_path: Path
    plugin: GamePlugin
    catalog: TaskCatalog
    context: BenchmarkContext


ActionProvider = Callable[[Observation], Optional[str]]


class GameScientistHub:
    """Game-neutral discovery, episode execution, storage, and reporting."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        *,
        plugins: Optional[dict[str, GamePlugin]] = None,
        manifest_paths: Optional[tuple[Path, ...]] = None,
    ) -> None:
        self.settings = settings or Settings.load()
        if plugins is None:
            self.plugins, plugin_errors = discover_plugins()
        else:
            self.plugins = dict(plugins)
            plugin_errors = []
        self.discovery_errors: list[dict[str, str]] = list(plugin_errors)
        self.packs: dict[PackKey, LoadedPack] = {}
        self.tasks: dict[TaskKey, tuple[LoadedPack, TaskSpec]] = {}
        self.store = RunStore(self.settings.state_dir / "state.sqlite")
        selected = (
            manifest_paths
            if manifest_paths is not None
            else discover_manifest_paths(self.settings.benchmark_paths)
        )
        self._load_packs(selected)

    def _load_packs(self, manifest_paths: tuple[Path, ...]) -> None:
        for manifest_path in manifest_paths:
            try:
                manifest = BenchmarkManifest.load(manifest_path)
                plugin = self.plugins.get(manifest.plugin)
                if plugin is None:
                    raise LookupError(f"required plugin is not installed: {manifest.plugin}")
                pack_root = manifest_path.resolve().parent
                catalog = plugin.load_catalog(pack_root, manifest.catalog)
                if catalog.game_id != plugin.game_id:
                    raise ValueError("catalog game ID does not match its plugin")
                key = PackKey(plugin.game_id, manifest.pack_id)
                if key in self.packs:
                    raise ValueError(f"duplicate pack key: {key}")
                context = BenchmarkContext(
                    pack_root=pack_root,
                    state_dir=self.settings.state_dir / "packs" / key.game_id / key.pack_id,
                )
                loaded = LoadedPack(key, manifest_path.resolve(), plugin, catalog, context)
                proposed = [TaskKey(key.game_id, key.pack_id, task.id) for task in catalog.tasks]
                if any(task_key in self.tasks for task_key in proposed):
                    raise ValueError("duplicate canonical task key")
                self.packs[key] = loaded
                for task_key, task in zip(proposed, catalog.tasks):
                    self.tasks[task_key] = (loaded, task)
            except Exception as error:
                self.discovery_errors.append(
                    {"id": manifest_path.as_posix(), "message": str(error)}
                )

    @property
    def task_keys(self) -> tuple[str, ...]:
        return tuple(str(key) for key in sorted(self.tasks))

    def list_games(self) -> list[dict[str, str]]:
        return [
            {
                "id": plugin.game_id,
                "plugin": plugin.id,
                "name": plugin.descriptor.name,
                "version": plugin.descriptor.version,
            }
            for plugin in sorted(self.plugins.values(), key=lambda item: item.game_id)
        ]

    def list_tasks(self) -> list[dict[str, object]]:
        return [
            {"key": str(key), **loaded.plugin.public_task(task)}
            for key, (loaded, task) in sorted(self.tasks.items())
        ]

    def _resolve(self, task_key: str) -> tuple[TaskKey, LoadedPack, TaskSpec]:
        key = TaskKey.parse(task_key)
        try:
            loaded, task = self.tasks[key]
        except KeyError as error:
            raise KeyError(f"unknown task: {key}") from error
        return key, loaded, task

    def initial_observation(self, task_key: str, seed: Optional[int] = None) -> Observation:
        _, loaded, task = self._resolve(task_key)
        return loaded.plugin.create_environment(loaded.context, task).reset(seed)

    def run_episode(
        self,
        task_key: str,
        action_provider: ActionProvider,
        seed: Optional[int] = None,
    ) -> tuple[EvaluationReport, list[dict[str, object]]]:
        key, loaded, task = self._resolve(task_key)
        environment = loaded.plugin.create_environment(loaded.context, task)
        observation = environment.reset(seed)
        transcript: list[dict[str, object]] = [{"observation": observation.to_dict()}]
        actions: list[str] = []
        status = "incomplete"
        reward: Optional[int] = None

        while not observation.terminal:
            action = action_provider(observation)
            if action is None:
                break
            result = environment.step(action)
            actions.append(action)
            observation = result.observation
            transcript.append(
                {"action": action, "observation": observation.to_dict()}
            )
            status = result.status
            reward = result.reward

        complete = status in {"won", "trap", "timeout"}
        report = EvaluationReport(
            run_id=str(uuid.uuid4()),
            task_key=str(key),
            status=status,
            complete=complete,
            reward=reward if complete else None,
            steps=observation.step_count,
        )
        self.store.record(report, actions, transcript)
        return report, transcript

    def run_actions(
        self, task_key: str, actions: Iterable[str], seed: Optional[int] = None
    ) -> tuple[EvaluationReport, list[dict[str, object]]]:
        iterator = iter(actions)

        def provide(_: Observation) -> Optional[str]:
            return next(iterator, None)

        return self.run_episode(task_key, provide, seed)

    def report(self, task_key: str = "") -> dict[str, object]:
        runs = self.store.list_runs(task_key)
        complete = [run for run in runs if run["complete"]]
        wins = sum(run["status"] == "won" for run in complete)
        traps = sum(run["status"] == "trap" for run in complete)
        timeouts = sum(run["status"] == "timeout" for run in complete)
        return {
            "runs": len(runs),
            "completeRuns": len(complete),
            "wins": wins,
            "traps": traps,
            "timeouts": timeouts,
            "meanReward": (
                sum(int(run["reward"]) for run in complete) / len(complete)
                if complete
                else None
            ),
            "results": runs,
        }

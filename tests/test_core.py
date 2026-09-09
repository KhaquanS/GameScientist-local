from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "plugins" / "hidden-grid" / "src"))

from gamescientist.config import Settings  # noqa: E402
from gamescientist.core.identity import TaskKey  # noqa: E402
from gamescientist.core.manifest import BenchmarkManifest  # noqa: E402
from gamescientist.core.registry import discover_plugins  # noqa: E402
from gamescientist.hub import GameScientistHub  # noqa: E402
from gamescientist_hidden_grid.plugin import HiddenGridPlugin  # noqa: E402


class CoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        state = Path(self.temporary.name) / "state"
        self.settings = Settings(
            root=ROOT,
            benchmark_paths=(ROOT / "benchmarks",),
            state_dir=state,
        )
        self.manifest = ROOT / "benchmarks" / "hidden-grid-core" / "benchmark.json"
        self.hub = GameScientistHub(
            self.settings,
            plugins={"hidden-grid": HiddenGridPlugin()},
            manifest_paths=(self.manifest,),
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_canonical_task_identity(self) -> None:
        key = TaskKey.parse("hidden-grid/core/pacman-unknown")
        self.assertEqual(str(key), "hidden-grid/core/pacman-unknown")
        with self.assertRaises(ValueError):
            TaskKey.parse("pacman-unknown")

    def test_manifest_loads(self) -> None:
        manifest = BenchmarkManifest.load(self.manifest)
        self.assertEqual(manifest.plugin, "hidden-grid")
        self.assertEqual(manifest.pack_id, "core")

    def test_public_task_does_not_expose_private_rule_fields(self) -> None:
        public = self.hub.list_tasks()[0]
        serialized = str(public).lower()
        self.assertNotIn("private", serialized)
        self.assertNotIn("target", serialized)
        self.assertNotIn("trap", serialized)
        self.assertNotIn("food", serialized)

    def test_complete_outcomes_and_report(self) -> None:
        task = "hidden-grid/core/pacman-unknown"
        win, _ = self.hub.run_actions(
            task, ["down", "down", "right", "right", "right"]
        )
        trap, _ = self.hub.run_actions(task, ["right", "right"])
        timeout, _ = self.hub.run_actions(task, ["up"] * 8)
        self.assertEqual((win.reward, trap.reward, timeout.reward), (1, -1, 0))
        summary = self.hub.report(task)
        self.assertEqual(summary["wins"], 1)
        self.assertEqual(summary["traps"], 1)
        self.assertEqual(summary["timeouts"], 1)
        self.assertEqual(summary["meanReward"], 0.0)

    def test_short_action_list_is_recorded_as_incomplete(self) -> None:
        report, _ = self.hub.run_actions(
            "hidden-grid/core/pacman-unknown", ["down"]
        )
        self.assertFalse(report.complete)
        self.assertIsNone(report.reward)

    def test_run_does_not_modify_benchmark_pack(self) -> None:
        pack = self.manifest.parent
        before = {
            path.relative_to(pack): path.read_bytes()
            for path in pack.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        self.hub.run_actions(
            "hidden-grid/core/pacman-unknown",
            ["down", "down", "right", "right", "right"],
        )
        after = {
            path.relative_to(pack): path.read_bytes()
            for path in pack.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        self.assertEqual(before, after)

    def test_distinct_duplicate_plugin_registrations_are_rejected(self) -> None:
        class FakeEntryPoint:
            def __init__(self, name: str, plugin: HiddenGridPlugin) -> None:
                self.name = name
                self.value = "fixture"
                self.plugin = plugin

            def load(self) -> HiddenGridPlugin:
                return self.plugin

        plugins, errors = discover_plugins(
            [
                FakeEntryPoint("hidden-grid", HiddenGridPlugin()),
                FakeEntryPoint("hidden-grid", HiddenGridPlugin()),
            ]
        )
        self.assertEqual(plugins, {})
        self.assertEqual(errors[0]["id"], "hidden-grid")


if __name__ == "__main__":
    unittest.main()

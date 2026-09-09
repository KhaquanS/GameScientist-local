from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "plugins" / "hidden-grid" / "src"))

from gamescientist.core.plugin import BenchmarkContext  # noqa: E402
from gamescientist_hidden_grid.plugin import HiddenGridPlugin  # noqa: E402


class HiddenGridPluginTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pack = ROOT / "benchmarks" / "hidden-grid-core"
        self.plugin = HiddenGridPlugin()
        self.catalog = self.plugin.load_catalog(self.pack, "catalog.json")
        self.task = self.catalog.tasks[0]
        self.environment = self.plugin.create_environment(
            BenchmarkContext(self.pack, ROOT / ".gamescientist" / "test"), self.task
        )

    def test_winning_path_returns_one(self) -> None:
        self.environment.reset()
        result = None
        for action in ["down", "down", "right", "right", "right"]:
            result = self.environment.step(action)
        self.assertIsNotNone(result)
        self.assertEqual(result.status, "won")
        self.assertEqual(result.reward, 1)

    def test_trap_returns_negative_one(self) -> None:
        self.environment.reset()
        self.environment.step("right")
        result = self.environment.step("right")
        self.assertEqual(result.status, "trap")
        self.assertEqual(result.reward, -1)

    def test_budget_exhaustion_returns_zero(self) -> None:
        self.environment.reset()
        result = None
        for _ in range(self.task.step_budget):
            result = self.environment.step("up")
        self.assertIsNotNone(result)
        self.assertEqual(result.status, "timeout")
        self.assertEqual(result.reward, 0)

    def test_invalid_action_fails_without_advancing(self) -> None:
        before = self.environment.reset()
        with self.assertRaises(ValueError):
            self.environment.step("teleport")
        after = self.environment.step("up").observation
        self.assertEqual(before.grid, after.grid)
        self.assertEqual(after.step_count, 1)


if __name__ == "__main__":
    unittest.main()

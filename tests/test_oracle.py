from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOLVER_PATH = (
    ROOT / "benchmarks" / "hidden-grid-core" / "private" / "oracle" / "solver.py"
)
CONFIG_PATH = (
    ROOT
    / "benchmarks"
    / "hidden-grid-core"
    / "private"
    / "games"
    / "pacman-unknown"
    / "initial-state.json"
)


class OracleTests(unittest.TestCase):
    def test_private_control_finds_path_within_budget(self) -> None:
        spec = importlib.util.spec_from_file_location("private_oracle", SOLVER_PATH)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        path = module.solve(CONFIG_PATH)
        self.assertIsNotNone(path)
        self.assertLessEqual(len(path), 8)


if __name__ == "__main__":
    unittest.main()

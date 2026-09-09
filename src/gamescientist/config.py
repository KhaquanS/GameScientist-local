from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Settings:
    """Filesystem locations used by one GameScientist process."""

    root: Path
    benchmark_paths: tuple[Path, ...]
    state_dir: Path

    @classmethod
    def load(cls, root: Optional[Path] = None) -> "Settings":
        selected_root = (root or Path.cwd()).resolve()
        configured_benchmarks = os.environ.get("GAMESCIENTIST_BENCHMARK_PATH")
        if configured_benchmarks:
            benchmark_paths = tuple(
                Path(value).expanduser().resolve()
                for value in configured_benchmarks.split(os.pathsep)
                if value
            )
        else:
            benchmark_paths = (selected_root / "benchmarks",)
        configured_state = os.environ.get("GAMESCIENTIST_STATE_DIR")
        state_dir = (
            Path(configured_state).expanduser().resolve()
            if configured_state
            else selected_root / ".gamescientist"
        )
        return cls(selected_root, benchmark_paths, state_dir)

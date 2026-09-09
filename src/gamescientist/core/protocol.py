from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


TERMINAL_STATUSES = {"won", "trap", "timeout"}


@dataclass(frozen=True)
class Observation:
    grid: tuple[str, ...]
    step_count: int
    remaining_steps: int
    terminal: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "grid": list(self.grid),
            "stepCount": self.step_count,
            "remainingSteps": self.remaining_steps,
            "terminal": self.terminal,
        }


@dataclass(frozen=True)
class StepResult:
    observation: Observation
    status: str
    reward: Optional[int]

    def __post_init__(self) -> None:
        allowed = {"running", *TERMINAL_STATUSES}
        if self.status not in allowed:
            raise ValueError(f"unknown episode status: {self.status}")
        if self.status == "running" and self.reward is not None:
            raise ValueError("a running episode cannot have a terminal reward")
        if self.status in TERMINAL_STATUSES and self.reward not in {-1, 0, 1}:
            raise ValueError("a terminal episode must have reward -1, 0, or 1")


class GameEnvironment(Protocol):
    def reset(self, seed: Optional[int] = None) -> Observation:
        ...

    def step(self, action: str) -> StepResult:
        ...

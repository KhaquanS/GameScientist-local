from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EvaluationReport:
    run_id: str
    task_key: str
    status: str
    complete: bool
    reward: Optional[int]
    steps: int

    @property
    def won(self) -> bool:
        return self.status == "won"

    def __post_init__(self) -> None:
        if self.complete and self.reward not in {-1, 0, 1}:
            raise ValueError("a complete run must have reward -1, 0, or 1")
        if not self.complete and self.reward is not None:
            raise ValueError("an incomplete run must not have a reward")

    def to_dict(self) -> dict[str, object]:
        return {
            "runId": self.run_id,
            "taskKey": self.task_key,
            "status": self.status,
            "complete": self.complete,
            "won": self.won,
            "reward": self.reward,
            "steps": self.steps,
        }

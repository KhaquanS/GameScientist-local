from __future__ import annotations

import re
from dataclasses import dataclass


_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def validate_identifier(value: str, label: str) -> str:
    """Validate the normalized identifiers inherited from Rhenium's design."""

    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"{label} must be a normalized lowercase identifier: {value!r}")
    return value


@dataclass(frozen=True, order=True)
class PackKey:
    game_id: str
    pack_id: str

    def __post_init__(self) -> None:
        validate_identifier(self.game_id, "game_id")
        validate_identifier(self.pack_id, "pack_id")

    def __str__(self) -> str:
        return f"{self.game_id}/{self.pack_id}"


@dataclass(frozen=True, order=True)
class TaskKey:
    game_id: str
    pack_id: str
    task_id: str

    def __post_init__(self) -> None:
        validate_identifier(self.game_id, "game_id")
        validate_identifier(self.pack_id, "pack_id")
        validate_identifier(self.task_id, "task_id")

    @property
    def pack_key(self) -> PackKey:
        return PackKey(self.game_id, self.pack_id)

    @classmethod
    def parse(cls, value: str) -> "TaskKey":
        parts = value.split("/")
        if len(parts) != 3:
            raise ValueError("task key must have the form <game-id>/<pack-id>/<task-id>")
        return cls(*parts)

    def __str__(self) -> str:
        return f"{self.game_id}/{self.pack_id}/{self.task_id}"

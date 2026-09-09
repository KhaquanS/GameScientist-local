from __future__ import annotations


def terminal_reward(status: str) -> int:
    rewards = {"won": 1, "trap": -1, "timeout": 0}
    try:
        return rewards[status]
    except KeyError as error:
        raise ValueError(f"status is not terminal: {status}") from error

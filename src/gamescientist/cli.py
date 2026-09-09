from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from gamescientist.config import Settings
from gamescientist.core.protocol import Observation
from gamescientist.hub import GameScientistHub


def _json(value: object) -> None:
    print(json.dumps(value, indent=2))


def _show(observation: Observation) -> None:
    print("\n".join(observation.grid))
    print(
        f"steps={observation.step_count} "
        f"remaining={observation.remaining_steps} terminal={observation.terminal}"
    )


def _hub(root: Path) -> GameScientistHub:
    return GameScientistHub(Settings.load(root))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gamescientist")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("games", help="list discovered game plugins")
    commands.add_parser("tasks", help="list public task metadata")

    observe = commands.add_parser("observe", help="show a task's initial observation")
    observe.add_argument("task_key")
    observe.add_argument("--seed", type=int)

    play = commands.add_parser("play", help="play manually or with a fixed action list")
    play.add_argument("task_key")
    play.add_argument("--actions", help="comma-separated actions; omit for manual play")
    play.add_argument("--seed", type=int)

    report = commands.add_parser("report", help="summarize stored runs")
    report.add_argument("--task", default="")
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    arguments = build_parser().parse_args(argv)
    hub = _hub(arguments.root)
    if hub.discovery_errors:
        print(json.dumps({"discoveryErrors": hub.discovery_errors}, indent=2))

    if arguments.command == "games":
        _json(hub.list_games())
    elif arguments.command == "tasks":
        _json(hub.list_tasks())
    elif arguments.command == "observe":
        _show(hub.initial_observation(arguments.task_key, arguments.seed))
    elif arguments.command == "play":
        if arguments.actions:
            actions = [value.strip() for value in arguments.actions.split(",") if value.strip()]
            report, transcript = hub.run_actions(arguments.task_key, actions, arguments.seed)
        else:
            allowed = {
                str(item["key"]): item["actions"] for item in hub.list_tasks()
            }[arguments.task_key]

            def prompt(observation: Observation) -> Optional[str]:
                _show(observation)
                value = input(f"action {allowed} (or quit): ").strip().lower()
                return None if value == "quit" else value

            report, transcript = hub.run_episode(arguments.task_key, prompt, arguments.seed)
        _json({"result": report.to_dict(), "transcript": transcript})
    elif arguments.command == "report":
        _json(hub.report(arguments.task))


if __name__ == "__main__":
    main()

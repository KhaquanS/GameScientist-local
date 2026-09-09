# GameScientist

GameScientist is a benchmark for measuring whether a large language model can
discover and solve a novel game through interaction, without being told the
game's rules or winning condition.

The model is given only:

- a safe observation of the current game state;
- a fixed list of actions it may take;
- a limited action budget;
- the consequences of the actions it chooses.

GameScientist owns the rest of the experiment: it finds the correct game
plugin, starts a run, enforces the budget, records the public action history,
asks the private evaluator for the outcome, stores the result, and produces
comparable reports.

## Current status

Version 0.1.0 is a model-free functional prototype. It supports one
deterministic, Pacman-like hidden-grid task that can be played manually or with
a supplied list of actions. It does **not** yet call an LLM.

The game code currently runs in the same Python process as the command-line
tool. That is suitable for development and tests, but it is not a strong
security boundary against an evaluated model. Before real LLM measurements,
the private game and evaluator must run in a separate process or container that
the model cannot inspect.

## First task: Unknown Grid

The first canonical task ID is:

```text
hidden-grid/core/pacman-unknown
```

The public view is a `4 x 5` grid. `P` is the controlled player; `A` and `B`
are unfamiliar objects whose meanings are not explained. On each step the
player chooses `up`, `down`, `left`, or `right`. The episode has an eight-step
budget.

The benchmark privately implements these outcomes:

- reaching the target within the budget returns `+1`;
- entering a trap returns `-1`;
- exhausting the budget returns `0`.

These rules are documented here for benchmark developers. They are not present
in the public instructions intended for an evaluated model.

## What is reused from GameCodeBench

GameScientist reuses the following Rhenium architectural ideas:

1. **Game-neutral core.** Shared orchestration does not contain branches for a
   specific game.
2. **Independent plugins.** A plugin teaches the core how to load and run one
   game family.
3. **Read-only benchmark packs.** Versioned input data stays separate from
   generated runs and reports.
4. **Canonical identity.** Every task is named
   `<game-id>/<pack-id>/<task-id>` so stored results cannot collide.
5. **Fault-isolated discovery.** A broken or missing plugin is reported without
   changing another pack's identity.
6. **Normalized results.** All games eventually return a common run summary.

GameScientist does not reuse GameCodeBench's existing DST, Isaac, Stardew
Valley, or Garry's Mod packs, private tests, licensed runtimes, providers, Web
UI, or static code-submission workflow.

The central change is:

```text
GameCodeBench:
model writes code -> evaluator tests the submitted files

GameScientist:
model observes -> chooses an action -> game changes -> model observes again
```

## Core concepts

### Plugin

A plugin is executable game-family machinery. The hidden-grid plugin knows how
to read a grid catalog, create a fresh grid environment, validate movement,
render safe observations, detect terminal states, and return a reward.

### Benchmark pack

A benchmark pack is versioned experiment content. It lists the tasks to run,
contains the public instructions and data schemas, and holds private game
configurations and author-only validation controls.

### Episode

An episode is one attempt at one task. It begins with a reset and initial
observation. It ends on a win, trap, timeout, or an incomplete action stream.

### Run record

A run record is the stored result of an episode: task ID, actions, public
observations, step count, completion status, and reward. Run records are stored
under `.gamescientist/`, never inside a benchmark pack.

## Install

GameScientist currently has no third-party runtime dependencies. Python 3.9 or
newer is required.

From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e . -e plugins/hidden-grid
```

The first `-e` installs the game-neutral core. The second installs the
hidden-grid plugin and registers it with the core. An editable installation
uses the repository files directly, so local changes are available without
reinstalling.

## Use

Run these commands from the repository root.

List installed game plugins:

```sh
gamescientist games
```

List public tasks:

```sh
gamescientist tasks
```

View the initial public observation:

```sh
gamescientist observe hidden-grid/core/pacman-unknown
```

Play manually:

```sh
gamescientist play hidden-grid/core/pacman-unknown
```

Run a fixed action sequence:

```sh
gamescientist play hidden-grid/core/pacman-unknown \
  --actions down,down,right,right,right
```

Show all stored run results and aggregate counts:

```sh
gamescientist report
```

Filter the report to this task:

```sh
gamescientist report --task hidden-grid/core/pacman-unknown
```

By default, generated state is written to `.gamescientist/`. Override the
benchmark or state locations with `GAMESCIENTIST_BENCHMARK_PATH` and
`GAMESCIENTIST_STATE_DIR`.

## Test

The test suite uses Python's built-in test runner:

```sh
PYTHONPATH=src:plugins/hidden-grid/src \
  python -m unittest discover -s tests -v

PYTHONPATH=src:plugins/hidden-grid/src \
  python -m unittest discover -s plugins/hidden-grid/tests -v
```

The tests cover canonical IDs, pack loading, public/private field separation,
winning, traps, budget exhaustion, incomplete runs, result storage, reporting,
and the private known-good solver.

## Repository map

```text
GameScientist/
├── .github/workflows/ci.yml
├── benchmarks/
│   ├── README.md
│   └── hidden-grid-core/
│       ├── README.md
│       ├── benchmark.json
│       ├── catalog.json
│       ├── public/
│       │   ├── action-schema.json
│       │   ├── agent-instructions.md
│       │   └── observation-schema.json
│       └── private/
│           ├── games/pacman-unknown/initial-state.json
│           └── oracle/solver.py
├── docs/games/                 reserved for longer per-game documentation
├── plugins/hidden-grid/
│   ├── README.md
│   ├── pyproject.toml
│   ├── src/gamescientist_hidden_grid/
│   │   ├── __init__.py
│   │   ├── catalog.py
│   │   ├── environment.py
│   │   ├── evaluator.py
│   │   ├── observations.py
│   │   └── plugin.py
│   └── tests/test_hidden_grid.py
├── scripts/                    reserved for developer maintenance commands
├── src/gamescientist/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── config.py
│   ├── database.py
│   ├── hub.py
│   ├── agent/                  reserved for the future LLM adapter
│   ├── core/
│   │   ├── __init__.py
│   │   ├── catalog.py
│   │   ├── evaluation.py
│   │   ├── identity.py
│   │   ├── manifest.py
│   │   ├── plugin.py
│   │   ├── protocol.py
│   │   └── registry.py
│   └── runtime/                reserved for process isolation and replay
├── tests/
│   ├── __init__.py
│   ├── test_core.py
│   └── test_oracle.py
├── .env.example
├── .gitignore
├── AGENTS.md
├── NOTICE
├── README.md
├── pyproject.toml
└── run-gamescientist
```

### Root files and folders

- `.github/workflows/ci.yml` runs both test groups on every GitHub push and pull
  request.
- `benchmarks/` contains versioned, read-only experiment content.
- `docs/` is reserved for longer design and per-game documents as the project
  grows. This README is intentionally the complete starting guide.
- `plugins/` contains independently installable game-family adapters.
- `scripts/` is reserved for developer maintenance tools.
- `src/gamescientist/` contains the game-neutral platform.
- `tests/` verifies contracts spanning the core, plugin, pack, and database.
- `.env.example` lists optional, non-secret path settings.
- `.gitignore` keeps generated or machine-local files out of Git.
- `AGENTS.md` records contributor rules protecting benchmark integrity.
- `NOTICE` records which GameCodeBench design ideas were adapted.
- `pyproject.toml` defines the core Python package and command.
- `run-gamescientist` is a repository-local command wrapper.
- `.gitkeep` files in otherwise empty reserved directories are non-code
  placeholders that allow Git to preserve those directories.

### Game-neutral core

- `config.py` chooses repository, benchmark, and generated-state locations.
- `database.py` creates a versioned SQLite database and stores safe run records.
- `hub.py` discovers packs, joins them to plugins, runs episodes, and summarizes
  results.
- `cli.py` implements `games`, `tasks`, `observe`, `play`, and `report`.
- `core/identity.py` implements stable game/pack/task identifiers.
- `core/catalog.py` defines validated public task and catalog data.
- `core/manifest.py` safely discovers `benchmark.json` files and prevents pack
  paths from escaping their pack directory.
- `core/plugin.py` defines the contract implemented by every game plugin.
- `core/protocol.py` defines observations, step results, and game environments.
- `core/evaluation.py` defines the common final result.
- `core/registry.py` discovers installed plugins through Python entry points.
- `agent/` is reserved for the future LLM adapter.
- `runtime/` is reserved for the future separate-process isolation layer.

### Hidden-grid plugin

- `plugins/hidden-grid/pyproject.toml` registers the `hidden-grid` plugin.
- `catalog.py` validates the hidden-grid pack's catalog.
- `environment.py` applies actions, enforces the budget, and detects terminal
  states.
- `observations.py` converts private state into the safe public grid.
- `evaluator.py` maps terminal states to rewards.
- `plugin.py` connects those pieces to the game-neutral core contract.
- `test_hidden_grid.py` directly verifies the plugin's game behavior.

### Hidden-grid benchmark pack

- `benchmark.json` binds pack `core` to plugin `hidden-grid`.
- `catalog.json` defines the public task metadata and internal private-config
  reference.
- `public/agent-instructions.md` is the rule-free text intended for an agent.
- `public/action-schema.json` defines the four accepted actions.
- `public/observation-schema.json` defines the safe observation shape.
- `private/games/pacman-unknown/initial-state.json` contains the target and trap
  coordinates and must never be exposed to an evaluated model.
- `private/oracle/solver.py` proves to benchmark authors that a safe winning
  path exists within the budget. An oracle is a trusted known-good control used
  to validate a benchmark.

## Data flow

```text
task ID
  -> Hub finds benchmark pack
  -> manifest selects hidden-grid plugin
  -> plugin creates private environment
  -> environment returns public observation
  -> human/script chooses action
  -> environment changes hidden state
  -> repeat until won, trap, timeout, or incomplete
  -> Hub stores normalized result
  -> report aggregates completed runs
```

## Public/private boundary

The current repository separates files by convention:

```text
benchmarks/hidden-grid-core/public/   safe agent-facing material
benchmarks/hidden-grid-core/private/  rules and author-only controls
```

That directory split is necessary but not sufficient for real model testing.
An LLM with repository access could still inspect the private directory. The
next security milestone is to start the game behind a narrow communication
interface in a separate process or container and create an agent workspace
containing only the public files.

## Planned next milestones

1. Add a separate private game process and strict filesystem isolation.
2. Add automated leakage tests against observations, errors, and reports.
3. Add a provider-neutral LLM adapter in `src/gamescientist/agent/`.
4. Add seeded layouts and repeated-trial experiment configuration.
5. Add episode replay and richer aggregate reporting.
6. Author additional novel games without changing the game-neutral core.

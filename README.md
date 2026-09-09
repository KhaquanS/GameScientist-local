# GameScientist

GameScientist is an experimental benchmark for evaluating whether an LLM can
discover and solve a novel game through interaction alone. The LLM receives a
controlled observation-and-action interface; it does not receive the game's
rules, hidden state, source code, or private evaluator.

## Initial scope

This repository is currently a documentation-and-directory scaffold. It
contains no executable GameScientist code and no copied GameCodeBench source
code.

The first planned benchmark task is `hidden-grid/core/pacman-unknown`: a small
two-dimensional grid game with a hidden success condition, hidden hazards, and
a fixed move budget. The intended interaction loop is:

```text
observe -> choose one allowed move -> receive the next observation -> repeat
```

The private game implementation and evaluator will be kept separate from the
LLM-facing workspace. This separation is required for a valid hidden-rule
evaluation.

## Planned layout

```text
src/gamescientist/       Benchmark platform code (to be implemented)
plugins/hidden-grid/     Adapter for hidden-rule grid games (to be implemented)
benchmarks/hidden-grid-core/
                         Public task interface and private game assets
docs/                    Methodology, architecture, and authoring guidance
tests/                   Tests for correctness, reproducibility, and isolation
scripts/                 Developer maintenance commands
```

## Relationship to GameCodeBench

GameScientist is being designed from the GameCodeBench architecture. It plans
to reuse the general ideas of independently discovered game plugins,
versioned benchmark packs, run records, and reports. It will replace the
static code-submission workflow with an interactive game episode workflow.

## Next steps

1. Define the public observation/action protocol.
2. Define the private-game isolation boundary and leakage tests.
3. Create a minimal deterministic hidden-grid game.
4. Add an episode runner, evaluator, replay support, and reporting.

No benchmark score should be reported until the private-rule boundary and
reproducibility controls are implemented and tested.

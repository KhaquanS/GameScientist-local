# GameScientist repository rules

GameScientist evaluates agents on games whose rules are intentionally hidden.
Code under `benchmarks/**/private/` must never be copied into an evaluated
agent workspace, prompt, observation, error message, or public report.

Keep `src/gamescientist/` game-neutral. Game-specific behavior belongs in an
independently packaged plugin under `plugins/`, while versioned benchmark data
belongs under `benchmarks/`. Benchmark packs are read-only during a run;
generated state belongs under `.gamescientist/`.

Behavior changes require tests. Do not claim that real LLM evaluation is safe
until the model-facing process boundary and leakage tests are implemented.

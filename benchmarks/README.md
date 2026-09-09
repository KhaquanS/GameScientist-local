# Benchmark packs

Each directory below this root is a versioned, read-only benchmark pack.
Only files under a pack's `public/` directory may be copied into an evaluated
agent environment. Files under `private/` contain rules, evaluator inputs, or
validation controls and must never be exposed to the agent.

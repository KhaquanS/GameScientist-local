# Hidden-grid plugin

This independently packaged plugin connects GameScientist to deterministic
two-dimensional grid games. It owns the grid catalog parser, observation
renderer, action handling, terminal conditions, and reward mapping.

The plugin reads private task configuration only inside the benchmark process.
Its public task metadata never contains target coordinates, hazard coordinates,
or their meanings.

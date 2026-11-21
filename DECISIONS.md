# Decisions

One line per choice: the options weighed and the reason.

- 2026-11-21 Name: `handoffpact`. pypi.org/pypi/handoffpact/json answered 404 and registry.npmjs.org/handoffpact answered 404 on 2026-11-21, and the brief's search on 2026-11-20 found no well-known project. Backup `pactline` not needed. The repo name matches.
- 2026-11-21 Branch: `claude/project-thread-kd42dy`, not `claude/build-handoffpact`. The session's own git rules allow pushes to this branch only, and they win over the coordinator note. Branched from origin main (a45d76d).
- 2026-11-21 No runtime dependencies. Options: pydantic, jsonschema, plain stdlib. The brief names only tomllib, dataclasses and pytest, so the checker is plain Python.
- 2026-11-21 Contract format: one TOML file per edge with `[edge]`, `[fields.<name>]` and `[semantic] checks`. A typo in a field key or type raises ContractError, so a broken contract cannot pass everything quietly.
- 2026-11-21 ID references resolve a dotted path in the producer's input context. `orders[*].order_id` walks list items, and a list found at the path counts item by item.
- 2026-11-21 A semantic check that raises counts as a violation, not a crash. A broken check should stop the handoff, not the pipeline.
- 2026-11-21 Decorator context: the output check uses the agent's own input as context, because the brief says ID checks look in the producer's input context.

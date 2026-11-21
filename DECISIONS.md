# Decisions

One line per choice: the options weighed and the reason.

- 2026-11-21 Name: `handoffpact`. pypi.org/pypi/handoffpact/json answered 404 and registry.npmjs.org/handoffpact answered 404 on 2026-11-21, and the brief's search on 2026-11-20 found no well-known project. Backup `pactline` not needed. The repo name matches.
- 2026-11-21 Branch: `claude/project-thread-kd42dy`, not `claude/build-handoffpact`. The session's own git rules allow pushes to this branch only, and they win over the coordinator note. Branched from origin main (a45d76d).
- 2026-11-21 No runtime dependencies. Options: pydantic, jsonschema, plain stdlib. The brief names only tomllib, dataclasses and pytest, so the checker is plain Python.
- 2026-11-21 Contract format: one TOML file per edge with `[edge]`, `[fields.<name>]` and `[semantic] checks`. A typo in a field key or type raises ContractError, so a broken contract cannot pass everything quietly.
- 2026-11-21 ID references resolve a dotted path in the producer's input context. `orders[*].order_id` walks list items, and a list found at the path counts item by item.
- 2026-11-21 A semantic check that raises counts as a violation, not a crash. A broken check should stop the handoff, not the pipeline.
- 2026-11-21 Decorator context: the output check uses the agent's own input as context, because the brief says ID checks look in the producer's input context.
- 2026-11-21 Sample layout: the pipeline, its contracts, checks and corpus live in `src/handoffpact/sample/`, so they install with the package and CI needs no extra paths. The library proper stays in three files.
- 2026-11-21 Scenarios have two turns per customer, so the stale fault reuses the real turn 1 message on the same edge.
- 2026-11-21 The scripted model obeys every leaked instruction. Options: obey some, obey none, obey all. Obey all is the worst case and makes the harm of a leak visible without contracts.
- 2026-11-21 Leak phrases were written before the instruction patterns. Two of twelve slip past. I did not tune the patterns to catch them, to keep the leak number honest.
- 2026-11-21 Clean tickets include benign lines like "Please ignore my previous email". The patterns target model words (instructions, rules, policy, prompt, role tags), not "previous", so these do not raise false alarms.
- 2026-11-21 Blast radius counts later steps that finish on corrupted data plus delivery. A step that crashes is the stop and does not count. Maximum is four for a fault on the first edge.
- 2026-11-21 Fault mix is balanced: an equal number of runs per fault type. Edge and field come from the run's seed. Every injected fault must change the message.
- 2026-11-21 Detection means a contract stopped the run before delivery. Detection at the faulted edge is also stored. In stop mode they are the same, because the first violation stops the run.
- 2026-11-21 Run sizes: 2100 fault runs (300 per type) and 500 clean runs. The brief asks for at least 500 and 200. The whole run takes under two seconds, so larger sizes give tighter intervals for free.
- 2026-11-21 Two seeds: dev seed 1 and final seed 2026. The README headline uses seed 2026 and reports seed 1 next to it.
- 2026-11-21 Wilson interval upper bound is set to exactly 1.0 when every run is detected. Float rounding gave 0.9999999, which broke the lo <= rate <= hi check.
- 2026-11-21 The plugin entry point worked, so the fixture module fallback from the brief was not needed.
- 2026-11-21 Mutation check: with the `get` tracking removed from TrackedDict, the planted drift test failed to catch the drift. With the ref rule disabled, the ref tests failed. Both restored.
- 2026-11-21 Outside review fixes: items rules now apply to plain `list` fields, parse rejects rules that do not fit the field type, semantic checks may return True or False, and per-type run counts use divmod so no run is dropped. Results files are byte-identical in every counted field after the fixes.
- 2026-11-21 Branch is `claude/project-thread-kd42dy`, not `claude/build-handoffpact`, because this session may push only to that branch.

# Plan

The brief in docs/build/BUILD_PROMPT.md is the spec. This plan follows its build order. Each step ends with a passing test and a commit.

## Goal

A small Python library that checks every message one agent hands to another against a TOML contract, a sample four-agent pipeline, a fault injector and a benchmark that measures detection, false alarms and blast radius.

## Architecture

1. `contract.py` loads contracts and runs `check(edge, message, context)`.
2. `guard.py` holds the decorator that checks an agent's input and output.
3. `pytest_plugin.py` replays recorded producer outputs into a consumer.
4. `pipeline.py` runs intake, research, draft and review with a scripted model on an invented policy corpus.
5. `faults.py` corrupts one handoff per run.
6. `bench.py` runs seeded scenarios and scores them.
7. `docsgen.py` writes contract pages and a mermaid graph.
8. `report.py` writes the README tables and docs/index.html from results files.

## Steps

1. Initializer: memory files, init.sh, CI, secret scan. Test: `./init.sh`.
2. Contract format and parser. Test: bad contract files raise ContractError.
3. One validator per check type. Test: a bad message fails and a good one passes, for each type.
4. Decorator with stop and warn modes. Test: stop raises HandoffBlocked, warn logs and passes.
5. Sample pipeline. Test: 50 clean seeds pass every contract and produce a reply.
6. Fault injector. Test: each fault type changes the message for every edge where it applies.
7. Benchmark. Test: metrics on a small run, Wilson intervals, blast radius bounds.
8. pytest plugin. Test: pytester runs an example with a planted consumer drift and sees it fail.
9. Docs generator. Test: one page per contract and a mermaid block with four edges.
10. README, study kit, release check and hand-off.

## Assumptions

- Blast radius counts the downstream steps that run on corrupted data: each later agent plus the final delivery to the customer. The maximum is 4 for a fault on the first edge.
- A run counts as "detected" when a contract check stops it before delivery. Detection at the faulted edge itself is reported too.
- A false alarm is any contract violation on a clean run.
- The fault mix is balanced: an equal number of runs for each of the seven fault types. The edge and field are drawn with the run's seed.
- Each scenario has two turns, so the stale fault has an earlier value to reuse.

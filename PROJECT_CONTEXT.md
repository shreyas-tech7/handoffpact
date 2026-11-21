# Project context

## What it is
handoffpact checks every message one agent passes to another against a TOML contract. It stops a bad handoff before the next agent acts on it, and a benchmark measures detection, false alarms and blast radius with and without contracts.

## Status
v0.1.0-rc1 release candidate. All Done-means items pass. See PROGRESS.md.

## Stack
Python 3.11 or newer, standard library only at runtime (`tomllib`, `dataclasses`). pytest and ruff for development. No network, no keys, no model downloads.

## Commands
- `./init.sh`: venv, install, ruff, link check, all tests offline.
- `.venv/bin/handoffpact demo`: one clean ticket and one faulted ticket.
- `.venv/bin/handoffpact bench --faults 2100 --clean 500 --seed 2026 --out results/final-seed2026.json`
- `.venv/bin/handoffpact readme [--check]`: write or check the README numbers and docs/index.html.
- `.venv/bin/handoffpact docs`: contract pages and mermaid graph in docs/contracts.
- `.venv/bin/handoffpact record`: refresh the example recordings.

## Layout
- `src/handoffpact/contract.py` checker, `guard.py` decorator, `pytest_plugin.py` plugin.
- `src/handoffpact/faults.py`, `bench.py`, `docsgen.py`, `report.py`, `cli.py`.
- `src/handoffpact/sample/` pipeline, semantic checks, four contracts, invented policy corpus.
- `examples/contract_test/` the plugin example with a planted drift.
- `tests/` offline tests. `results/` benchmark JSON. `docs/` generated and written docs.

## Rules
- Never type numbers into the README. Run `handoffpact readme`.
- Never change results, reference values or tests to make code pass.
- Keep the library small: one file for the checker, one for the decorator, one for the plugin.
- Run gitleaks before each commit. Tests must stay offline (conftest guard).
- No em dashes, no dashes as punctuation, no semicolons in prose (tests/test_repo.py checks).

## Skills that fit
superpowers test-driven-development, systematic-debugging, verification-before-completion, requesting-code-review. Ponytail rules for code. Humanizer rules for docs.

## Do not read
`.venv/`, `results/*.json` beyond the `meta`, `overall` and `by_type` keys (they are large), `docs/build/BUILD_PROMPT.md` unless you need the brief.

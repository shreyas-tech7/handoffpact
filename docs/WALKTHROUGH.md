# Walkthrough

A tour of every file. Short sentences. One idea each.

## The idea in four lines

Agents pass messages to each other. Each message is a handoff. A contract says what a good handoff looks like. handoffpact checks each handoff and stops the bad ones.

## The library (src/handoffpact)

- `contract.py` is the checker. It is the heart of the project.
  - `parse` turns a TOML dict into a `Contract`. It rejects unknown keys and unknown types. A typo should fail loudly.
  - `load` reads one TOML file. `load_dir` reads a folder of them.
  - `resolve` walks a dotted path in the context. `orders[*].order_id` means "the order_id of every order".
  - `check(edge, message, context)` runs every rule and returns a `Result`.
  - `Result.ok` is True when there are no violations. Each `Violation` has a path, a rule and a detail.
  - `semantic("name")` registers a Python function as a named check. Contracts list checks by name.
- `guard.py` is the decorator.
  - `guard(outbound=...)` checks what an agent returns. The agent's own input is the context.
  - `guard(inbound=...)` checks what an agent receives.
  - Stop mode raises `HandoffBlocked`. Warn mode logs and lets the message pass.
- `pytest_plugin.py` is the pytest plugin.
  - pyproject.toml registers it under `pytest11`, so pytest loads it on its own.
  - The `handoff_pact` fixture has one method, `replay`.
  - `replay` checks each recorded message, then runs the consumer on it.
  - `TrackedDict` remembers every key the consumer reads.
  - A read of a key that the contract does not promise is consumer drift. The test fails.
- `faults.py` is the fault injector.
  - `inject(kind, message, rng, earlier)` returns a corrupted copy and a note about what changed.
  - The seven kinds are drop, wrong_type, invented_id, truncate, stale, leak and swap.
  - `LEAKS` holds the leaked instruction phrases. They were written before the detector.
- `bench.py` is the benchmark.
  - `plan_fault` picks the edge and builds the corrupted message for one seed.
  - `one_fault_run` runs the same ticket with contracts and without.
  - `run_bench` repeats that, balances the fault mix and adds clean runs for false alarms.
  - `wilson` gives the 95% interval for a rate. `mean_ci` gives a bootstrap interval for a mean.
- `docsgen.py` writes one Markdown page per contract and a mermaid graph.
  - `_label` escapes quotes, pipes and brackets, so odd names do not break the graph.
- `report.py` writes the README number blocks and `docs/index.html` from the results files.
- `cli.py` is the command line: check, demo, bench, record, docs and readme.

## The sample (src/handoffpact/sample)

- `policies.toml` is an invented policy corpus. No real company.
- `contracts/` holds the four contracts, one per edge.
- `checks.py` holds the named semantic checks, such as `order_facts_match` and `no_instruction_text`.
- `pipeline.py` holds the four agents and the runner.
  - `make_scenario(seed)` invents a customer, three orders and two tickets.
  - `intake`, `research`, `draft` and `review` are the agents. A scripted model drives them.
  - The scripted model obeys leaked instructions. That is the worst case, on purpose.
  - `run_turn` runs one ticket, checks each handoff and counts the blast radius.
  - `history` gives the turn 1 messages, which the stale fault reuses.

## Tests (tests)

- `conftest.py` blocks every network connection that is not local. `test_network_guard.py` proves it.
- `test_checks.py` has one bad case and one good case for each check type, plus the decorator.
- `test_pipeline.py` runs clean seeds through every contract and checks stop and warn modes.
- `test_faults.py` proves each fault changes the message.
- `test_bench.py` checks the intervals, the fault mix and the blast radius bounds.
- `test_plugin.py` runs the example suite with pytester and expects the planted drift to fail.
- `test_docsgen.py` checks the pages and the mermaid escaping.
- `test_repo.py` checks the README parts, the generated numbers, the writing rules and the shipped files.

## Example (examples/contract_test)

- `recordings/research_to_draft.jsonl` holds recorded research outputs, made by `handoffpact record`.
- `test_draft_contract.py` passes.
- `test_drifted_draft.py` plants a drift. Its unit test passes. Its contract test fails.

## Results and docs

- `results/final-seed2026.json` is the headline run. `results/dev-seed1.json` is the second seed.
- `docs/index.html` is the static results page. It opens from disk.
- `docs/contracts/` is the generated contract documentation.
- `docs/DEMO.md` is a real terminal transcript.
- `docs/social-preview.png` comes from `scripts/make_social_preview.py`.
- `scripts/check_links.py` checks every relative link and anchor.

## Memory files

- `PROGRESS.md`, `BLOCKERS.md`, `DECISIONS.md` and `feature_list.json` let a new session resume.
- `PROJECT_CONTEXT.md` is the short map. `CLAUDE.md` gives the read order.
- `docs/build/BUILD_PROMPT.md` is the brief, word for word.

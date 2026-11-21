# Interview questions and answers

Each answer points at the code and the results in this repo. Numbers come from `results/final-seed2026.json` (2026-11-21, scripted model, seed 2026) unless the answer says otherwise.

**1. What does a contract between two agents contain?**
One TOML file per edge. It names the producer and the consumer. It lists each field with its type, whether it is required, an enum, length limits, list sizes and an ID reference. It can forbid unknown fields. It names semantic checks, which are Python functions. See `src/handoffpact/sample/contracts/research_to_draft.toml` and `parse` in `src/handoffpact/contract.py`.

**2. Why check at the boundary and not at the end?**
An error is cheapest to stop where it starts. Once the drafter writes a refund from a stale total, the reviewer sees a well formed reply and approves it. The check at `research_to_draft` sees the total does not match the order list. In the benchmark, blast radius falls from 1.99 steps without contracts to 0.21 with them (`overall.blast_off` and `overall.blast_on`).

**3. What does blast radius measure?**
The number of later steps that run on corrupted data before something stops it. A step is each later agent plus the delivery to the customer. A fault on the first edge can reach at most four steps. The counter is in `run_turn` in `src/handoffpact/sample/pipeline.py`.

**4. What can contracts not catch?**
An answer that is wrong but well formed. A truncated question is still ticket text and still long enough, so 90 of the 115 misses are truncated questions at the first edge. A stale intent from last turn is still a valid enum. See the `missed` list in the results file and `by_type.truncate.detected` (210 of 300).

**5. Why do ID references look in the producer's input context?**
An agent should only cite things it was given. If research cites policy P-77 and P-77 was not in its corpus, it invented it. `check` resolves the `ref` path against the context, and `guard` passes the agent's own input as that context.

**6. How do you know the checks do not just fire on everything?**
False alarms on clean runs. 500 clean runs gave 0 alarms (Wilson upper bound 0.8%, `false_alarms`). The clean tickets include benign lines such as "Please ignore my previous email", which a careless instruction pattern would flag. The patterns in `src/handoffpact/sample/checks.py` target words that talk to a model, like "instructions" or a role tag.

**7. Why were the leak phrases written before the detector?**
To reduce overfitting. `LEAKS` in `src/handoffpact/faults.py` is varied on purpose, and two of the twelve phrases get past the patterns. `test_instruction_detector_on_leaks_and_on_clean_text` asserts that some get through. The detection rate for leaks (291 of 300) is still likely optimistic, because the same author wrote both.

**8. How does the pytest plugin catch consumer drift?**
`replay` wraps each recorded message in a `TrackedDict`. After the consumer runs, it compares the keys read with the contract fields. The example drafter reads `customer_tier` with `.get()`, which never raises. A plain unit test passes, and the contract test fails. See `examples/contract_test/test_drifted_draft.py`.

**9. Why stop mode by default, and what is warn mode for?**
A bad handoff should not reach the next agent. Warn mode lets a team add contracts to a live system, watch the violations and then switch to stop. `guard(mode="warn")` logs and calls `on_violation`.

**10. Why are semantic checks code and not LLM judgments?**
Code is exact, fast and free, and the brief keeps LLM judges out of scope. The benchmark runs 11000 ticket runs in under two seconds on one core (`meta.seconds`, `meta.pipeline_runs`).

**11. How are the intervals computed?**
Rates use the Wilson score interval (`wilson` in `src/handoffpact/bench.py`), which behaves well at 0% and 100%. Mean blast radius uses a seeded percentile bootstrap (`mean_ci`). A second seed (`results/dev-seed1.json`) gives 95.3% detection against 94.5% here.

**12. What would change with real models?**
The fault mix. Real models may fail more often with well formed but wrong content, which contracts miss. That is why the README says the faults are injected by script, and why the record mode run is listed as a manual step.

**13. Why a scripted model?**
Exact replays. The same seed gives the same run, so a with-contracts run and a without-contracts run differ only in the checks. It also costs nothing and needs no key.

**14. How do you keep the README honest?**
Numbers live between generated markers. `handoffpact readme` writes them from the results files, and `test_readme_numbers_match_results_files` fails if they drift. CI runs `readme --check`.

**15. Why not use Pydantic?**
Pydantic validates one object against a schema. It does not know about the producer's input, so it cannot say "this ID was invented". The brief also asks for the standard library only. The whole checker, `contract.py`, is about 250 lines.

**16. How would you drop this into an existing agent fleet?**
Write one TOML file per edge. Wrap each producer with `@guard(outbound=contract, mode="warn")`. Record real handoffs and add a `handoff_pact.replay` test for each consumer. Switch to stop mode once the warnings stop.

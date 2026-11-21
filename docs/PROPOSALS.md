# Proposals

Ideas that are not in the brief. Shreyas picks what gets built.

- A record mode run with a free model (the stretch item), about 30 runs, to count natural contract violations by type. Blocked on a reachable free provider.
- Nested field paths in contracts, such as `order.total`. The sample pipeline uses flat messages, so it was not needed.
- A contract diff command that tells which consumers break when a producer contract changes.
- A JSON Schema export for each contract, so other languages can reuse the field rules.
- Per edge counters in warn mode, written to a JSONL file, for a gradual rollout dashboard.

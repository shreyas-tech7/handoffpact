# Handover

Branch: `claude/project-thread-kd42dy` on origin `shreyas-tech7/handoffpact` and on the backup remote.

## Done
Every feature in feature_list.json passes. The release SHA is in CHANGELOG.md and docs/HUMAN_STEPS.md.

## Next
1. Human steps in docs/HUMAN_STEPS.md.
2. Optional stretch: record mode with a real model once a provider host is reachable.

## Commands
- `./init.sh`
- `.venv/bin/handoffpact bench --faults 2100 --clean 500 --seed 2026 --out results/final-seed2026.json && .venv/bin/handoffpact readme`
- `git push -u origin HEAD && git push backup HEAD && git ls-remote origin`

## Open decisions
None. The branch name follows the session's git rule (see DECISIONS.md).

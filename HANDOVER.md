# Handover

Branch: `claude/project-thread-kd42dy` on origin `shreyas-tech7/handoffpact` and on the backup remote.

## Done
Everything in feature_list.json except F12 passes. See PROGRESS.md.

## Next
1. Read the outside check result in docs/RELEASE_CHECK.md and fix what it finds.
2. Write the release SHA into CHANGELOG.md and docs/HUMAN_STEPS.md (replace RELEASE_SHA_PENDING).
3. Push to origin and backup, write the bundle, copy the report to /mnt/project-files/portfolio/reports/handoffpact.md, update the handoffpact row in QUEUE2.md.

## Commands
- `./init.sh`
- `.venv/bin/handoffpact bench --faults 2100 --clean 500 --seed 2026 --out results/final-seed2026.json && .venv/bin/handoffpact readme`
- `git push -u origin HEAD && git push backup HEAD && git ls-remote origin`

## Open decisions
None. The branch name follows the session's git rule (see DECISIONS.md).

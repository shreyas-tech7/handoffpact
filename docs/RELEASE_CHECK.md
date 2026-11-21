# Release check

Run on 2026-11-21 on branch `claude/project-thread-kd42dy`.

| Step | Command | Result |
| --- | --- | --- |
| Code review (Ponytail rules, by hand) | read the branch diff | Removed a lazy import in `pipeline.py`, made `agent_input` public instead of importing a private name in `cli.py`, closed `/proc/cpuinfo` with a context manager. No extra layers found. The library stays at three files |
| Security audit | skipped | The brief says skip it. No sign-in, personal data or payments |
| Secret scan, full history | `gitleaks git -v .` | no leaks found |
| Dependency audit | `pip-audit -r requirements (dev deps from the venv) --no-deps --disable-pip` | No known vulnerabilities found. The package has no runtime dependencies |
| Security lint | `ruff check --select S src scripts examples` | 7 findings, all accepted: 5 are S311 (seeded `random.Random` for the simulation, no crypto use) and 2 are S101 (assert in the example tests) |
| Workflow lint | `actionlint .github/workflows/*.yml` | clean |
| Links | `scripts/check_links.py` | 0 problems. External links listed as not checked |
| Humanizer rules (by hand) | `tests/test_repo.py::test_writing_rules` | README and docs pass: no em dashes, no dashes as punctuation, no semicolons in prose, no listed buzzwords |
| CI on GitHub | Actions runs on the branch | green on Python 3.11 (runs 1 and 2) |
| Outside check | separate reviewer subagent, fresh clone, `./init.sh` | All six Done-means items pass. The reviewer also found six weak spots. Fixed three with tests: items rules on a plain `list`, rules that do not fit the field type, and semantic checks that return True or False. Run counts that do not split evenly by seven are now kept. Logged the other three as limits in the README and BLOCKERS.md. Both benchmark files are unchanged after the fixes |
| Clean tree and flags | `git status`, feature_list.json | clean, every flag matches a passing check |

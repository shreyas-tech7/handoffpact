# Contributing

Thanks for your interest. This is a small project, so the rules are short.

1. Run `./init.sh` before and after your change. It installs the project, lints, checks links and runs every test offline.
2. Write a test that fails first. Name the broken case in its docstring.
3. Keep the library small. The checker, the decorator and the plugin are one file each.
4. Never type a number into the README. Run `.venv/bin/handoffpact readme` after a new benchmark run.
5. New ideas go to [docs/PROPOSALS.md](docs/PROPOSALS.md) first.
6. Run the secret scan before you commit: `gitleaks git --pre-commit --redact --staged`.

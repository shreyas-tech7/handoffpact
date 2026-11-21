# Tooling

| Tool | Source | Version | Why | Check result |
| --- | --- | --- | --- | --- |
| superpowers skills | already in the session (claude.ai account) | as installed | plans, TDD, debugging, verification, review | followed inline to save tokens |
| ponytail, caveman, humanizer, find-skills | `npx skills add ...` | none | code style, terse progress, doc pass, skill search | not installed. The permission system denied the first `npx skills add` on 2026-11-21, so no install was retried. The rules were applied by hand: small plain code, plain word docs |
| gitleaks | `go install github.com/zricethezav/gitleaks/v8@latest` | v8.30.1 (go install build) | secret scan before each commit and on full history | installed, no leaks |
| actionlint | `go install github.com/rhysd/actionlint/cmd/actionlint@latest` | v1.7.12 | workflow lint | installed, both workflows pass |
| pip-audit | `uv tool install pip-audit` | see docs/RELEASE_CHECK.md | dependency audit | see docs/RELEASE_CHECK.md |
| ruff | PyPI (dev extra) | at install time | lint, format, `--select S` | runs in init.sh |
| graphify, cisco-ai-skill-scanner, pre-commit | `uv tool install` | not installed | not needed: under 30 source files, no third-party skills installed, gitleaks runs directly | skipped |
| security-audit | session skill | not used | the brief says skip it: no sign-in, personal data or payments | skipped by design |

## Repos from the shared list (GITHUB_REPOS.md)

| Repo | Fit | What happened |
| --- | --- | --- |
| obra/superpowers | yes | already in the session, used inline |
| DietrichGebert/ponytail, JuliusBrussee/caveman, blader/humanizer | yes | install denied by the permission system, rules followed by hand |
| gitleaks/gitleaks | yes | used |
| google/osv-scanner, semgrep/semgrep | partly | api.osv.dev and semgrep.dev did not answer. pip-audit and ruff S rules instead |
| Graphify-Labs/graphify | no | small codebase |
| meta-llama/PurpleLlama, protectai deberta prompt injection model | idea only | huggingface.co blocked and the brief keeps LLM judges out of scope. The leak check stays a code pattern list. A model based leak check is a proposal |
| cisco-ai-defense/skill-scanner, mcp-scanner | no | no skills or MCP server installed |
| NVIDIA/garak | no | needs a model endpoint |
| OmniRoute, litellm, free-llm-api-resources | stretch only | key needed and provider hosts blocked. Listed in docs/HUMAN_STEPS.md |
| microsoft/playwright-mcp, crawl4ai, anatomy | no | no UI, no crawling, figure is a stretch |
| coreyhaines31/marketingskills | partly | README structure follows the brief. Not installed |

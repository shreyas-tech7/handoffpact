# Blockers

| Date | What failed | Exact error | What I did instead |
| --- | --- | --- | --- |
| 2026-11-21 | `npx -y skills add DietrichGebert/ponytail -g -a claude-code -y` | "Permission for this action was denied by the Claude Code auto mode classifier" | Did not retry any skill install. Applied the Ponytail, caveman and humanizer rules by hand. Superpowers skills were already in the session |
| 2026-11-21 | Probe of huggingface.co, api.groq.com, openrouter.ai, api.osv.dev | curl answered `000` (proxy refused CONNECT) | No record mode (stretch only). pip-audit instead of osv-scanner. See docs/ENVIRONMENT.md |
| 2026-11-21 | Outside review, known limits not fixed | Truncated question still passes `question_from_ticket`; intent not tied to ticket text; `TrackedDict` misses `dict()`, `.copy()` and `.items()` reads; blast radius counts steps by position | Listed in the README Limits section. Fixing the first two would mean tuning checks to the injected faults |

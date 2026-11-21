# Environment

Probed on 2026-11-21 with `curl -sS -o /dev/null -w '%{http_code}' -m 10 <url>`.

| Host | Answer | Used for |
| --- | --- | --- |
| https://pypi.org/pypi/handoffpact/json | 404 (reachable, name free) | Name check |
| https://registry.npmjs.org/handoffpact | 404 (reachable, name free) | Name check |
| https://huggingface.co | 000 (proxy refused) | Not needed |
| https://api.groq.com, https://openrouter.ai | 000 (proxy refused) | Stretch record mode only. Not run |
| https://api.osv.dev | 000 (proxy refused) | Not used. pip-audit instead |

Machine: Intel(R) Xeon(R) Processor @ 2.10GHz, 4 cores, Python 3.13.18, uv 0.11.32.
No provider key variables were set. The benchmark is pure Python on one core and needs no network.

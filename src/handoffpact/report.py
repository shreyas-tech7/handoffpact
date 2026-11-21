"""Write the README number blocks and docs/index.html from the results files.

Nobody types a number into the README. Each block sits between
`<!-- gen:NAME -->` and `<!-- /gen:NAME -->` and this module rewrites it.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

FINAL = "results/final-seed2026.json"
SECOND = "results/dev-seed1.json"
LABELS = {
    "drop": "dropped field",
    "wrong_type": "wrong type",
    "invented_id": "invented ID",
    "truncate": "truncated text",
    "stale": "stale value from turn 1",
    "leak": "instruction text in a data field",
    "swap": "two fields swapped",
}
BLOCK = re.compile(r"(<!-- gen:(\w+) -->\n)(.*?)(<!-- /gen:\2 -->)", re.S)


def pct(r: dict) -> str:
    return (
        f"{r['k']}/{r['n']} = {100 * r['rate']:.1f}% ({100 * r['lo']:.1f} to {100 * r['hi']:.1f})"
    )


def mean(m: list) -> str:
    return f"{m[0]:.2f} ({m[1]:.2f} to {m[2]:.2f})"


def _rows(res: dict) -> list[list[str]]:
    rows = []
    for kind, label in LABELS.items():
        t = res["by_type"][kind]
        rows.append(
            [
                label,
                pct(t["detected"]),
                mean(t["blast_on"]),
                mean(t["blast_off"]),
                f"{t['wrong_delivered_on']['k']} / {t['wrong_delivered_off']['k']}",
            ]
        )
    o = res["overall"]
    rows.append(
        [
            "all faults",
            pct(o["detected"]),
            mean(o["blast_on"]),
            mean(o["blast_off"]),
            f"{o['wrong_delivered_on']['k']} / {o['wrong_delivered_off']['k']}",
        ]
    )
    return rows


HEAD = [
    "Fault (injected by script)",
    "Stopped before delivery, 95% CI",
    "Blast radius with contracts",
    "Blast radius without",
    "Wrong answers delivered, with / without",
]


def blocks(root: Path) -> dict[str, str]:
    final = json.loads((root / FINAL).read_text())
    second = json.loads((root / SECOND).read_text())
    m, o, fa = final["meta"], final["overall"], final["false_alarms"]
    table = ["| " + " | ".join(HEAD) + " |", "| " + " | ".join(["---"] * len(HEAD)) + " |"]
    table += ["| " + " | ".join(r) + " |" for r in _rows(final)]
    mix = ", ".join(f"{LABELS[k]} {v}" for k, v in m["fault_mix"].items())
    s2 = second["overall"]
    results = "\n".join(
        [
            f"Run of {m['date']}, model: {m['model']}, seed {m['seed']}, file `{FINAL}`.",
            f"{m['fault_runs']} fault runs and {m['clean_runs']} clean runs.",
            "",
            *table,
            "",
            f"False alarms on clean runs: {pct(fa)}. The upper bound is the Wilson 95% bound for zero events.",
            "",
            f"Fault mix: {mix}. The edge and the field are drawn with each run's seed.",
            f"Without contracts, {pct(o['crash_stops_off'])} of fault runs stopped because a later agent crashed. The rest ran to the end.",
            "",
            f"Second run with another seed ({second['meta']['seed']}, file `{SECOND}`): stopped {pct(s2['detected'])}, "
            f"false alarms {pct(second['false_alarms'])}, blast radius {mean(s2['blast_on'])} with contracts "
            f"and {mean(s2['blast_off'])} without.",
            "",
            "Blast radius intervals are seeded percentile bootstrap intervals. Wrong answer counts are out of the runs in each row and are shown without an interval.",
        ]
    )
    per_run = 1000 * m["seconds"] / m["pipeline_runs"]
    cost = "\n".join(
        [
            f"Cost per task: ${m['cost_usd']:.2f}. The scripted model makes no API calls.",
            f"The whole benchmark ({m['pipeline_runs']} ticket runs) took {m['seconds']} s on {m['cores_used']} core of an {m['cpu']}, "
            f"Python {m['python']}, on {m['date']}. That is about {per_run:.2f} ms per ticket run, four contract checks included.",
        ]
    )
    status = (
        f"**Status:** v0.1.0-rc1 release candidate. Numbers come from `{FINAL}` "
        f"({m['date']}, {m['model']}, seed {m['seed']})."
    )
    return {"status": status, "results": results, "cost": cost}


def render_readme(text: str, gen: dict[str, str]) -> str:
    def sub(mo):
        name = mo.group(2)
        if name not in gen:
            return mo.group(0)
        return f"{mo.group(1)}{gen[name]}\n{mo.group(4)}"

    return BLOCK.sub(sub, text)


def render_html(root: Path) -> str:
    final = json.loads((root / FINAL).read_text())
    gen = blocks(root)
    m = final["meta"]
    head = "".join(f"<th>{html.escape(h)}</th>" for h in HEAD)
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in r) + "</tr>" for r in _rows(final)
    )
    fa = html.escape(pct(final["false_alarms"]))
    cost = html.escape(gen["cost"].replace("\n", " "))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>handoffpact results</title>
<style>
:root {{ --bg: #ffffff; --fg: #1f2328; --muted: #59636e; --line: #d1d9e0; --accent: #0969da; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg: #0d1117; --fg: #e6edf3; --muted: #9aa4ae; --line: #30363d; --accent: #6ea8ff; }} }}
body {{ background: var(--bg); color: var(--fg); font: 16px/1.5 system-ui, sans-serif; margin: 0 auto; max-width: 1100px; padding: 24px 16px; }}
h1 {{ margin-bottom: 4px; }} p {{ color: var(--muted); }}
.wrap {{ overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
th, td {{ border-bottom: 1px solid var(--line); padding: 8px; text-align: left; vertical-align: top; }}
th {{ color: var(--accent); }}
</style>
</head>
<body>
<h1 id="results">handoffpact results</h1>
<p>Run of {html.escape(m["date"])}, model: {html.escape(m["model"])}, seed {m["seed"]}. {m["fault_runs"]} fault runs, {m["clean_runs"]} clean runs. Faults are injected by script. Faults from real models can look different.</p>
<div class="wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>
<p>False alarms on clean runs: {fa}.</p>
<p>{cost}</p>
<p>Blast radius is the number of later steps (agents plus delivery to the customer) that run on corrupted data before something stops it. See <a href="../README.md">the README</a> and <a href="contracts/README.md">the contract graph</a>.</p>
</body>
</html>
"""


def write(root: Path, check: bool = False) -> list[str]:
    """Rewrite README.md and docs/index.html. With check=True, return the stale files."""
    root = Path(root)
    readme = root / "README.md"
    new_readme = render_readme(readme.read_text(encoding="utf-8"), blocks(root))
    new_html = render_html(root)
    targets = [(readme, new_readme), (root / "docs" / "index.html", new_html)]
    stale = []
    for path, text in targets:
        old = path.read_text(encoding="utf-8") if path.exists() else None
        if old != text:
            stale.append(str(path.relative_to(root)))
            if not check:
                path.write_text(text, encoding="utf-8")
    return stale

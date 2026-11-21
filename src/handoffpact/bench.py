"""The fault benchmark: seeded runs of the sample pipeline, with and without contracts.

For each fault run we corrupt one handoff and run the ticket twice: once with the four
contracts in stop mode and once with no checks. Clean runs measure false alarms.
"""

from __future__ import annotations

import math
import platform
import random
import time
from datetime import UTC, datetime

from .faults import FAULTS, inject
from .sample.pipeline import EDGES, history, make_scenario, run_turn


def cpu_model() -> str:
    try:
        for line in open("/proc/cpuinfo", encoding="utf-8"):
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or platform.machine()


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for k successes in n trials."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    lo = 0.0 if k == 0 else max(0.0, c - h)
    hi = 1.0 if k == n else min(1.0, c + h)
    return (lo, hi)


def mean_ci(xs: list[float], seed: int, reps: int = 2000) -> tuple[float, float, float]:
    """Mean with a 95% percentile bootstrap interval (seeded)."""
    if not xs:
        return (0.0, 0.0, 0.0)
    rng = random.Random(seed)
    n = len(xs)
    means = sorted(sum(rng.choices(xs, k=n)) / n for _ in range(reps))
    return (sum(xs) / n, means[int(0.025 * reps)], means[int(0.975 * reps) - 1])


def plan_fault(seed: int, kind: str, scenario: dict):
    """Pick the edge for this run's fault and return a fault callable, or None."""
    ticket = scenario["tickets"][1]
    clean = run_turn(ticket, use_contracts=False).messages
    earlier = history(scenario)
    rng = random.Random(f"{seed}-{kind}")
    order = list(range(len(EDGES)))
    rng.shuffle(order)
    for k in order:
        if k >= len(clean):
            continue
        state = random.Random(f"{seed}-{kind}-{k}")
        got = inject(kind, clean[k], state, earlier[k] if k < len(earlier) else None)
        if got is None:
            continue
        bad, info = got
        info = {**info, "edge": EDGES[k], "edge_index": k}

        def fault(i, msg, k=k, bad=bad):
            return bad if i == k else None

        return fault, info
    return None


def one_fault_run(seed: int, kind: str) -> dict | None:
    scenario = make_scenario(seed)
    ticket = scenario["tickets"][1]
    planned = plan_fault(seed, kind, scenario)
    if planned is None:
        return None
    fault, info = planned
    clean = run_turn(ticket, use_contracts=False)
    on = run_turn(ticket, use_contracts=True, fault=fault)
    off = run_turn(ticket, use_contracts=False, fault=fault)

    def wrong(r):
        return r.delivered and r.final != clean.final

    return {
        "seed": seed,
        **info,
        "detected": on.stopped_by == "contract",
        "detected_at_edge": on.stopped_by == "contract" and on.stop_edge == info["edge"],
        "rules": sorted({rule for _, _, rule in on.violations}),
        "blast_on": on.blast_radius,
        "blast_off": off.blast_radius,
        "stopped_off": off.stopped_by,
        "wrong_delivered_on": wrong(on),
        "wrong_delivered_off": wrong(off),
    }


def rate(k: int, n: int) -> dict:
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "rate": k / n if n else 0.0, "lo": lo, "hi": hi}


def run_bench(faults: int, clean: int, seed: int) -> dict:
    """`faults` fault runs split evenly over the fault types, plus `clean` clean runs."""
    t0 = time.perf_counter()
    runs, skipped = [], 0
    i = 0
    per_type = {k: 0 for k in FAULTS}
    want = faults // len(FAULTS)
    while min(per_type.values()) < want:
        s = seed + i
        kind = FAULTS[i % len(FAULTS)]
        i += 1
        if per_type[kind] >= want:
            continue
        r = one_fault_run(s, kind)
        if r is None:
            skipped += 1
            continue
        per_type[kind] += 1
        runs.append(r)
    false_alarms, alarm_rules = 0, {}
    clean_seed = seed + 1_000_000
    for j in range(clean):
        sc = make_scenario(clean_seed + j)
        r = run_turn(sc["tickets"][1], use_contracts=True, mode="warn")
        if r.violations:
            false_alarms += 1
            for edge, _path, rule in r.violations:
                key = f"{edge}:{rule}"
                alarm_rules[key] = alarm_rules.get(key, 0) + 1
    elapsed = time.perf_counter() - t0
    # Each fault run does 5 ticket runs (plan, history, clean, with and without contracts).
    pipeline_runs = 5 * len(runs) + clean

    by_type = {}
    for kind in FAULTS:
        rs = [r for r in runs if r["fault"] == kind]
        by_type[kind] = {
            "detected": rate(sum(r["detected"] for r in rs), len(rs)),
            "detected_at_edge": rate(sum(r["detected_at_edge"] for r in rs), len(rs)),
            "blast_on": mean_ci([r["blast_on"] for r in rs], seed),
            "blast_off": mean_ci([r["blast_off"] for r in rs], seed),
            "wrong_delivered_on": rate(sum(r["wrong_delivered_on"] for r in rs), len(rs)),
            "wrong_delivered_off": rate(sum(r["wrong_delivered_off"] for r in rs), len(rs)),
        }
    by_edge = {}
    for e in EDGES:
        rs = [r for r in runs if r["edge"] == e]
        by_edge[e] = {
            "n": len(rs),
            "detected": rate(sum(r["detected"] for r in rs), len(rs)),
            "blast_off": mean_ci([r["blast_off"] for r in rs], seed),
        }
    n = len(runs)
    return {
        "meta": {
            "date": datetime.now(UTC).strftime("%Y-%m-%d"),
            "seed": seed,
            "model": "scripted (no LLM)",
            "fault_runs": n,
            "clean_runs": clean,
            "fault_mix": per_type,
            "skipped_not_applicable": skipped,
            "seconds": round(elapsed, 2),
            "cpu": cpu_model(),
            "cores_used": 1,
            "pipeline_runs": pipeline_runs,
            "python": platform.python_version(),
            "cost_usd": 0.0,
        },
        "overall": {
            "detected": rate(sum(r["detected"] for r in runs), n),
            "detected_at_edge": rate(sum(r["detected_at_edge"] for r in runs), n),
            "blast_on": mean_ci([r["blast_on"] for r in runs], seed),
            "blast_off": mean_ci([r["blast_off"] for r in runs], seed),
            "wrong_delivered_on": rate(sum(r["wrong_delivered_on"] for r in runs), n),
            "wrong_delivered_off": rate(sum(r["wrong_delivered_off"] for r in runs), n),
            "crash_stops_off": rate(sum(bool(r["stopped_off"]) for r in runs), n),
        },
        "false_alarms": {**rate(false_alarms, clean), "rules": alarm_rules},
        "by_type": by_type,
        "by_edge": by_edge,
        "missed": [r for r in runs if not r["detected"]][:40],
        "runs": runs,
    }

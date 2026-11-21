"""Command line: check, demo, bench, record, docs and readme."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .contract import check, load


def _demo() -> int:
    from .sample.pipeline import EDGES, history, make_scenario, run_turn

    seed = next(
        s
        for s in range(1000)
        if run_turn(make_scenario(s)["tickets"][1]).final["refund_amount"] > 0
    )
    sc = make_scenario(seed)
    ticket = sc["tickets"][1]
    print(f"scenario seed {seed}, ticket {ticket['ticket_id']}: {ticket['text']}")
    run = run_turn(ticket)
    for edge, msg in zip(EDGES, run.messages, strict=True):
        print(f"\n[{edge}] contract ok")
        print(json.dumps(msg, indent=2))
    old = history(sc)[1]["order_total"]
    print(f"\nNow research hands over a stale order_total ({old}) from the turn 1 order.")

    def fault(k, msg):
        return {**msg, "order_total": old} if k == 1 else None

    on = run_turn(ticket, fault=fault)
    off = run_turn(ticket, use_contracts=False, fault=fault)
    print(
        f"with contracts: stopped by {on.stopped_by} at {on.stop_edge}, blast radius {on.blast_radius}"
    )
    for edge, path, rule in on.violations:
        print(f"  violation {edge}: {path} {rule}")
    print(f"without contracts: delivered={off.delivered}, blast radius {off.blast_radius}")
    if off.final:
        print(f"  reply sent: {off.final['reply']}")
    return 0


def _record(out: Path, n: int) -> int:
    from .sample.pipeline import agent_input, intake, make_scenario, research

    lines = []
    for seed in range(n):
        ticket = make_scenario(seed)["tickets"][1]
        inp = agent_input(1, ticket, intake(ticket))
        lines.append(json.dumps({"message": research(inp), "context": inp}, sort_keys=True))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {n} recordings to {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="handoffpact", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="check one message against a contract")
    c.add_argument("contract")
    c.add_argument("message", help="JSON file with the message")
    c.add_argument("--context", help="JSON file with the producer's input context")
    sub.add_parser("demo", help="run one ticket, then the same ticket with a fault")
    b = sub.add_parser("bench", help="run the fault benchmark")
    b.add_argument("--faults", type=int, default=2100)
    b.add_argument("--clean", type=int, default=500)
    b.add_argument("--seed", type=int, default=2026)
    b.add_argument("--out", required=True)
    r = sub.add_parser("record", help="record research outputs for the contract test example")
    r.add_argument("--out", default="examples/contract_test/recordings/research_to_draft.jsonl")
    r.add_argument("-n", type=int, default=20)
    d = sub.add_parser("docs", help="write contract pages and a mermaid graph")
    d.add_argument("contracts", nargs="?", default=None)
    d.add_argument("--out", default="docs/contracts")
    m = sub.add_parser("readme", help="write README tables and docs/index.html from results/")
    m.add_argument("--check", action="store_true", help="fail if the files are out of date")
    m.add_argument("--root", default=".")
    args = ap.parse_args(argv)

    if args.cmd == "check":
        contract = load(args.contract)
        msg = json.loads(Path(args.message).read_text())
        ctx = json.loads(Path(args.context).read_text()) if args.context else {}
        from .sample import checks  # noqa: F401  (registers the sample's semantic checks)

        res = check(contract, msg, ctx)
        if res.ok:
            print(f"{contract.name}: pass")
            return 0
        for v in res.violations:
            print(f"{contract.name}: {v}")
        return 1
    if args.cmd == "demo":
        return _demo()
    if args.cmd == "bench":
        from .bench import run_bench

        res = run_bench(args.faults, args.clean, args.seed)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        o = res["overall"]
        print(
            f"{res['meta']['fault_runs']} fault runs, {res['meta']['clean_runs']} clean runs, "
            f"{res['meta']['seconds']}s"
        )
        print(f"detected {o['detected']['k']}/{o['detected']['n']}")
        print(f"false alarms {res['false_alarms']['k']}/{res['false_alarms']['n']}")
        print(
            f"blast radius {o['blast_on'][0]:.2f} with contracts, {o['blast_off'][0]:.2f} without"
        )
        return 0
    if args.cmd == "record":
        return _record(Path(args.out), args.n)
    if args.cmd == "docs":
        from .docsgen import generate
        from .sample.pipeline import CONTRACTS_DIR, EDGES

        src = Path(args.contracts) if args.contracts else CONTRACTS_DIR
        order = EDGES if src.resolve() == CONTRACTS_DIR.resolve() else None
        for p in generate(src, args.out, order=order):
            print("wrote", p)
        return 0
    if args.cmd == "readme":
        from .report import write

        stale = write(Path(args.root), check=args.check)
        if args.check and stale:
            print("out of date:", ", ".join(stale))
            return 1
        print("up to date" if args.check else "written")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())

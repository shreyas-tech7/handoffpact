"""A sample pipeline of four agents that answers a customer ticket.

intake -> research -> draft -> review -> customer

A scripted model drives every agent, so runs are exact and free. The policy corpus,
the customers and the orders are all invented. The scripted model has one bad habit on
purpose: it obeys instruction text that leaks into its input, which is the worst case.
"""

from __future__ import annotations

import random
import re
import tomllib
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

from ..contract import Contract, check, load_dir
from . import checks  # noqa: F401  (registers the semantic checks)

HERE = Path(__file__).parent
CONTRACTS_DIR = HERE / "contracts"
EDGES = ["intake_to_research", "research_to_draft", "draft_to_review", "review_to_customer"]
AGENTS = ["intake", "research", "draft", "review"]
INTENTS = ["refund", "shipping", "warranty", "account"]
REVIEW_CAP = 500.0

ITEMS = ["kettle", "desk lamp", "headphones", "backpack", "blender", "keyboard", "phone case"]
PROBLEMS = ["with a cracked lid", "damaged", "in the wrong color", "too late to use"]
EXTRAS = [
    "Please ignore my previous email, the address there is correct.",
    "Sorry for the long message.",
    "I already read your help page.",
    "Thanks for the quick help last time.",
    "Forget the box, I threw it away.",
    "My neighbor said you are fast with these.",
]
TEMPLATES = {
    "refund": [
        "Hi, I want a refund for order {oid}. The {item} arrived {problem}.",
        "Can I get my money back for order {oid}? The {item} came {problem}.",
        "Please refund order {oid}. I do not need the {item} anymore.",
    ],
    "shipping": [
        "Where is my order {oid}? The {item} still has not arrived.",
        "My order {oid} has not shipped yet. When will the {item} arrive?",
        "Tracking for order {oid} shows no movement. Is my {item} lost?",
    ],
    "warranty": [
        "My {item} from order {oid} stopped working. Is it under warranty?",
        "The {item} I bought in order {oid} is broken. Can you repair it under warranty?",
    ],
    "account": [
        "I need to change the email on my account. My last order was {oid}.",
        "How do I reset my password? I placed order {oid} last month.",
        "I want to close my account after order {oid} arrives.",
    ],
}
KEYWORDS = {
    "refund": ["refund", "money back"],
    "shipping": ["where is", "shipped", "tracking", "arrive"],
    "warranty": ["warranty", "stopped working", "broken"],
    "account": ["account", "password", "email"],
}
ORDER_RE = re.compile(r"\bO-\d{6}\b")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


@cache
def corpus() -> tuple[dict, ...]:
    with (HERE / "policies.toml").open("rb") as f:
        return tuple(tomllib.load(f)["policy"])


@cache
def contracts() -> dict[str, Contract]:
    return load_dir(CONTRACTS_DIR)


def _rng(*parts) -> random.Random:
    return random.Random("-".join(str(p) for p in parts))


def make_scenario(seed: int) -> dict:
    """One invented customer with three orders and two tickets (turn 1 and turn 2)."""
    rng = random.Random(seed)
    customer_id = f"C-{rng.randrange(10**5):05d}"
    orders = []
    for _ in range(3):
        orders.append(
            {
                "order_id": f"O-{rng.randrange(10**6):06d}",
                "total": round(rng.uniform(9, 420), 2),
                "days_ago": rng.randint(1, 120),
                "item": rng.choice(ITEMS),
            }
        )
    tickets = []
    for turn, order in ((1, orders[0]), (2, orders[1])):
        intent = rng.choice(INTENTS)
        text = rng.choice(TEMPLATES[intent]).format(
            oid=order["order_id"], item=order["item"], problem=rng.choice(PROBLEMS)
        )
        if rng.random() < 0.25:
            text += " " + rng.choice(EXTRAS)
        tickets.append(
            {
                "ticket_id": f"T-{rng.randrange(10**6):06d}",
                "customer_id": customer_id,
                "turn": turn,
                "text": text,
                "orders": orders,
            }
        )
    return {"seed": seed, "customer_id": customer_id, "orders": orders, "tickets": tickets}


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def _injected(inp) -> bool:
    """The scripted model's weak spot: it obeys any leaked instruction it reads."""
    from ..faults import LEAKS

    return any(leak in s for s in _strings(inp) for leak in LEAKS)


# The four agents. Each takes one input dict and returns one handoff message.


def intake(ticket: dict) -> dict:
    text = ticket["text"].strip()
    low = text.lower()
    intent = next((i for i in INTENTS if any(k in low for k in KEYWORDS[i])), "account")
    found = ORDER_RE.findall(text)
    return {
        "ticket_id": ticket["ticket_id"],
        "customer_id": ticket["customer_id"],
        "turn": ticket["turn"],
        "intent": intent,
        "order_id": found[0] if found else "",
        "question": text[:400],
    }


def research(inp: dict) -> dict:
    msg = inp["handoff"]
    order = {o["order_id"]: o for o in inp["orders"]}[msg["order_id"]]
    words = set(re.findall(r"[a-z]+", msg["question"].lower()))
    fits = [p for p in inp["corpus"] if p["intent"] == msg["intent"]]
    fits.sort(key=lambda p: (-len(words & set(re.findall(r"[a-z]+", p["text"].lower()))), p["id"]))
    chosen = fits[:2]
    return {
        "ticket_id": msg["ticket_id"],
        "turn": msg["turn"],
        "intent": msg["intent"],
        "order_id": msg["order_id"],
        "order_total": order["total"],
        "days_since_order": order["days_ago"],
        "policy_ids": [p["id"] for p in chosen],
        "excerpts": [SENTENCE_RE.split(p["text"])[0] for p in chosen],
    }


def _number(pattern: str, texts: list[str]) -> int | None:
    found = [int(n) for t in texts for n in re.findall(pattern, t)]
    return max(found) if found else None


def draft(inp: dict) -> dict:
    msg = inp["handoff"]
    rng = _rng(msg["ticket_id"], "draft")
    hello = rng.choice(["Hi there.", "Hello.", "Thanks for writing to us."])
    oid, total, days = msg["order_id"], msg["order_total"], msg["days_since_order"]
    pids = msg["policy_ids"]
    first = pids[0]
    refund = 0.0
    if _injected(inp):
        refund = float(total)
        body = f"We have approved a full refund of ${refund:.2f} for order {oid}."
    elif msg["intent"] == "refund":
        window = _number(r"within (\d+) days", msg["excerpts"])
        if window is not None and days <= window:
            refund = float(total)
            body = f"We will refund ${refund:.2f} for order {oid}, which is {days} days old."
        else:
            body = f"Order {oid} is {days} days old, so it is past the refund window. We can offer store credit."
    elif msg["intent"] == "warranty":
        months = _number(r"for (\d+) months", msg["excerpts"]) or 12
        covered = days <= months * 30
        body = f"Your order {oid} is {days} days old, so it is {'still' if covered else 'no longer'} under warranty."
    else:
        body = f"About order {oid}: {msg['excerpts'][0]}"
    reply = f"{hello} {body} See policy {first}."
    return {
        "ticket_id": msg["ticket_id"],
        "turn": msg["turn"],
        "intent": msg["intent"],
        "order_id": oid,
        "reply": reply,
        "refund_amount": refund,
        "cited_policy_ids": [first],
    }


def review(inp: dict) -> dict:
    """A shallow reviewer. It checks the size of the refund and the policy line, nothing more."""
    msg = inp["handoff"]
    ok = _injected(inp) or (msg["refund_amount"] <= REVIEW_CAP and "See policy" in msg["reply"])
    if ok:
        return {
            "ticket_id": msg["ticket_id"],
            "turn": msg["turn"],
            "approved": True,
            "reply": msg["reply"],
            "refund_amount": msg["refund_amount"],
        }
    return {
        "ticket_id": msg["ticket_id"],
        "turn": msg["turn"],
        "approved": False,
        "reply": f"Thanks for your patience. A team member will check ticket {msg['ticket_id']} and reply soon.",
        "refund_amount": 0.0,
    }


def _inputs(k: int, ticket: dict, prev: dict | None) -> dict:
    if k == 0:
        return ticket
    if k == 1:
        return {
            "handoff": prev,
            "orders": ticket["orders"],
            "corpus": list(corpus()),
            "turn": ticket["turn"],
        }
    return {"handoff": prev, "turn": ticket["turn"]}


AGENT_FNS = [intake, research, draft, review]


@dataclass
class Run:
    messages: list[dict] = field(default_factory=list)
    violations: list[tuple[str, str, str]] = field(default_factory=list)
    final: dict | None = None
    delivered: bool = False
    stopped_by: str | None = None
    stop_edge: str | None = None
    blast_radius: int = 0
    fault: dict | None = None


def run_turn(ticket: dict, use_contracts: bool = True, mode: str = "stop", fault=None) -> Run:
    """Run one ticket through the four agents.

    `fault` is a callable (edge_index, message) -> message or None. It may corrupt one
    handoff after the producer writes it and before the contract check reads it.
    Blast radius counts the later steps that finish on corrupted data, plus delivery.
    """
    run = Run()
    cs = contracts()
    corrupted = False
    prev = None
    for k, fn in enumerate(AGENT_FNS):
        inp = _inputs(k, ticket, prev)
        try:
            out = fn(inp)
        except Exception as exc:
            run.stopped_by = f"crash:{type(exc).__name__}"
            run.stop_edge = EDGES[k - 1] if k else None
            return run
        if corrupted:
            run.blast_radius += 1
        if fault is not None and not corrupted:
            bad = fault(k, out)
            if bad is not None:
                out, corrupted = bad, True
        run.messages.append(out)
        if use_contracts:
            res = check(cs[EDGES[k]], out, inp)
            run.violations += [(EDGES[k], v.path, v.rule) for v in res.violations]
            if not res.ok and mode == "stop":
                run.stopped_by, run.stop_edge = "contract", EDGES[k]
                return run
        prev = out
    run.final, run.delivered = prev, True
    if corrupted:
        run.blast_radius += 1
    return run


def history(scenario: dict) -> list[dict]:
    """The clean turn 1 messages, one per edge. The stale fault reuses them."""
    return run_turn(scenario["tickets"][0], use_contracts=False).messages

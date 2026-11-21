"""Named semantic checks for the sample pipeline. Each gets (message, context).

Context is the producer's input. A check returns a problem string, a list of them,
or None when the message is fine.
"""

from __future__ import annotations

import re

from ..contract import semantic

# Generic signs of instruction text inside a data field. These target words that talk
# to a model (instructions, rules, prompt, a role tag), not ordinary customer phrasing.
INSTRUCTION_PATTERNS = [
    re.compile(p, re.I)
    for p in [
        r"\b(ignore|disregard|forget|override)\b[^.]{0,60}\b(instructions?|rules?|polic(y|ies)|prompt|guidelines?)\b",
        r"\b(system|assistant|admin|developer)\s*:",
        r"\bnew instructions?\b",
        r"\byou (must|should|will) now\b",
        r"\bto the (ai |drafting |review |reviewer )?(agent|assistant|model)\b",
        r"</?\s*(data|system|instructions?)\s*>",
    ]
]


def _strings(value, path="$"):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from _strings(v, f"{k}" if path == "$" else f"{path}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _strings(v, f"{path}[{i}]")


@semantic("no_instruction_text")
def no_instruction_text(msg, ctx):
    out = []
    for path, s in _strings(msg):
        for pat in INSTRUCTION_PATTERNS:
            m = pat.search(s)
            if m:
                out.append(f"{path} holds instruction text {m.group(0)!r}")
                break
    return out


@semantic("order_id_in_ticket")
def order_id_in_ticket(msg, ctx):
    if msg.get("order_id") not in ctx.get("text", ""):
        return f"order {msg.get('order_id')!r} is not named in the ticket"
    return None


@semantic("question_from_ticket")
def question_from_ticket(msg, ctx):
    q = msg.get("question")
    if isinstance(q, str) and q not in ctx.get("text", ""):
        return "question is not text from the ticket"
    return None


def _order(ctx, order_id):
    return {o["order_id"]: o for o in ctx.get("orders", [])}.get(order_id)


@semantic("order_facts_match")
def order_facts_match(msg, ctx):
    order = _order(ctx, msg.get("order_id"))
    if order is None:
        return f"order {msg.get('order_id')!r} is not in the order list"
    out = []
    if msg.get("order_total") != order["total"]:
        out.append(f"order_total {msg.get('order_total')!r} != {order['total']}")
    if msg.get("days_since_order") != order["days_ago"]:
        out.append(f"days_since_order {msg.get('days_since_order')!r} != {order['days_ago']}")
    return out


@semantic("policies_fit_intent")
def policies_fit_intent(msg, ctx):
    intents = {p["id"]: p["intent"] for p in ctx.get("corpus", [])}
    ids = msg.get("policy_ids") if isinstance(msg.get("policy_ids"), list) else []
    bad = [
        i
        for i in ids
        if isinstance(i, str) and intents.get(i, msg.get("intent")) != msg.get("intent")
    ]
    return [f"policy {i} is not a {msg.get('intent')} policy" for i in bad]


@semantic("excerpts_are_sentences")
def excerpts_are_sentences(msg, ctx):
    texts = {p["id"]: p["text"] for p in ctx.get("corpus", [])}
    ids = msg.get("policy_ids") if isinstance(msg.get("policy_ids"), list) else []
    sources = [texts.get(i, "") for i in ids if isinstance(i, str)]
    out = []
    for i, e in enumerate(msg.get("excerpts") or []):
        if not isinstance(e, str):
            continue
        if not e.rstrip().endswith((".", "!", "?")):
            out.append(f"excerpts[{i}] does not end a sentence")
        elif not any(e in s for s in sources):
            out.append(f"excerpts[{i}] is not from a cited policy")
    return out


@semantic("refund_matches_total")
def refund_matches_total(msg, ctx):
    """The quoted refund amount matches the order total, and the reply quotes it."""
    research = ctx.get("handoff", {})
    amount = msg.get("refund_amount")
    if not isinstance(amount, int | float) or isinstance(amount, bool):
        return None  # the type rule reports it
    if amount not in (0, research.get("order_total")):
        return f"refund {amount} is neither 0 nor the order total {research.get('order_total')}"
    if amount > 0 and f"${amount:.2f}" not in str(msg.get("reply", "")):
        return f"reply does not quote the refund ${amount:.2f}"
    if amount > 0 and research.get("intent") != "refund":
        return f"refund offered on a {research.get('intent')} ticket"
    return None


@semantic("reply_cites_policies")
def reply_cites_policies(msg, ctx):
    reply = str(msg.get("reply", ""))
    ids = msg.get("cited_policy_ids") if isinstance(msg.get("cited_policy_ids"), list) else []
    return [f"reply does not cite {i}" for i in ids if str(i) not in reply]


@semantic("reply_is_complete")
def reply_is_complete(msg, ctx):
    reply = msg.get("reply")
    if isinstance(reply, str) and not reply.rstrip().endswith((".", "!", "?")):
        return "reply stops mid sentence"
    return None


@semantic("review_keeps_draft")
def review_keeps_draft(msg, ctx):
    d = ctx.get("handoff", {})
    if msg.get("approved") is True:
        out = []
        if msg.get("reply") != d.get("reply"):
            out.append("approved reply is not the drafted reply")
        if msg.get("refund_amount") != d.get("refund_amount"):
            out.append("approved refund is not the drafted refund")
        return out
    if msg.get("approved") is False and msg.get("refund_amount") not in (0, 0.0):
        return "an escalated ticket carries a refund"
    return None

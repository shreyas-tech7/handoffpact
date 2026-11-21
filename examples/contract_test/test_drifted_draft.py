"""A planted consumer drift. A new drafter reads `customer_tier`, which research never
promised. A plain unit test passes, because `.get()` quietly returns the default. The
contract test fails, because the consumer now depends on a field outside the contract."""

from pathlib import Path

from handoffpact.sample.pipeline import CONTRACTS_DIR, draft

RECORDINGS = Path(__file__).parent / "recordings" / "research_to_draft.jsonl"
CONTRACT = CONTRACTS_DIR / "research_to_draft.toml"


def drifted_draft(inp):
    out = draft(inp)
    if inp["handoff"].get("customer_tier", "standard") == "gold":
        out["reply"] += " As a gold member you also get free express shipping."
    return out


def test_drifted_draft_unit():
    import json

    first = json.loads(RECORDINGS.read_text().splitlines()[0])
    assert drifted_draft({"handoff": first["message"]})["reply"]


def test_drifted_draft_keeps_the_contract(handoff_pact):
    handoff_pact.replay(CONTRACT, RECORDINGS, lambda m: drifted_draft({"handoff": m}))

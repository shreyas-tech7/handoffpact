"""A consumer-driven contract test: replay recorded research outputs into the drafter."""

from pathlib import Path

from handoffpact.sample.pipeline import CONTRACTS_DIR, draft

RECORDINGS = Path(__file__).parent / "recordings" / "research_to_draft.jsonl"
CONTRACT = CONTRACTS_DIR / "research_to_draft.toml"


def test_draft_keeps_the_contract(handoff_pact):
    outputs = handoff_pact.replay(CONTRACT, RECORDINGS, lambda m: draft({"handoff": m}))
    assert all(o["reply"] for o in outputs)

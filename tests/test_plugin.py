"""The pytest plugin catches a planted consumer drift in the example contract test."""

import json
import shutil
from pathlib import Path

import pytest

from handoffpact.pytest_plugin import DriftError, HandoffPact, TrackedDict, read_recordings
from handoffpact.sample.pipeline import CONTRACTS_DIR, draft

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "contract_test"
CONTRACT = CONTRACTS_DIR / "research_to_draft.toml"


def test_example_suite_catches_the_planted_drift(pytester):
    """Broken case: test_drifted_draft.py reads a field the contract never promised."""
    shutil.copytree(EXAMPLE, pytester.path / "contract_test")
    result = pytester.runpytest("contract_test", "-p", "no:cacheprovider")
    result.assert_outcomes(passed=2, failed=1)
    result.stdout.fnmatch_lines(["*consumer drift*customer_tier*research_to_draft*"])
    result.stdout.fnmatch_lines(["*FAILED*test_drifted_draft_keeps_the_contract*"])


def test_plugin_is_registered_by_entry_point(pytester):
    pytester.makepyfile("def test_x(handoff_pact):\n    assert handoff_pact\n")
    pytester.runpytest().assert_outcomes(passed=1)


def _recs(n=5):
    return read_recordings(EXAMPLE / "recordings" / "research_to_draft.jsonl")[:n]


def test_clean_replay_returns_outputs():
    outs = HandoffPact().replay(CONTRACT, _recs(), lambda m: draft({"handoff": m}))
    assert len(outs) == 5


def test_producer_drift_is_caught():
    """Broken case: a recording where research renamed `excerpts` to `quotes`."""
    recs = _recs(2)
    msg = dict(recs[0]["message"])
    msg["quotes"] = msg.pop("excerpts")
    recs[0] = {**recs[0], "message": msg}
    with pytest.raises(DriftError, match="producer drift"):
        HandoffPact().replay(CONTRACT, recs, lambda m: draft({"handoff": m}))


def test_consumer_crash_is_caught():
    def broken(m):
        return m["order_total"] / 0

    with pytest.raises(DriftError, match="consumer raised ZeroDivisionError"):
        HandoffPact().replay(CONTRACT, _recs(1), broken)


def test_empty_recordings_fail():
    with pytest.raises(DriftError, match="no recordings"):
        HandoffPact().replay(CONTRACT, [], lambda m: m)


def test_tracked_dict_records_reads():
    t = TrackedDict({"a": 1})
    t["a"], t.get("b"), "c" in t
    assert t.reads == {"a", "b", "c"}


def test_recordings_keep_the_contract():
    for rec in _recs(20):
        assert json.dumps(rec)

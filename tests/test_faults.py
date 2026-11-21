"""The fault injector: every fault type changes the message where it applies."""

import random

import pytest

from handoffpact.faults import FAULTS, LEAKS, inject
from handoffpact.sample import pipeline as p
from handoffpact.sample.checks import no_instruction_text


def _messages(seed):
    sc = p.make_scenario(seed)
    return p.run_turn(sc["tickets"][1], use_contracts=False).messages, p.history(sc)


@pytest.mark.parametrize("kind", FAULTS)
def test_fault_changes_the_message(kind):
    applied = 0
    for seed in range(20):
        msgs, earlier = _messages(seed)
        for k, msg in enumerate(msgs):
            got = inject(kind, msg, random.Random(seed), earlier[k])
            if got is None:
                continue
            bad, info = got
            assert bad != msg, (kind, info)
            assert info["fault"] == kind and info["field"]
            applied += 1
    assert applied >= 20


def test_inject_does_not_touch_the_original():
    msgs, earlier = _messages(1)
    before = repr(msgs[1])
    for kind in FAULTS:
        inject(kind, msgs[1], random.Random(0), earlier[1])
    assert repr(msgs[1]) == before


def test_specific_faults():
    msgs, earlier = _messages(2)
    m = msgs[1]
    assert "order_id" not in inject("drop", {"order_id": "O-1"}, random.Random(0))[0]
    bad, info = inject("stale", m, random.Random(0), earlier[1])
    assert bad[info["field"]] == earlier[1][info["field"]]
    bad, info = inject("leak", m, random.Random(0))
    assert any(leak in str(bad) for leak in LEAKS)
    bad, info = inject("swap", {"a": "x", "b": "y"}, random.Random(0))
    assert bad == {"a": "y", "b": "x"}
    assert inject("stale", m, random.Random(0), None) is None
    assert inject("invented_id", {"n": 3}, random.Random(0)) is None
    with pytest.raises(ValueError):
        inject("melt", m, random.Random(0))


def test_instruction_detector_on_leaks_and_on_clean_text():
    """Report, not tune: count how many leak phrasings the generic patterns catch."""
    caught = sum(bool(no_instruction_text({"t": leak}, {})) for leak in LEAKS)
    assert 6 <= caught < len(LEAKS)  # some phrasings get through, on purpose
    for extra in p.EXTRAS:
        assert no_instruction_text({"t": extra}, {}) == []

"""One test per check type: a bad message fails and a good message passes."""

import pytest

from handoffpact import ContractError, HandoffBlocked, check, guard, parse, semantic

CONTRACT = {
    "edge": {"name": "a_to_b", "producer": "a", "consumer": "b"},
    "fields": {
        "ticket_id": {"type": "str", "ref": "ticket_id"},
        "order_id": {"type": "str", "ref": "orders[*].order_id"},
        "intent": {"type": "str", "enum": ["refund", "shipping"]},
        "question": {"type": "str", "min_length": 5, "max_length": 40},
        "total": {"type": "float"},
        "count": {"type": "int"},
        "urgent": {"type": "bool"},
        "tags": {"type": "list[str]", "min_items": 1, "max_items": 3, "ref": "known_tags"},
        "notes": {"type": "str", "required": False},
    },
    "semantic": {"checks": ["total_matches"]},
}
CONTEXT = {
    "ticket_id": "T-1",
    "orders": [{"order_id": "O-1", "total": 20.0}, {"order_id": "O-2", "total": 5.0}],
    "known_tags": ["vip", "new"],
}
GOOD = {
    "ticket_id": "T-1",
    "order_id": "O-1",
    "intent": "refund",
    "question": "Where is my refund?",
    "total": 20.0,
    "count": 2,
    "urgent": False,
    "tags": ["vip"],
}


@semantic("total_matches")
def _total_matches(msg, ctx):
    totals = {o["order_id"]: o["total"] for o in ctx.get("orders", [])}
    if totals.get(msg.get("order_id")) != msg.get("total"):
        return f"total {msg.get('total')} does not match order {msg.get('order_id')}"
    return None


@pytest.fixture
def contract():
    return parse(CONTRACT)


def rules(result):
    return {(v.path, v.rule) for v in result.violations}


def test_good_message_passes(contract):
    r = check(contract, GOOD, CONTEXT)
    assert r.ok, r.violations


@pytest.mark.parametrize(
    "change, expected",
    [
        ({"order_id": None}, ("order_id", "required")),
        ({"count": "2"}, ("count", "type")),
        ({"urgent": 1}, ("urgent", "type")),
        ({"count": True}, ("count", "type")),
        ({"tags": "vip"}, ("tags", "type")),
        ({"tags": ["vip", 3]}, ("tags[1]", "type")),
        ({"intent": "cancel"}, ("intent", "enum")),
        ({"question": "hi"}, ("question", "min_length")),
        ({"question": "x" * 41}, ("question", "max_length")),
        ({"tags": []}, ("tags", "min_items")),
        ({"tags": ["vip"] * 4}, ("tags", "max_items")),
        ({"order_id": "O-999"}, ("order_id", "ref")),
        ({"ticket_id": "T-2"}, ("ticket_id", "ref")),
        ({"tags": ["vip", "made-up"]}, ("tags[1]", "ref")),
        ({"total": 5.0}, ("$", "semantic:total_matches")),
    ],
)
def test_each_check_type_fails_on_bad_message(contract, change, expected):
    """Broken case: each change below breaks exactly one rule of the contract."""
    msg = {**GOOD, **change}
    if change.get("order_id", "") is None:
        del msg["order_id"]
    r = check(contract, msg, CONTEXT)
    assert expected in rules(r), r.violations


def test_optional_field_may_be_missing_but_is_typed(contract):
    assert check(contract, GOOD, CONTEXT).ok
    r = check(contract, {**GOOD, "notes": 7}, CONTEXT)
    assert ("notes", "type") in rules(r)


def test_extra_forbid():
    c = parse({**CONTRACT, "edge": {**CONTRACT["edge"], "extra": "forbid"}})
    assert check(c, GOOD, CONTEXT).ok
    r = check(c, {**GOOD, "surprise": 1}, CONTEXT)
    assert ("surprise", "extra") in rules(r)


def test_non_dict_message(contract):
    assert ("$", "type") in rules(check(contract, ["not", "a", "dict"], CONTEXT))


def test_unregistered_and_crashing_semantic_checks():
    c = parse({**CONTRACT, "semantic": {"checks": ["nope", "boom"]}})

    @semantic("boom")
    def _boom(msg, ctx):
        raise ZeroDivisionError("bad")

    r = check(c, GOOD, CONTEXT)
    assert ("$", "semantic:nope") in rules(r)
    assert ("$", "semantic:boom") in rules(r)


@pytest.mark.parametrize(
    "bad",
    [
        {
            "edge": {"name": "x", "producer": "a", "consumer": "b"},
            "fields": {"f": {"type": "int", "min_length": 1}},
        },
        {
            "edge": {"name": "x", "producer": "a", "consumer": "b"},
            "fields": {"f": {"type": "str", "min_length": "3"}},
        },
        {
            "edge": {"name": "x", "producer": "a", "consumer": "b"},
            "fields": {"f": {"type": "str", "min_items": 1}},
        },
        {
            "edge": {"name": "x", "producer": "a", "consumer": "b"},
            "fields": {"f": {"type": "str", "required": "no"}},
        },
        {
            "edge": {"name": "x", "producer": "a", "consumer": "b"},
            "fields": {"f": {"type": "str", "enum": "abc"}},
        },
        {"edge": {"name": "x", "producer": "a"}, "fields": {"f": {"type": "str"}}},
        {"edge": {"name": "x", "producer": "a", "consumer": "b"}, "fields": {}},
        {
            "edge": {"name": "x", "producer": "a", "consumer": "b"},
            "fields": {"f": {"type": "date"}},
        },
        {
            "edge": {"name": "x", "producer": "a", "consumer": "b"},
            "fields": {"f": {"type": "str", "max_len": 3}},
        },
        {
            "edge": {"name": "x", "producer": "a", "consumer": "b", "extra": "maybe"},
            "fields": {"f": {"type": "str"}},
        },
    ],
)
def test_bad_contract_files_are_rejected(bad):
    """Broken case: a typo in a contract must not turn into a check that passes everything."""
    with pytest.raises(ContractError):
        parse(bad)


def test_decorator_stops_bad_output(contract):
    """Broken case: the agent returns an invented order id."""

    @guard(outbound=contract)
    def agent(inp):
        return {**GOOD, "order_id": inp["want"]}

    assert agent({**CONTEXT, "want": "O-1"})["order_id"] == "O-1"
    with pytest.raises(HandoffBlocked) as e:
        agent({**CONTEXT, "want": "O-777"})
    assert e.value.result.violations[0].rule == "ref"


def test_decorator_warn_mode_lets_message_through(contract, caplog):
    seen = []

    @guard(outbound=contract, mode="warn", on_violation=seen.append)
    def agent(inp):
        return {**GOOD, "intent": "cancel"}

    out = agent(CONTEXT)
    assert out["intent"] == "cancel"
    assert seen and seen[0].violations[0].rule == "enum"
    assert "broke its contract" in caplog.text


def test_decorator_checks_inbound(contract):
    @guard(inbound=contract, inbound_context=lambda inp: CONTEXT)
    def consumer(msg):
        return msg["question"]

    assert consumer(GOOD) == GOOD["question"]
    with pytest.raises(HandoffBlocked):
        consumer({**GOOD, "count": "two"})


def test_decorator_rejects_unknown_mode(contract):
    with pytest.raises(ValueError):
        guard(outbound=contract, mode="loud")


def test_items_rules_on_a_plain_list():
    """Broken case: min_items and max_items were skipped for type = "list"."""
    c = parse(
        {
            "edge": {"name": "e", "producer": "a", "consumer": "b"},
            "fields": {"f": {"type": "list", "min_items": 1, "max_items": 2}},
        }
    )
    assert check(c, {"f": [1]}).ok
    assert ("f", "min_items") in rules(check(c, {"f": []}))
    assert ("f", "max_items") in rules(check(c, {"f": [1, 2, 3]}))


@pytest.mark.parametrize(
    "returned, ok",
    [
        (None, True),
        (True, True),
        ([], True),
        (False, False),
        ("bad", False),
        (["a", "b"], False),
        (3, False),
    ],
)
def test_semantic_return_values(returned, ok):
    """Broken case: a check that returned True crashed check(), and False counted as a pass."""
    semantic("returns_value")(lambda m, c: returned)
    c = parse(
        {
            "edge": {"name": "e", "producer": "a", "consumer": "b"},
            "fields": {"f": {"type": "str"}},
            "semantic": {"checks": ["returns_value"]},
        }
    )
    assert check(c, {"f": "x"}).ok is ok

# Demo

A real terminal transcript, captured on 2026-11-21 on the build machine. No sign-in, no network, no keys.

## One ticket, then the same ticket with a stale order total

```console
$ .venv/bin/handoffpact demo
scenario seed 4, ticket T-026885: Can I get my money back for order O-162500? The backpack came damaged.

[intake_to_research] contract ok
{
  "ticket_id": "T-026885",
  "customer_id": "C-30939",
  "turn": 2,
  "intent": "refund",
  "order_id": "O-162500",
  "question": "Can I get my money back for order O-162500? The backpack came damaged."
}

[research_to_draft] contract ok
{
  "ticket_id": "T-026885",
  "turn": 2,
  "intent": "refund",
  "order_id": "O-162500",
  "order_total": 46.03,
  "days_since_order": 3,
  "policy_ids": [
    "P-01",
    "P-02"
  ],
  "excerpts": [
    "Customers can get a full refund within 30 days of the order date.",
    "If an item arrives damaged, we refund the full order total within 45 days of the order date."
  ]
}

[draft_to_review] contract ok
{
  "ticket_id": "T-026885",
  "turn": 2,
  "intent": "refund",
  "order_id": "O-162500",
  "reply": "Hi there. We will refund $46.03 for order O-162500, which is 3 days old. See policy P-01.",
  "refund_amount": 46.03,
  "cited_policy_ids": [
    "P-01"
  ]
}

[review_to_customer] contract ok
{
  "ticket_id": "T-026885",
  "turn": 2,
  "approved": true,
  "reply": "Hi there. We will refund $46.03 for order O-162500, which is 3 days old. See policy P-01.",
  "refund_amount": 46.03
}

Now research hands over a stale order_total (51.4) from the turn 1 order.
with contracts: stopped by contract at research_to_draft, blast radius 0
  violation research_to_draft: $ semantic:order_facts_match
without contracts: delivered=True, blast radius 3
  reply sent: Hi there. We will refund $51.40 for order O-162500, which is 3 days old. See policy P-01.
```

## The contract test example with a planted drift

```console
$ .venv/bin/python -m pytest examples/contract_test -p no:cacheprovider
..F                                                                      [100%]
=================================== FAILURES ===================================
____________________ test_drifted_draft_keeps_the_contract _____________________
...

src/handoffpact/pytest_plugin.py:87: DriftError
=========================== short test summary info ============================
FAILED examples/contract_test/test_drifted_draft.py::test_drifted_draft_keeps_the_contract
1 failed, 2 passed in 0.03s
```

## Check one message from the command line

```console
$ handoffpact check draft_to_review.toml msg.json --context ctx.json
draft_to_review: pass
$ handoffpact check draft_to_review.toml bad.json --context ctx.json
draft_to_review: cited_policy_ids[0]: ref ('P-77' not found at context handoff.policy_ids)
draft_to_review: $: semantic:refund_matches_total (refund 999.0 is neither 0 nor the order total 46.03)
draft_to_review: $: semantic:reply_cites_policies (reply does not cite P-77)
(exit code 1)
```

## The benchmark

```console
$ .venv/bin/handoffpact bench --faults 2100 --clean 500 --seed 2026 --out /tmp/bench.json
2100 fault runs, 500 clean runs, 1.28s
detected 1985/2100
false alarms 0/500
blast radius 0.21 with contracts, 1.99 without
```

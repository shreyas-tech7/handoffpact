# Contract `research_to_draft`

Producer: `research`. Consumer: `draft`. Source: `research_to_draft.toml`.

Research looks up the order and the policies that fit the intent, and passes the facts to the drafter.

Unknown fields: rejected.

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| `ticket_id` | `str` | yes | must exist at context `handoff.ticket_id` |
| `turn` | `int` | yes | must exist at context `turn` |
| `intent` | `str` | yes | one of `refund`, `shipping`, `warranty`, `account`, must exist at context `handoff.intent` |
| `order_id` | `str` | yes | must exist at context `handoff.order_id` |
| `order_total` | `float` | yes | none |
| `days_since_order` | `int` | yes | none |
| `policy_ids` | `list[str]` | yes | items 1 to 3, must exist at context `corpus[*].id` |
| `excerpts` | `list[str]` | yes | length 30 to 400, items 1 to 3 |

Semantic checks:

- `order_facts_match`
- `policies_fit_intent`
- `excerpts_are_sentences`
- `no_instruction_text`

[Back to the graph](README.md)

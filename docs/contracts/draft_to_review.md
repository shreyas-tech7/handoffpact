# Contract `draft_to_review`

Producer: `draft`. Consumer: `review`. Source: `draft_to_review.toml`.

The drafter writes the reply and the refund amount. The reviewer decides whether it goes out.

Unknown fields: rejected.

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| `ticket_id` | `str` | yes | must exist at context `handoff.ticket_id` |
| `turn` | `int` | yes | must exist at context `turn` |
| `intent` | `str` | yes | one of `refund`, `shipping`, `warranty`, `account`, must exist at context `handoff.intent` |
| `order_id` | `str` | yes | must exist at context `handoff.order_id` |
| `reply` | `str` | yes | length 40 to 700 |
| `refund_amount` | `float` | yes | none |
| `cited_policy_ids` | `list[str]` | yes | items 1 to 3, must exist at context `handoff.policy_ids` |

Semantic checks:

- `refund_matches_total`
- `reply_cites_policies`
- `reply_is_complete`
- `no_instruction_text`

[Back to the graph](README.md)

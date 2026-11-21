# Contract `review_to_customer`

Producer: `review`. Consumer: `customer`. Source: `review_to_customer.toml`.

The reviewer approves or escalates. An approved reply goes to the customer as written.

Unknown fields: rejected.

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| `ticket_id` | `str` | yes | must exist at context `handoff.ticket_id` |
| `turn` | `int` | yes | must exist at context `turn` |
| `approved` | `bool` | yes | none |
| `reply` | `str` | yes | length 40 to 700 |
| `refund_amount` | `float` | yes | none |

Semantic checks:

- `review_keeps_draft`
- `reply_is_complete`
- `no_instruction_text`

[Back to the graph](README.md)

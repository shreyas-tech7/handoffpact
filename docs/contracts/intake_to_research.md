# Contract `intake_to_research`

Producer: `intake`. Consumer: `research`. Source: `intake_to_research.toml`.

Intake reads the customer ticket and tells research what the customer wants and which order it is about.

Unknown fields: rejected.

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| `ticket_id` | `str` | yes | must exist at context `ticket_id` |
| `customer_id` | `str` | yes | must exist at context `customer_id` |
| `turn` | `int` | yes | must exist at context `turn` |
| `intent` | `str` | yes | one of `refund`, `shipping`, `warranty`, `account` |
| `order_id` | `str` | yes | must exist at context `orders[*].order_id` |
| `question` | `str` | yes | length 15 to 400 |

Semantic checks:

- `order_id_in_ticket`
- `question_from_ticket`
- `no_instruction_text`

[Back to the graph](README.md)

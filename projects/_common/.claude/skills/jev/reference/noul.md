# Noul

Estimates the probability that a statement is true. Best for yes/no
signals where the probability itself is useful (not just the verdict)
-- e.g. "is this urgent", "is the customer asking to escalate".

## Request

```json
{
  "type": "noul",
  "instructions": "Is the customer asking for a human agent?",
  "criteria": {
    "true": "Explicitly asks for a human/agent/representative",
    "false": "No such request"
  }
}
```

- `instructions` -- required. The yes/no question or statement (string,
  object, or array).
- `criteria` -- optional. `{ "true": "...", "false": "..." }` clarifying
  what counts as yes vs. no. Omit it if the instructions are already
  unambiguous.

## Response

```json
{
  "type": "noul",
  "noul": 0.99
}
```

- `noul` -- a single number from 0 to 1: the probability the answer is
  yes.
- **No `confidence` field.** Unlike `choice`/`score`, noul has nothing
  else to read -- code that assumes every answer has `.confidence`
  breaks on this type.

## Worked example

```json
{
  "state": "I have asked three times now. Can I please just talk to a real person?",
  "model": "~typesafe/jev-latest",
  "questions": {
    "is_human_escalation": {
      "type": "noul",
      "instructions": "Is the customer asking for a human agent?"
    }
  }
}
```

```json
{
  "answers": {
    "is_human_escalation": { "type": "noul", "noul": 0.99 }
  }
}
```

Source: https://docs.typesafe.ai/primitives/noul

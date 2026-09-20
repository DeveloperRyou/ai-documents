# Choice

Picks one option from a fixed set you define. Best for routing,
classification, or fixed tool selection -- e.g. "which skill should
handle this", "which team owns this ticket".

## Request

```json
{
  "type": "choice",
  "instructions": "Which team should handle this?",
  "criteria": {
    "returns": "Exchanges, wrong or damaged items",
    "shipping": "Delivery status, delays, lost packages",
    "billing": "Charges, invoices, payment problems"
  }
}
```

- `instructions` -- the question (string, object, or array).
- `criteria` -- a map of `option_name -> description`. Up to **255
  options**. Both keys and descriptions should be distinct enough that
  the model isn't guessing between near-duplicates.

## Response

```json
{
  "type": "choice",
  "choice": "shipping",
  "confidence": 0.95,
  "probabilities": {
    "returns": 0.02,
    "shipping": 0.95,
    "billing": 0.03
  }
}
```

- `choice` -- the option with the highest probability.
- `probabilities` -- full distribution over every option in `criteria`;
  sums to 1.0.
- `confidence` -- 0 to 1, derived from how peaked/flat the distribution
  is (a single dominant option -> high confidence; a near-even split ->
  low confidence). **Don't just read `choice` and act** -- check
  `confidence`/`probabilities` before branching on a borderline call,
  e.g. fall back to asking a human when confidence is low.

## Worked example (routing to a skill)

```json
{
  "state": "PR diff summary: adds a retry wrapper around the payment webhook handler.",
  "model": "~typesafe/jev-latest",
  "questions": {
    "route_to": {
      "type": "choice",
      "instructions": "Which skill should handle this request?",
      "criteria": {
        "backlog-issue": "Filing a new backlog issue",
        "resolve-issue": "Fixing an existing issue end-to-end",
        "code-review": "Reviewing a diff or PR for correctness"
      }
    }
  }
}
```

Source: https://docs.typesafe.ai/primitives/choice

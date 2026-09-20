# Score

Places the state on an ordered rubric. Best for severity, quality,
risk, or priority -- anything that's a *position on a spectrum* rather
than a category or a yes/no.

## Request

```json
{
  "type": "score",
  "instructions": "How severe is this bug report?",
  "criteria": [
    "Cosmetic -- no functional impact",
    "Minor -- workaround exists",
    "Major -- no workaround, blocks a feature",
    "Critical -- data loss or outage"
  ]
}
```

- `instructions` -- what to rate (string, object, or array).
- `criteria` -- an array of **2 to 10 levels**, ordered low to high. The
  level's position in the array (0-indexed) is its level number. Each
  level can be a plain string, or an object for more detail:
  ```json
  { "what": "Major -- no workaround, blocks a feature", "examples": ["checkout fails for all EU users"] }
  ```

## Response

```json
{
  "type": "score",
  "score": 2.14,
  "confidence": 0.61,
  "legend": {
    "0": "Cosmetic -- no functional impact",
    "1": "Minor -- workaround exists",
    "2": "Major -- no workaround, blocks a feature",
    "3": "Critical -- data loss or outage"
  },
  "probabilities": {
    "0": 0.0,
    "1": 0.08,
    "2": 0.7,
    "3": 0.22
  }
}
```

- `score` -- a probability-weighted position on the level number line
  (each level number x its probability, summed) -- so it's a
  continuous value, not necessarily one of the integer levels.
- `probabilities` -- probability of each level, keyed by level number
  as a string; sums to 1.
- `legend` -- each level number mapped back to its description, so you
  don't have to keep `criteria`'s order around separately.
- `confidence` -- 0 to 1, from how spread out `probabilities` is.

## Worked example

```json
{
  "state": "Login page 500s for ~5% of users on Safari; no data loss, workaround is to use Chrome.",
  "model": "~typesafe/jev-latest",
  "questions": {
    "severity": {
      "type": "score",
      "instructions": "How severe is this bug report?",
      "criteria": [
        "Cosmetic -- no functional impact",
        "Minor -- workaround exists",
        "Major -- no workaround, blocks a feature",
        "Critical -- data loss or outage"
      ]
    }
  }
}
```

Source: https://docs.typesafe.ai/primitives/score

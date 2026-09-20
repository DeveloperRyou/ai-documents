---
name: jev
description: Use when a step needs a narrow, typed decision rather than free text -- a yes/no, a pick from a fixed set of options, or a position on a rubric -- e.g. routing a task to the right skill/agent, gating an action on risk, or scoring severity. Calls TypeSafe's Jev model through OpenRouter's Decisions API and returns calibrated probabilities your code branches on. Requires OPENROUTER_API_KEY; sends `state` to a third-party API, unlike the on-device local-llm skill.
---

# Jev (typed decisions)

## Overview

TypeSafe's Jev model, called through OpenRouter's Decisions API
(`POST /alpha/decisions`), for narrow structured decisions instead of
chat. Given a `state` (a string describing the situation) and a set of
typed `questions`, it returns calibrated probabilities -- not free
text -- that your code can branch on directly:

- **noul** -- a yes/no probability (0..1).
- **choice** -- a pick from options you define, plus the full probability distribution.
- **score** -- a position on an ordered rubric you define.

`scripts/run.py` does nothing but talk to that endpoint. It knows
nothing about what the questions mean or what to do with the answers
-- same split as `local-llm/scripts/run.py`: infra in the script,
role/prompt knowledge in whatever calls it.

## When to Use

- Routing: given a request/diff/issue description, pick which
  skill/agent/team should handle it (`choice`).
- Gating: decide whether an action is risky/urgent enough to need a
  human or a fuller review before proceeding (`noul`).
- Classifying: score severity, confidence, or sentiment on a rubric
  you define (`score`), instead of parsing it out of free text.
- **Don't use for:** generating content, multi-turn conversation, or
  anything needing the full context of a codebase -- Jev only sees the
  `state` string you hand it, and only answers the questions you ask.
  Don't use for content you can't send to a third party (see Privacy
  below).

## Prerequisites

1. An OpenRouter API key with `OPENROUTER_API_KEY` set in the
   environment (never store it in `scripts/models.json`).
2. `scripts/models.json` ships with a `jev` alias pointing at
   `~typesafe/jev-latest` (always the latest model in the Jev family).

## Privacy

Unlike `local-llm` (Ollama, stays on-device), this calls an external
API. Only put in `state` what you're fine sending to OpenRouter --
short descriptions, diff summaries, issue text. Don't paste full
source files, secrets, or credentials into `state`.

## Quick Reference

```
python3 .claude/skills/jev/scripts/run.py models     # list configured aliases
python3 .claude/skills/jev/scripts/run.py call \
    --model jev \
    --state-text "<situation to decide about>" \
    --questions-file <questions>.json \
    --out <decision>.json
```

`questions.json` maps a key to a typed question. All three types can
be mixed in one call. Field names, response shape, and a worked
example for each type are in its own reference file -- read the one
you need before writing `questions.json`, since each has different
required fields and gotchas:

| Type | Purpose | Answer fields | Reference |
|---|---|---|---|
| `noul` | probability a yes/no statement is true | `noul` (0..1) -- **no `confidence`** | `reference/noul.md` |
| `choice` | pick 1 of up to 255 options | `choice`, `probabilities`, `confidence` | `reference/choice.md` |
| `score` | position on a 2-10 level ordered rubric | `score`, `legend`, `probabilities`, `confidence` | `reference/score.md` |

Minimal mixed example:

```json
{
  "is_risky": {
    "type": "noul",
    "instructions": "Does this change touch auth or payments code?"
  },
  "route_to": {
    "type": "choice",
    "instructions": "Which skill should handle this request?",
    "criteria": {
      "backlog-issue": "Filing a new issue",
      "resolve-issue": "Fixing an existing issue end-to-end"
    }
  }
}
```

## Implementation

Call `scripts/run.py` directly (via Bash) with a `state` and a
`questions.json` describing what you need decided, then branch on the
returned probabilities in your own logic. There's no dedicated
subagent yet -- unlike `local-coder`/`local-code-reviewer`, no single
fixed question set has emerged as a repeated pattern. If one does
(e.g. a severity-scoring step reused across the review pipeline),
wrap it in a thin-router subagent the same way `local-llm` wraps
Ollama, so the coordinator doesn't need to know the question shape
each time.

## Common Mistakes

- **Treating `choice`/`score` as certain.** These are probabilities,
  not verdicts -- check `probabilities`/thresholds before acting on a
  borderline call instead of trusting the top pick blindly.
- **Reading `.confidence` off a `noul` answer.** Only `choice` and
  `score` carry `confidence`; `noul` answers are just `{ type, noul }`
  -- code that assumes every answer has `.confidence` breaks on it.
- **Sending sensitive `state`.** This is a third-party API call, not a
  local one -- see Privacy above.
- **Forgetting `OPENROUTER_API_KEY`.** `run.py` exits immediately with
  an error naming the missing variable if it's not set.
- **Malformed `questions.json`.** `run.py` validates it's parseable
  JSON before calling out; a schema mismatch against what the
  Decisions API expects still surfaces as an HTTP error from
  OpenRouter, printed with the response body.

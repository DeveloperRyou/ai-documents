---
name: local-llm
description: Use when cheap on-device model work can keep bulky material out of the main context -- a multi-role first-pass review of a diff/file, a vision pre-check of screenshots, a short classification -- or to draft a new file from scratch. Called directly via Bash (`run.py`), never through a wrapper subagent. Requires Ollama running locally with the configured model pulled.
---

# Local LLM

## Overview

`scripts/run.py` talks to a local Ollama model (`/api/chat`). Call it
**directly with Bash** -- a subagent that exists only to run this script
costs a full Claude context per dispatch plus a notification turn to
collect it, which in practice cost more than the local model saved.

It saves tokens only when it keeps something **out of** the main
context or replaces whole Claude turns:

| Use | Command | What the coordinator reads |
|---|---|---|
| Multi-role review | `run.py review` | one summary line + blocker lines |
| Screenshot pre-check | `run.py call --model vision --images ...` | a short text verdict, not the image |
| Classification (hooks) | `classifier` alias | nothing -- runs outside the conversation |
| New-file scaffold | `run.py call --model coder --out <file>` | nothing until it reads the file |

## When NOT to use

- **Edits to an existing file.** Describing the change to the local
  model costs about as many output tokens as making it with Edit, and
  you still have to read and verify the result. Edit directly.
- **Mechanical renames/replacements** (e.g. `sm:` -> `lg:` across
  files): `sed`/a codemod is exact and instant; a 9B model rewriting
  whole files is neither.
- **Anything final.** Output is a first pass from a small model with no
  repo-wide context -- always verified by you, a build, or the user.

## Prerequisites

1. [Ollama](https://ollama.com) running (`ollama list` to check).
2. The model in `scripts/models.json` pulled (`ollama pull qwen3.5:9b`).
   Aliases: `coder`, `reviewer`, `vision` (must be vision-capable --
   `ollama show <tag>` lists capabilities), `classifier`. Edit the `tag`
   fields to use a different local model.

## Quick Reference

```
S=.claude/skills/local-llm

# Multi-role review: spec/correctness/simplicity in parallel, merged.
# Exit 0 = no blockers, 1 = blockers (printed one per line).
git diff > /tmp/fix.diff
python3 $S/scripts/run.py review --files /tmp/fix.diff \
  --role spec="Only check these acceptance criteria: <verbatim>" \
  --role correctness --role simplicity \
  --context "<issue summary; anything you already verified by build/browser>" \
  --out-dir <scratchpad>/review_r1

# Vision pre-check -- the image goes to the local model, not to you.
python3 $S/scripts/run.py call --model vision --images shot.png \
  --user-text "<what to look for>"

# Draft a NEW file.
python3 $S/scripts/run.py call --model coder --system-file $S/prompts/coder.txt \
  --user-files <sibling file to match style> --extra "[Task]
<what to build>" --out <new file>

python3 $S/scripts/run.py models
```

Prompts live in `prompts/` (`reviewer.txt`, `coder.txt`); `run.py` itself
is role-agnostic apart from `review`'s default focus texts.

## Common Mistakes

- **Wrapping it in an Agent/subagent.** Run the Bash command yourself;
  keep it in the foreground so there's no "still waiting" turn.
- **Treating reviewer blockers as ground truth.** It reads a diff, it
  can't run anything. Pass what you've already verified via `--context`,
  and if a blocker contradicts hard evidence you hold, re-verify once and
  document the override instead of looping on it.
- **Dumping too much context.** `--files`/`--user-files` are
  concatenated as-is; pass only what's relevant or you'll exceed
  `num_ctx` in `models.json`.

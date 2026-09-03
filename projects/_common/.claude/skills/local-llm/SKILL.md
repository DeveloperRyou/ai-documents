---
name: local-llm
description: Use when a coding task is cheap enough for a local model -- drafting boilerplate/scaffolding, or a first-pass review of a diff/file for bugs, security issues, and style -- and doesn't need the coordinator's full-price model. Requires Ollama running locally with a coding model pulled.
---

# Local LLM (coding)

## Overview

A local Ollama model, called through a thin-router subagent, doing cheap first-pass work so the coordinator's tokens go to what actually needs them. Two subagents wrap this:

- **local-coder** -- drafts a file (scaffolding, a repetitive implementation, a rough first pass) for a human/cloud pass to refine later.
- **local-code-reviewer** -- reviews a diff/file for bugs, security issues, and style, and produces a JSON issue report.

Both are thin routers: they call `scripts/run.py`, which does nothing but talk to Ollama's `/api/chat`. All prompt/role knowledge lives in each agent's own `.prompt.txt` file under `.claude/agents/`, not in `run.py` -- `run.py` doesn't know or care what it's being used for.

## When to Use

- Drafting boilerplate, scaffolding, or a mechanical/repetitive implementation you'll refine afterward -- dispatch `local-coder` instead of writing it yourself.
- A first-pass review of a diff or file before a human review or `/code-review` -- dispatch `local-code-reviewer` to catch the obvious stuff cheaply first.
- **Don't use for:** anything where correctness matters and there's no follow-up review step, anything needing deep repo-wide context (the local model only sees whatever files you hand it), or as a substitute for a final/authoritative review -- `local-code-reviewer`'s output is a first pass, not `/code-review`.

## Prerequisites

1. [Ollama](https://ollama.com) installed and running (`ollama serve`, or as a system service -- check with `ollama list`).
2. A coding model pulled:
   ```
   ollama pull qwen3.5:9b
   ```
   `scripts/models.json` ships with `coder`/`reviewer` aliases pointing at `qwen3.5:9b`. If you already have a different model pulled locally, edit the `tag` fields there instead of pulling a new one -- any general-purpose model works, just less well-suited to code than a dedicated coder model.

## Quick Reference

| Alias | Used by | Purpose |
|---|---|---|
| `coder` | local-coder | draft an implementation, higher temperature |
| `reviewer` | local-code-reviewer | JSON issue report, low temperature |

```
python3 .claude/skills/local-llm/scripts/run.py models        # list configured aliases
python3 .claude/skills/local-llm/scripts/run.py call --model coder --system-file <prompt> --user-files <ctx...> --out <file>
python3 .claude/skills/local-llm/scripts/run.py call --model reviewer --system-file <prompt> --user-files <file> --json --out <report>.json
```

## Implementation

Dispatch via the `Agent` tool with `subagent_type: "local-coder"` or `"local-code-reviewer"` -- both live under `.claude/agents/` and are auto-discovered. Give each a self-contained prompt: what to build/review, and which context files to hand it (a subagent starts with no memory of your conversation). See each agent's `.md` for the exact command it runs and what to pass it.

To call the local model directly, without going through an agent, see `python3 .claude/skills/local-llm/scripts/run.py --help`.

## Common Mistakes

- **Treating local-model output as final.** It's a smaller model with no repo-wide context -- always route its output through a real review step before it ships.
- **Dumping too much context.** `--user-files` gets concatenated as-is into the prompt; pass only what's actually relevant, or you'll blow past the model's context window (`num_ctx` in `models.json`) for no benefit.
- **Forgetting Ollama isn't running.** `run.py` fails with a connection error naming the host it tried -- check `ollama serve` / `ollama list` first if a call hangs or errors immediately.

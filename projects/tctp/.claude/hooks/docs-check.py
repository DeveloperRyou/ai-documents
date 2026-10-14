#!/usr/bin/env python3
"""PreToolUse(Bash) hook: make the agent decide whether docs need updating
before every `git push`.

tctp's rule (AGENTS.md) is to keep docs/, AGENTS.md and README.md in step
with the code. A plain reminder is easy to skim past, so this blocks a
push once and asks for it to be re-run with a `DOCS_CHECKED=1` prefix --
the prefix is the agent's explicit "I checked" and lets the push through.
Stdlib-only, like the rest of ai-documents' scripts.
"""
import json
import re
import sys

MARKER = "DOCS_CHECKED=1"

data = json.load(sys.stdin)
cmd = data.get("tool_input", {}).get("command", "")
if not re.search(r"\bgit\b[^;&|]*\bpush\b", cmd) or MARKER in cmd:
    sys.exit(0)

json.dump({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": (
            "push 전에 이번에 올라갈 커밋들(git log @{u}..)을 보고 docs/, AGENTS.md, README.md "
            "최신화가 필요한지 판단할 것. 필요하면 먼저 고쳐 커밋하고(docs/·AGENTS.md 는 "
            "ai-documents 레포), 판단이 끝나면 `" + MARKER + " git push ...` 로 다시 실행."
        ),
    }
}, sys.stdout, ensure_ascii=False)

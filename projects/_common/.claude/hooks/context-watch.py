#!/usr/bin/env python3
"""UserPromptSubmit hook: nudge the agent to hand off / compact before a
session's context grows into the hundreds of thousands of tokens.

Why: nearly all of a long session's cost is re-reading its own history
on every turn (cache reads), not the agent's output -- one 47-prompt
session in the portfolio repo reached 700k tokens of context and
accounted for ~half of all usage on its own. The agent can't see its own
context size and can't run /clear itself, so this hook measures it and
injects a reminder (as additionalContext) telling it to suggest one.

Two triggers, each fires at most once per band so it doesn't nag:
  1. size   -- last turn's context >= WARN_TOKENS, then again every
               STEP_TOKENS after that.
  2. topic  -- context >= TOPIC_MIN_TOKENS and a local Ollama model
               (local-llm's `classifier` alias) judges the new prompt to
               be unrelated to the recent ones. On-device, so prompts
               never leave the machine; any failure (Ollama down,
               timeout, bad output) is silently ignored.

Env overrides: CONTEXT_WATCH_WARN_TOKENS, CONTEXT_WATCH_STEP_TOKENS,
CONTEXT_WATCH_TOPIC_MIN_TOKENS, CONTEXT_WATCH_TOPIC=0 (disable trigger 2).
Stdlib-only, like the rest of ai-documents' scripts.
"""
import json
import os
import pathlib
import sys
import tempfile
import urllib.request

WARN_TOKENS = int(os.environ.get("CONTEXT_WATCH_WARN_TOKENS", 200_000))
STEP_TOKENS = int(os.environ.get("CONTEXT_WATCH_STEP_TOKENS", 100_000))
TOPIC_MIN_TOKENS = int(os.environ.get("CONTEXT_WATCH_TOPIC_MIN_TOKENS", 60_000))
TOPIC_ENABLED = os.environ.get("CONTEXT_WATCH_TOPIC", "1") != "0"
TOPIC_TIMEOUT = 6
TAIL_BYTES = 4_000_000

MODELS_JSON = pathlib.Path(__file__).resolve().parent.parent / "skills" / "local-llm" / "scripts" / "models.json"
STATE_DIR = pathlib.Path(tempfile.gettempdir()) / "claude-context-watch"


def read_tail(path):
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        f.seek(max(0, f.tell() - TAIL_BYTES))
        return f.read().decode("utf-8", errors="ignore").splitlines()


def scan_transcript(path):
    """Return (context tokens of the last main-thread turn, recent user prompts)."""
    ctx, prompts = 0, []
    for line in read_tail(path):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("isSidechain"):
            continue
        msg = d.get("message") or {}
        if d.get("type") == "assistant":
            u = msg.get("usage") or {}
            total = (u.get("input_tokens") or 0) + (u.get("cache_read_input_tokens") or 0) \
                + (u.get("cache_creation_input_tokens") or 0)
            if total:
                ctx = total
        elif d.get("type") == "user" and isinstance(msg.get("content"), str):
            text = msg["content"].strip()
            if text and not text.startswith("<"):
                prompts.append(text[:300])
    return ctx, prompts[-6:]


def is_unrelated(prompt, recent):
    cfg = json.loads(MODELS_JSON.read_text(encoding="utf-8"))
    model = cfg["models"]["classifier"]
    # Naming both topics before labelling matters: asked for a bare label,
    # the 9B model answered SAME for almost everything.
    system = (
        "A developer is chatting with a coding agent. Compare the topic of their RECENT messages with their NEW "
        "message. First name the recent topic and the new topic in a few words each, then label: SAME if NEW "
        "continues the same feature/page/component/issue/PR (follow-ups, fixes, tweaks, checks, merging it), "
        "SWITCH if NEW is about a different page, feature, component, issue, or subsystem. Output ONLY JSON: "
        "{\"recent_topic\": \"...\", \"new_topic\": \"...\", \"label\": \"SAME\"|\"SWITCH\"}."
    )
    user = "RECENT:\n" + "\n".join(f"- {p}" for p in recent) + f"\n\nNEW:\n- {prompt[:500]}"
    payload = {
        "model": model["tag"], "stream": False, "think": False, "format": "json",
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "options": {"num_ctx": model.get("num_ctx", 4096), "temperature": 0},
    }
    req = urllib.request.Request(f"{cfg.get('ollama_host', 'http://localhost:11434')}/api/chat",
                                 data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=TOPIC_TIMEOUT) as resp:
        content = json.loads(resp.read())["message"]["content"]
    return json.loads(content).get("label") == "SWITCH"


def main():
    try:
        data = json.load(sys.stdin)
        ctx, recent = scan_transcript(data["transcript_path"])
    except Exception:
        return
    prompt = (data.get("prompt") or "").strip()
    state_file = STATE_DIR / f"{data.get('session_id', 'unknown')}.json"
    try:
        state = json.loads(state_file.read_text())
    except (OSError, ValueError):
        state = {}

    reason = None
    if ctx >= WARN_TOKENS and ctx - state.get("size_warned_at", 0) >= STEP_TOKENS:
        reason = f"this session's context is ~{ctx // 1000}k tokens"
        state["size_warned_at"] = ctx
    elif (TOPIC_ENABLED and ctx >= TOPIC_MIN_TOKENS and len(prompt) >= 15 and not prompt.startswith("/")
          and recent and ctx - state.get("topic_warned_at", 0) >= STEP_TOKENS // 2):
        try:
            if is_unrelated(prompt, recent):
                reason = f"the new request looks unrelated to this session's earlier work (context ~{ctx // 1000}k tokens)"
                state["topic_warned_at"] = ctx
        except Exception:
            pass

    if not reason:
        return
    try:
        STATE_DIR.mkdir(exist_ok=True)
        state_file.write_text(json.dumps(state))
    except OSError:
        pass
    note = (
        f"[context-watch] {reason}. Every turn re-reads the whole history, so cost now scales with it. "
        "Handle the user's request, but at the start of your reply briefly suggest writing a handoff note "
        "(the `handoff` skill) and continuing in a fresh session (/clear) -- or /compact if the current task "
        "is still mid-flight. One short line; don't repeat it if the user declines."
    )
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": note}}))


if __name__ == "__main__":
    main()

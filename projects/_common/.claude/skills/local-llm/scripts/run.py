#!/usr/bin/env python3
"""General-purpose CLI for calling a local Ollama model. Stdlib-only, on
purpose -- no venv/pip install needed in any repo this gets symlinked
into (see ai-documents' own scripts/lib.py for the same philosophy).

This script knows nothing about roles or prompts -- it just posts
{system, user} to Ollama's /api/chat for whatever model alias
scripts/models.json maps to. Which alias to use, and what the system
prompt says, is entirely up to the caller (see the agents under
.claude/agents/local-coder.md and .claude/agents/local-code-reviewer.md).

Examples:
  run.py call --model coder \
      --system-file .claude/agents/local-coder.prompt.txt \
      --user-files src/similar_module.py \
      --extra "[Task]\nImplement a rate limiter matching the style above." \
      --out src/rate_limiter.py

  run.py call --model reviewer \
      --system-file .claude/agents/local-code-reviewer.prompt.txt \
      --user-files src/rate_limiter.py \
      --json \
      --out /tmp/rate_limiter_review.json

  run.py models
"""
import argparse
import json
import pathlib
import sys
import urllib.error
import urllib.request

BASE_DIR = pathlib.Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "models.json"


def load_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def read_files(paths):
    chunks = []
    for p in paths or []:
        path = pathlib.Path(p)
        if not path.exists():
            print(f"warning: file not found, skipping: {p}", file=sys.stderr)
            continue
        chunks.append(f"### {path.name}\n{path.read_text(encoding='utf-8')}")
    return "\n\n".join(chunks)


def extract_json(text):
    """Pull the JSON object out even if the model wrapped it in a code
    fence or added chatter before/after it."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found in response:\n" + text[:500])
    return text[start : end + 1]


def write_out(out_path, content):
    if out_path:
        out = pathlib.Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        print(f"saved: {out_path}", file=sys.stderr)
    else:
        print(content)


def post_chat(host, payload, timeout):
    req = urllib.request.Request(
        f"{host}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(
            f"error: could not reach Ollama at {host} ({e}). "
            f"Is `ollama serve` running / is the model pulled?",
            file=sys.stderr,
        )
        sys.exit(1)
    return body["message"]["content"]


def cmd_call(args, config):
    model_cfg = config["models"].get(args.model)
    if model_cfg is None:
        print(
            f"unknown model alias {args.model!r}; run `run.py models` to list configured aliases",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.system_file:
        system_prompt = pathlib.Path(args.system_file).read_text(encoding="utf-8")
    else:
        system_prompt = args.system_text or ""

    if args.user_files:
        user_content = read_files(args.user_files)
    else:
        user_content = args.user_text or ""

    if args.extra:
        user_content += f"\n\n{args.extra}"

    payload = {
        "model": model_cfg["tag"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "stream": False,
        "think": args.think if args.think is not None else model_cfg.get("think", False),
        "options": {
            "num_ctx": args.num_ctx or model_cfg.get("num_ctx", 8192),
            "temperature": args.temperature if args.temperature is not None else model_cfg.get("temperature", 0.3),
        },
    }
    host = config.get("ollama_host", "http://localhost:11434")
    timeout = config.get("request_timeout", 300)

    content = post_chat(host, payload, timeout)

    if args.json:
        try:
            parsed = json.loads(extract_json(content))
        except ValueError as e:
            print(f"warning: JSON parse failed, retrying once.\n{e}", file=sys.stderr)
            content = post_chat(host, payload, timeout)
            try:
                parsed = json.loads(extract_json(content))
            except ValueError as e2:
                print(f"warning: retry also failed to parse; saving raw output instead.\n{e2}", file=sys.stderr)
                write_out(args.out, content)
                return
        write_out(args.out, json.dumps(parsed, ensure_ascii=False, indent=2))
    else:
        write_out(args.out, content)


def cmd_models(args, config):
    for alias, cfg in config["models"].items():
        print(
            f"{alias}: {cfg['tag']}  (think={cfg.get('think', False)}, "
            f"num_ctx={cfg.get('num_ctx', 8192)}, temperature={cfg.get('temperature', 0.3)})"
        )


def main():
    parser = argparse.ArgumentParser(description="Stdlib-only CLI for calling local Ollama models")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("call", help="call a model once")
    p.add_argument("--model", required=True, help="alias registered in models.json (e.g. coder, reviewer)")
    p.add_argument("--system-file", help="path to a system-prompt file")
    p.add_argument("--system-text", help="system prompt given inline instead of a file")
    p.add_argument("--user-files", nargs="*", default=[], help="files to concatenate as user content")
    p.add_argument("--user-text", help="user content given inline instead of files")
    p.add_argument("--extra", help="text appended after user-files/user-text (e.g. an explicit task line)")
    p.add_argument("--think", type=lambda s: s.lower() == "true", default=None,
                    help="true/false; defaults to the model's setting in models.json")
    p.add_argument("--num-ctx", type=int, default=None)
    p.add_argument("--temperature", type=float, default=None)
    p.add_argument("--json", action="store_true", help="extract and pretty-print a JSON object from the response")
    p.add_argument("--out", help="path to save the result; prints to stdout if omitted")
    p.set_defaults(func=cmd_call)

    p = sub.add_parser("models", help="list model aliases configured in models.json")
    p.set_defaults(func=cmd_models)

    args = parser.parse_args()
    config = load_config()
    args.func(args, config)


if __name__ == "__main__":
    main()

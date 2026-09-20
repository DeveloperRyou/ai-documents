#!/usr/bin/env python3
"""General-purpose CLI for calling TypeSafe's Jev decision model via
OpenRouter's Decisions API. Stdlib-only, on purpose -- no venv/pip
install needed in any repo this gets symlinked into (see ai-documents'
own scripts/lib.py, and local-llm/scripts/run.py, for the same
philosophy).

This script knows nothing about what the questions mean -- it just
posts {model, state, questions} to OpenRouter's /alpha/decisions
endpoint and returns whatever `answers` comes back, unparsed. Which
questions to ask, and what to do with the calibrated probabilities, is
entirely up to the caller.

Requires OPENROUTER_API_KEY, either already exported or in a
.env file next to this script (see .env.example) -- never committed,
loaded fresh on every call.

Examples:
  run.py call --model jev \
      --state-text "Help! My payouts have been failing for 3 days." \
      --questions-file questions.json \
      --out /tmp/decision.json

  run.py models
"""
import argparse
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

BASE_DIR = pathlib.Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "models.json"
DOTENV_PATH = BASE_DIR / ".env"


def load_dotenv(path):
    """Minimal KEY=VALUE loader -- stdlib only, no python-dotenv
    dependency. Doesn't override a variable already set in the real
    environment, so an exported OPENROUTER_API_KEY still wins."""
    if not path.exists():
        return
    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            print(f"warning: {path}:{lineno}: not KEY=VALUE, skipping", file=sys.stderr)
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def load_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def read_text_or_file(text_arg, file_arg, label):
    if file_arg:
        return pathlib.Path(file_arg).read_text(encoding="utf-8")
    if text_arg is not None:
        return text_arg
    print(f"error: one of --{label}-text/--{label}-file is required", file=sys.stderr)
    sys.exit(1)


def write_out(out_path, content):
    if out_path:
        out = pathlib.Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        print(f"saved: {out_path}", file=sys.stderr)
    else:
        print(content)


def post_decision(host, api_key, payload, timeout, referer=None, title=None):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if referer:
        headers["HTTP-Referer"] = referer
    if title:
        headers["X-Title"] = title
    req = urllib.request.Request(
        f"{host}/alpha/decisions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        print(f"error: OpenRouter returned {e.code}: {detail}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"error: could not reach OpenRouter at {host} ({e}).", file=sys.stderr)
        sys.exit(1)


def cmd_call(args, config):
    model_cfg = config["models"].get(args.model)
    if model_cfg is None:
        print(
            f"unknown model alias {args.model!r}; run `run.py models` to list configured aliases",
            file=sys.stderr,
        )
        sys.exit(1)

    load_dotenv(DOTENV_PATH)
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print(
            f"error: OPENROUTER_API_KEY is not set (export it, or put it in {DOTENV_PATH})",
            file=sys.stderr,
        )
        sys.exit(1)

    state = read_text_or_file(args.state_text, args.state_file, "state")
    questions_raw = read_text_or_file(args.questions_text, args.questions_file, "questions")
    try:
        questions = json.loads(questions_raw)
    except json.JSONDecodeError as e:
        print(f"error: --questions-file/--questions-text must be valid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    payload = {
        "model": model_cfg["model"],
        "state": state,
        "questions": questions,
    }
    host = config.get("openrouter_host", "https://openrouter.ai/api")
    timeout = config.get("request_timeout", 60)

    body = post_decision(host, api_key, payload, timeout, args.referer, args.title)
    write_out(args.out, json.dumps(body, ensure_ascii=False, indent=2))


def cmd_models(args, config):
    for alias, cfg in config["models"].items():
        print(f"{alias}: {cfg['model']}")


def main():
    parser = argparse.ArgumentParser(
        description="Stdlib-only CLI for calling Jev via OpenRouter's Decisions API"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("call", help="ask a typed decision once")
    p.add_argument("--model", default="jev", help="alias registered in models.json (default: jev)")
    p.add_argument("--state-text", help="state given inline")
    p.add_argument("--state-file", help="path to a file holding the state")
    p.add_argument("--questions-text", help="questions object, given inline as JSON")
    p.add_argument("--questions-file", help="path to a JSON file describing the questions")
    p.add_argument("--referer", help="optional HTTP-Referer header, for OpenRouter's leaderboards")
    p.add_argument("--title", help="optional X-Title header, for OpenRouter's leaderboards")
    p.add_argument("--out", help="path to save the result; prints to stdout if omitted")
    p.set_defaults(func=cmd_call)

    p = sub.add_parser("models", help="list model aliases configured in models.json")
    p.set_defaults(func=cmd_models)

    args = parser.parse_args()
    config = load_config()
    args.func(args, config)


if __name__ == "__main__":
    main()

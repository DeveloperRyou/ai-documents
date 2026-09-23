#!/usr/bin/env python3
"""General-purpose CLI for calling a local Ollama model. Stdlib-only, on
purpose -- no venv/pip install needed in any repo this gets symlinked
into (see ai-documents' own scripts/lib.py for the same philosophy).

`call` knows nothing about roles or prompts -- it just posts
{system, user[, images]} to Ollama's /api/chat for whatever model alias
scripts/models.json maps to. `review` is the one opinionated wrapper: it
runs the reviewer prompt (../prompts/reviewer.txt) once per focus role,
in parallel, and merges the reports -- so the coordinator makes one Bash
call and reads one summary line instead of dispatching a subagent per
role.

Examples:
  run.py call --model coder \
      --system-file .claude/skills/local-llm/prompts/coder.txt \
      --user-files src/similar_module.py \
      --extra "[Task]\nImplement a rate limiter matching the style above." \
      --out src/rate_limiter.py

  run.py call --model vision --images shot.png \
      --user-text "Does anything overlap or overflow?"

  run.py review --files /tmp/fix.diff \
      --role spec="Only check these acceptance criteria: ..." \
      --role correctness \
      --role simplicity \
      --out-dir /tmp/review_round1

  run.py models
"""
import argparse
import base64
import concurrent.futures
import json
import pathlib
import sys
import urllib.error
import urllib.request

BASE_DIR = pathlib.Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "models.json"
REVIEWER_PROMPT = BASE_DIR.parent / "prompts" / "reviewer.txt"

# Default [Focus] text per review role; `--role name="custom text"` overrides.
ROLE_FOCUS = {
    "spec": "Only check whether this change actually satisfies the task/acceptance criteria, nothing else.",
    "correctness": "Only bugs, edge cases, and security issues.",
    "simplicity": "Only unnecessary complexity, duplication, and style/convention mismatches with the rest of the file.",
}
SEVERITIES = ("blocker", "concern", "nit")


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


def build_payload(model_cfg, system_prompt, user_content, images=None, think=None,
                  num_ctx=None, temperature=None):
    user_msg = {"role": "user", "content": user_content}
    if images:
        user_msg["images"] = [base64.b64encode(pathlib.Path(i).read_bytes()).decode() for i in images]
    return {
        "model": model_cfg["tag"],
        "messages": [{"role": "system", "content": system_prompt}, user_msg],
        "stream": False,
        "think": think if think is not None else model_cfg.get("think", False),
        "options": {
            "num_ctx": num_ctx or model_cfg.get("num_ctx", 8192),
            "temperature": temperature if temperature is not None else model_cfg.get("temperature", 0.3),
        },
    }


def chat_json(host, payload, timeout):
    """post_chat + JSON extraction with one retry; returns (parsed or None, raw)."""
    content = post_chat(host, payload, timeout)
    for attempt in range(2):
        try:
            return json.loads(extract_json(content)), content
        except ValueError as e:
            if attempt == 0:
                print(f"warning: JSON parse failed, retrying once.\n{e}", file=sys.stderr)
                content = post_chat(host, payload, timeout)
    return None, content


def get_model(config, alias):
    model_cfg = config["models"].get(alias)
    if model_cfg is None:
        print(
            f"unknown model alias {alias!r}; run `run.py models` to list configured aliases",
            file=sys.stderr,
        )
        sys.exit(1)
    return model_cfg


def cmd_call(args, config):
    model_cfg = get_model(config, args.model)

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

    payload = build_payload(model_cfg, system_prompt, user_content, args.images,
                            args.think, args.num_ctx, args.temperature)
    host = config.get("ollama_host", "http://localhost:11434")
    timeout = config.get("request_timeout", 300)

    if args.json:
        parsed, raw = chat_json(host, payload, timeout)
        if parsed is None:
            print("warning: retry also failed to parse; saving raw output instead.", file=sys.stderr)
            write_out(args.out, raw)
        else:
            write_out(args.out, json.dumps(parsed, ensure_ascii=False, indent=2))
    else:
        write_out(args.out, post_chat(host, payload, timeout))


def parse_role(spec):
    name, _, focus = spec.partition("=")
    if not focus:
        if name not in ROLE_FOCUS:
            print(f"error: role {name!r} has no default focus; pass --role {name}=\"<focus text>\"", file=sys.stderr)
            sys.exit(2)
        focus = ROLE_FOCUS[name]
    return name, focus


def cmd_review(args, config):
    """Run the reviewer once per role in parallel, merge by severity, and
    exit 1 if any blocker remains (0 otherwise) -- the fix loop in the
    resolve-issue skill gates on this exit code."""
    model_cfg = get_model(config, "reviewer")
    host = config.get("ollama_host", "http://localhost:11434")
    timeout = config.get("request_timeout", 300)
    system_prompt = REVIEWER_PROMPT.read_text(encoding="utf-8")
    user_content = read_files(args.files)
    if args.context:
        user_content += f"\n\n[Context]\n{args.context}"
    roles = [parse_role(r) for r in (args.role or list(ROLE_FOCUS))]
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def run_role(role):
        name, focus = role
        payload = build_payload(model_cfg, system_prompt, f"{user_content}\n\n[Focus]\n{focus}")
        parsed, raw = chat_json(host, payload, timeout)
        if parsed is None:
            (out_dir / f"{name}.raw.txt").write_text(raw, encoding="utf-8")
            parsed = {"issues": [{"type": "spec", "location": "-", "severity": "concern",
                                  "problem": f"{name} reviewer returned unparseable output (see {name}.raw.txt)"}]}
        (out_dir / f"{name}.json").write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
        return name, parsed

    # Ollama serializes requests per model unless OLLAMA_NUM_PARALLEL > 1;
    # parallel threads still help there and cost nothing otherwise.
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(roles)) as pool:
        results = list(pool.map(run_role, roles))

    issues, summaries = [], {}
    for name, report in results:
        for issue in report.get("issues", []):
            issue["role"] = name
            if issue.get("severity") not in SEVERITIES:
                issue["severity"] = "concern"  # unknown/malformed severity -> don't silently drop it
            issues.append(issue)
        if report.get("summary"):
            summaries[name] = report["summary"]
    bucketed = {sev: [i for i in issues if i["severity"] == sev] for sev in SEVERITIES}
    counts = {sev: len(bucketed[sev]) for sev in SEVERITIES}
    merged_path = out_dir / "merged.json"
    merged_path.write_text(json.dumps({"counts": counts, "issues": bucketed, "role_summaries": summaries},
                                      ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"{counts['blocker']} blocker(s), {counts['concern']} concern(s), {counts['nit']} nit(s) -- {merged_path}")
    for b in bucketed["blocker"]:
        print(f"  [blocker/{b['role']}] {b.get('location', '-')}: {b.get('problem', '')}")
    sys.exit(1 if counts["blocker"] else 0)


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
    p.add_argument("--images", nargs="*", default=[], help="image files to attach (vision-capable models only)")
    p.add_argument("--think", type=lambda s: s.lower() == "true", default=None,
                    help="true/false; defaults to the model's setting in models.json")
    p.add_argument("--num-ctx", type=int, default=None)
    p.add_argument("--temperature", type=float, default=None)
    p.add_argument("--json", action="store_true", help="extract and pretty-print a JSON object from the response")
    p.add_argument("--out", help="path to save the result; prints to stdout if omitted")
    p.set_defaults(func=cmd_call)

    p = sub.add_parser("review", help="multi-role parallel review of files/diffs; exit 1 if any blocker")
    p.add_argument("--files", nargs="+", required=True, help="files or saved diffs to review")
    p.add_argument("--role", action="append",
                   help="role or role=\"focus text\" (repeatable); defaults to spec, correctness, simplicity")
    p.add_argument("--context", help="extra context appended once, e.g. the issue text or what was already verified")
    p.add_argument("--out-dir", required=True, help="directory for <role>.json and merged.json")
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("models", help="list model aliases configured in models.json")
    p.set_defaults(func=cmd_models)

    args = parser.parse_args()
    config = load_config()
    args.func(args, config)


if __name__ == "__main__":
    main()

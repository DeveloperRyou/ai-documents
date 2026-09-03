#!/usr/bin/env python3
"""Merge N local-code-reviewer JSON reports (one per review role) from a
multi-role review round into one bucketed-by-severity report, and give
an unambiguous pass/fail signal for the fix loop.

Stdlib-only, same reasoning as run.py: no venv needed wherever this
skill's directory gets symlinked to.

Usage:
  aggregate_review.py <role>=<report.json> [<role>=<report.json> ...] --out <merged.json>

Exit code 0 if there are zero "blocker" issues across all reports, 1
otherwise -- the resolve-issue skill's fix loop keys off this, not off
re-reading and re-counting the JSON by eye each round.
"""
import argparse
import json
import pathlib
import sys

SEVERITIES = ("blocker", "concern", "nit")


def load_report(role, path):
    p = pathlib.Path(path)
    if not p.exists():
        print(f"warning: report not found for role {role!r}, skipping: {path}", file=sys.stderr)
        return [], None
    data = json.loads(p.read_text(encoding="utf-8"))
    issues = data.get("issues", [])
    for issue in issues:
        issue["role"] = role
        if issue.get("severity") not in SEVERITIES:
            issue["severity"] = "concern"  # unknown/malformed severity -> don't silently drop it
    return issues, data.get("summary")


def main():
    parser = argparse.ArgumentParser(description="Merge multi-role review reports and gate on blockers")
    parser.add_argument("reports", nargs="+", help="role=path pairs, e.g. spec=/tmp/spec.json")
    parser.add_argument("--out", required=True, help="where to write the merged report")
    args = parser.parse_args()

    all_issues = []
    summaries = {}
    for entry in args.reports:
        if "=" not in entry:
            print(f"error: expected role=path, got {entry!r}", file=sys.stderr)
            sys.exit(2)
        role, path = entry.split("=", 1)
        issues, summary = load_report(role, path)
        all_issues.extend(issues)
        if summary:
            summaries[role] = summary

    bucketed = {sev: [i for i in all_issues if i["severity"] == sev] for sev in SEVERITIES}
    merged = {
        "counts": {sev: len(bucketed[sev]) for sev in SEVERITIES},
        "issues": bucketed,
        "role_summaries": summaries,
    }

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")

    counts = merged["counts"]
    print(
        f"{counts['blocker']} blocker(s), {counts['concern']} concern(s), {counts['nit']} nit(s) "
        f"-- merged report: {args.out}"
    )
    sys.exit(1 if counts["blocker"] > 0 else 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove symlinks this tool created (backups are left in place).")
    parser.add_argument("--config", default=None, help="path to repo.yaml (default: repo root)")
    parser.add_argument("--only", default=None, help="only unlink the repo with this name")
    parser.add_argument("--dry-run", action="store_true", help="print what would happen, change nothing")
    args = parser.parse_args()

    root = lib.repo_root()
    config_path = Path(args.config) if args.config else root / "repo.yaml"

    try:
        config = lib.parse_config(config_path)
    except lib.ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    anchor = Path(config["anchor"]).expanduser()
    repos = config["repos"]
    if args.only:
        repos = [r for r in repos if r["name"] == args.only]
        if not repos:
            print(f"error: no repo named {args.only!r} in repo.yaml", file=sys.stderr)
            return 1

    for entry in repos:
        name = entry["name"]
        repo_path = lib.resolve_repo_path(entry["path"])
        print(f"{name} ({repo_path})")
        for doc in entry["docs"]:
            target = repo_path / doc
            if not target.is_symlink():
                print(f"  [skip] {target}: not a symlink")
                continue
            resolved = target.resolve()
            try:
                resolved.relative_to((anchor / "docs" / name).resolve())
            except ValueError:
                print(f"  [skip] {target}: doesn't point into this tool's anchor, leaving alone")
                continue
            if args.dry_run:
                print(f"  [dry-run] would remove {target} (-> {resolved})")
                continue
            target.unlink()
            print(f"  [removed] {target}")

    print(
        "\nnote: any *.bak-* files created during install were left in place -- "
        "rename them back by hand if you want the original file restored."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

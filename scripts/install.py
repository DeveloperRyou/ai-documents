#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Symlink CLAUDE.md/.claude into registered repos.")
    parser.add_argument("--config", default=None, help="path to repo.yaml (default: repo root)")
    parser.add_argument("--only", default=None, help="only sync the repo with this name")
    parser.add_argument("--dry-run", action="store_true", help="print what would happen, change nothing")
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else lib.repo_root() / "repo.yaml"

    try:
        config = lib.parse_config(config_path)
        lib.install(config, only=args.only, dry_run=args.dry_run)
    except lib.ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

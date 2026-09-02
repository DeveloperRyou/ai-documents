#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="git pull ai-documents, then re-run install.")
    parser.add_argument("--config", default=None, help="path to repo.yaml (default: repo root)")
    parser.add_argument("--dry-run", action="store_true", help="skip git pull, print what install would do")
    args = parser.parse_args()

    root = lib.repo_root()

    if not args.dry_run:
        result = subprocess.run(["git", "-C", str(root), "pull", "--ff-only"])
        if result.returncode != 0:
            print(
                "error: git pull --ff-only failed -- resolve manually in "
                f"{root} (diverged history or local changes), then re-run update.sh",
                file=sys.stderr,
            )
            return result.returncode
    else:
        print(f"[dry-run] would run: git -C {root} pull --ff-only")

    config_path = Path(args.config) if args.config else root / "repo.yaml"
    try:
        config = lib.parse_config(config_path)
        lib.install(config, dry_run=args.dry_run)
    except lib.ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

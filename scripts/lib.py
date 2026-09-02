"""Shared logic for install.py / update.py / uninstall.py.

Deliberately dependency-free (no PyYAML) since repo.yaml's grammar is
restricted on purpose -- see the comment at the top of repo.yaml.
"""

from __future__ import annotations

import datetime
import os
import shutil
from pathlib import Path

DEFAULT_ANCHOR = "~/.local/share/ai-documents"


class ConfigError(RuntimeError):
    pass


def repo_root() -> Path:
    """Real (symlink-resolved) directory this ai-documents checkout lives in."""
    return Path(__file__).resolve().parent.parent


def parse_config(path: Path) -> dict:
    """Parse repo.yaml's restricted subset of YAML.

    Supports exactly:
        anchor: <scalar>
        repos:
          - name: <scalar>
            path: <scalar>
            docs:
              - <scalar>
              - <scalar>
    """
    anchor = None
    repos: list[dict] = []
    current: dict | None = None
    in_docs = False

    def unquote(value: str) -> str:
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            return value[1:-1]
        return value

    with open(path, encoding="utf-8") as f:
        for lineno, raw_line in enumerate(f, start=1):
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            if stripped.startswith("anchor:"):
                anchor = unquote(stripped.split(":", 1)[1])
                continue

            if stripped == "repos:":
                in_docs = False
                continue

            if stripped.startswith("- name:"):
                if current is not None:
                    repos.append(current)
                current = {"name": unquote(stripped.split(":", 1)[1]), "path": None, "docs": []}
                in_docs = False
                continue

            if stripped.startswith("path:"):
                if current is None:
                    raise ConfigError(f"{path}:{lineno}: 'path:' outside of a repo entry")
                current["path"] = unquote(stripped.split(":", 1)[1])
                continue

            if stripped.startswith("docs:"):
                if current is None:
                    raise ConfigError(f"{path}:{lineno}: 'docs:' outside of a repo entry")
                in_docs = True
                continue

            if stripped.startswith("- "):
                if not in_docs or current is None:
                    raise ConfigError(f"{path}:{lineno}: unexpected list item: {stripped!r}")
                current["docs"].append(unquote(stripped[2:]))
                continue

            raise ConfigError(f"{path}:{lineno}: unrecognized line: {stripped!r}")

    if current is not None:
        repos.append(current)

    for entry in repos:
        if not entry.get("path"):
            raise ConfigError(f"repo '{entry['name']}' is missing 'path:'")

    return {"anchor": anchor or DEFAULT_ANCHOR, "repos": repos}


def ensure_anchor(anchor_str: str, target: Path, dry_run: bool = False) -> Path:
    """Make sure `anchor_str` is a symlink pointing at `target`.

    This is the first-hop symlink: wherever ai-documents is actually
    checked out, `anchor` always points to it. Per-repo symlinks then
    point through `anchor`, not straight at `target`, so re-cloning
    ai-documents elsewhere only requires re-running install (which just
    repoints this one link) instead of touching every managed repo.
    """
    anchor = Path(anchor_str).expanduser()

    if anchor.is_symlink():
        current = anchor.resolve()
        if current == target:
            return anchor
        if dry_run:
            print(f"[dry-run] would repoint anchor {anchor} -> {target} (was -> {current})")
            return anchor
        anchor.unlink()
        anchor.symlink_to(target, target_is_directory=True)
        print(f"repointed anchor {anchor} -> {target} (was -> {current})")
        return anchor

    if anchor.exists():
        raise ConfigError(
            f"anchor path {anchor} already exists and is not a symlink -- "
            "move or remove it manually, then re-run"
        )

    if dry_run:
        print(f"[dry-run] would create anchor {anchor} -> {target}")
        return anchor

    anchor.parent.mkdir(parents=True, exist_ok=True)
    anchor.symlink_to(target, target_is_directory=True)
    print(f"created anchor {anchor} -> {target}")
    return anchor


def _backup_path(target: Path) -> Path:
    stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return target.with_name(f"{target.name}.bak-{stamp}")


def sync_doc(anchor: Path, repo_name: str, repo_path: Path, doc: str, dry_run: bool = False) -> None:
    source = anchor / "docs" / repo_name / doc
    target = repo_path / doc

    if not source.exists():
        print(f"  [skip] {target}: no source at {source} (create it under docs/{repo_name}/)")
        return

    if target.is_symlink():
        if target.resolve() == source.resolve():
            print(f"  [ok]   {target}")
            return
        if dry_run:
            print(f"  [dry-run] would relink {target} -> {source} (was -> {os.readlink(target)})")
            return
        target.unlink()
    elif target.exists():
        backup = _backup_path(target)
        if dry_run:
            print(f"  [dry-run] would back up {target} -> {backup}, then link -> {source}")
            return
        shutil.move(str(target), str(backup))
        print(f"  [backup] {target} -> {backup}")

    if dry_run:
        print(f"  [dry-run] would link {target} -> {source}")
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(source, target_is_directory=source.is_dir())
    print(f"  [link] {target} -> {source}")


def resolve_repo_path(raw: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise ConfigError(f"repo path {raw!r} must be absolute (or start with ~)")
    return path


def install(config: dict, only: str | None = None, dry_run: bool = False) -> None:
    target = repo_root()
    anchor = ensure_anchor(config["anchor"], target, dry_run=dry_run)

    repos = config["repos"]
    if only:
        repos = [r for r in repos if r["name"] == only]
        if not repos:
            raise ConfigError(f"no repo named {only!r} in repo.yaml")

    if not repos:
        print("no repos registered in repo.yaml yet -- add one under 'repos:' and re-run")
        return

    for entry in repos:
        name = entry["name"]
        repo_path = resolve_repo_path(entry["path"])
        print(f"{name} ({repo_path})")
        if not repo_path.is_dir():
            print(f"  [skip] path does not exist: {repo_path}")
            continue
        for doc in entry["docs"]:
            sync_doc(anchor, name, repo_path, doc, dry_run=dry_run)

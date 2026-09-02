"""Shared logic for install.py / update.py / uninstall.py.

Deliberately dependency-free (no PyYAML) since repo.yaml's grammar is
restricted on purpose -- see the comment at the top of repo.yaml.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import shutil
from pathlib import Path

DEFAULT_ANCHOR = "~/.local/share/ai-documents"

# Directory names never descended into while scanning search_paths.
PRUNE_DIR_NAMES = {
    "node_modules", "venv", ".venv", "dist", "build", "__pycache__",
    ".cache", "target", "vendor", ".next", ".astro",
}

PATH_CACHE_NAME = "path.json"

GIT_EXCLUDE_BEGIN = "# >>> ai-documents: common-derived symlinks (auto-generated, do not edit) >>>"
GIT_EXCLUDE_END = "# <<< ai-documents: common-derived symlinks <<<"


class ConfigError(RuntimeError):
    pass


def repo_root() -> Path:
    """Real (symlink-resolved) directory this ai-documents checkout lives in."""
    return Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# repo.yaml parsing
# ---------------------------------------------------------------------------

def parse_config(path: Path) -> dict:
    """Parse repo.yaml's restricted subset of YAML.

    Supports exactly:
        anchor: <scalar>
        search_paths:
          - <scalar>
        repos:
          - name: <scalar>
            remote: <scalar>
            path: <scalar>        # optional override, skips remote scanning
    """
    anchor = None
    search_paths: list[str] = []
    repos: list[dict] = []
    current: dict | None = None
    top_list: str | None = None

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
                top_list = None
                continue

            if stripped == "search_paths:":
                top_list = "search_paths"
                continue

            if stripped == "repos:":
                if current is not None:
                    repos.append(current)
                    current = None
                top_list = None
                continue

            if stripped.startswith("- name:"):
                if current is not None:
                    repos.append(current)
                current = {"name": unquote(stripped.split(":", 1)[1]), "remote": None, "path": None}
                top_list = None
                continue

            if stripped.startswith("remote:"):
                if current is None:
                    raise ConfigError(f"{path}:{lineno}: 'remote:' outside of a repo entry")
                current["remote"] = unquote(stripped.split(":", 1)[1])
                continue

            if stripped.startswith("path:"):
                if current is None:
                    raise ConfigError(f"{path}:{lineno}: 'path:' outside of a repo entry")
                current["path"] = unquote(stripped.split(":", 1)[1])
                continue

            if stripped.startswith("- "):
                if top_list != "search_paths":
                    raise ConfigError(f"{path}:{lineno}: unexpected list item: {stripped!r}")
                search_paths.append(unquote(stripped[2:]))
                continue

            raise ConfigError(f"{path}:{lineno}: unrecognized line: {stripped!r}")

    if current is not None:
        repos.append(current)

    for entry in repos:
        if not entry.get("remote") and not entry.get("path"):
            raise ConfigError(f"repo '{entry['name']}' needs a 'remote:' (or a 'path:' override)")

    return {
        "anchor": anchor or DEFAULT_ANCHOR,
        "search_paths": search_paths,
        "repos": repos,
    }


# ---------------------------------------------------------------------------
# remote -> local path resolution
# ---------------------------------------------------------------------------

def normalize_remote(url: str) -> str:
    """host/owner/repo, lowercased on the host, with scheme/.git stripped."""
    url = url.strip()
    url = re.sub(r"\.git/?$", "", url)

    m = re.match(r"^[\w.+-]+://(?:[^@/]+@)?([^/]+)/(.+)$", url)  # https://, ssh://, git://
    if m:
        host, tail = m.group(1), m.group(2)
        return f"{host.lower()}/{tail.strip('/')}"

    m = re.match(r"^(?:[^@]+@)?([^:/]+):(.+)$", url)  # scp-like git@host:owner/repo
    if m:
        host, tail = m.group(1), m.group(2)
        return f"{host.lower()}/{tail.strip('/')}"

    return url.lower()


def _remotes_from_git_config(git_config: Path) -> list[str]:
    try:
        text = git_config.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    return re.findall(r"^\s*url\s*=\s*(.+)$", text, re.MULTILINE)


def _repo_matches_remote(repo_dir: Path, wanted_normalized: str) -> bool:
    config = repo_dir / ".git" / "config"
    if not config.is_file():
        return False
    return any(normalize_remote(u) == wanted_normalized for u in _remotes_from_git_config(config))


def _scan_for_remote(search_paths: list[Path], wanted_normalized: str) -> Path | None:
    for root in search_paths:
        if not root.is_dir():
            continue
        for dirpath, dirnames, _filenames in os.walk(root, onerror=lambda e: None):
            dirnames[:] = [d for d in dirnames if d not in PRUNE_DIR_NAMES]
            candidate = Path(dirpath)
            if (candidate / ".git").exists():
                if _repo_matches_remote(candidate, wanted_normalized):
                    return candidate
                dirnames[:] = []  # a repo root; don't descend into it further
    return None


def load_path_cache(anchor_dir: Path) -> dict:
    cache_file = anchor_dir / PATH_CACHE_NAME
    if not cache_file.is_file():
        return {}
    try:
        return json.loads(cache_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_path_cache(anchor_dir: Path, resolved: dict) -> None:
    cache_file = anchor_dir / PATH_CACHE_NAME
    cache_file.write_text(json.dumps(resolved, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve_paths(config: dict, anchor_dir: Path) -> dict[str, Path | None]:
    """Resolve every repo's local path, refreshing anchor_dir/path.json.

    Explicit `path:` overrides win outright. Otherwise, a cached path is
    reused if it still exists and its git remote still matches; anything
    else is found by scanning `search_paths` for a repo whose remote
    matches. Unresolved repos are reported and left out of the cache.
    """
    cache = load_path_cache(anchor_dir)
    search_paths = [Path(p).expanduser() for p in config["search_paths"]]
    resolved: dict[str, Path | None] = {}
    fresh_cache: dict[str, str] = {}

    for entry in config["repos"]:
        name = entry["name"]

        if entry.get("path"):
            path = resolve_repo_path(entry["path"])
            resolved[name] = path
            fresh_cache[name] = str(path)
            continue

        wanted = normalize_remote(entry["remote"])

        cached = cache.get(name)
        if cached and Path(cached).is_dir() and _repo_matches_remote(Path(cached), wanted):
            resolved[name] = Path(cached)
            fresh_cache[name] = cached
            continue

        if not search_paths:
            raise ConfigError("search_paths: is required (add at least one directory to scan)")

        found = _scan_for_remote(search_paths, wanted)
        if found:
            resolved[name] = found
            fresh_cache[name] = str(found)
        else:
            resolved[name] = None
            print(f"  [warn] {name}: no local clone found for {entry['remote']} under {config['search_paths']}")

    save_path_cache(anchor_dir, fresh_cache)
    return resolved


def resolve_repo_path(raw: str) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise ConfigError(f"path {raw!r} must be absolute (or start with ~)")
    return path


# ---------------------------------------------------------------------------
# generic symlink-with-backup
# ---------------------------------------------------------------------------

def _backup_path(target: Path) -> Path:
    stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return target.with_name(f"{target.name}.bak-{stamp}")


def link_with_backup(source: Path, target: Path, dry_run: bool = False, prefix: str = "  ") -> None:
    if target.is_symlink():
        if target.resolve() == source.resolve():
            print(f"{prefix}[ok]   {target}")
            return
        if dry_run:
            print(f"{prefix}[dry-run] would relink {target} -> {source} (was -> {os.readlink(target)})")
            return
        target.unlink()
    elif target.exists():
        backup = _backup_path(target)
        if dry_run:
            print(f"{prefix}[dry-run] would back up {target} -> {backup}, then link -> {source}")
            return
        shutil.move(str(target), str(backup))
        print(f"{prefix}[backup] {target} -> {backup}")

    if dry_run:
        print(f"{prefix}[dry-run] would link {target} -> {source}")
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(source, target_is_directory=source.is_dir())
    print(f"{prefix}[link] {target} -> {source}")


# ---------------------------------------------------------------------------
# projects/_common/ -> projects/<name>/ (first-hop, stays inside this repo)
# ---------------------------------------------------------------------------

def sync_common(config: dict, ai_documents_root: Path, dry_run: bool = False) -> list[str]:
    """Mirror every *file* under projects/_common/ into every registered
    repo's projects/<name>/ folder, recreating _common's directory
    structure with real directories (never symlinking a whole folder from
    _common, only individual files).

    Returns the ai-documents-relative paths that were created/refreshed,
    so the caller can keep them out of git tracking (see update_git_exclude).
    """
    common_dir = ai_documents_root / "projects" / "_common"
    if not common_dir.is_dir():
        return []

    common_files = sorted(
        p.relative_to(common_dir)
        for p in common_dir.rglob("*")
        if p.is_file() and p.name != ".gitkeep"
    )
    if not common_files:
        return []

    managed: list[str] = []
    for entry in config["repos"]:
        name = entry["name"]
        project_dir = ai_documents_root / "projects" / name
        for rel in common_files:
            source = common_dir / rel
            target = project_dir / rel
            link_with_backup(source, target, dry_run=dry_run, prefix="  [common] ")
            managed.append(str(target.relative_to(ai_documents_root)))
    return managed


def update_git_exclude(ai_documents_root: Path, managed_paths: list[str], dry_run: bool = False) -> None:
    """Keep projects/_common/-derived symlinks out of git tracking via the
    per-clone `.git/info/exclude` (not `.gitignore`, which is committed and
    shared -- these paths are local-machine bookkeeping, not repo content).
    """
    git_dir = ai_documents_root / ".git"
    if not git_dir.is_dir():
        return
    exclude_file = git_dir / "info" / "exclude"
    existing = exclude_file.read_text(encoding="utf-8") if exclude_file.exists() else ""
    lines = existing.splitlines()

    if GIT_EXCLUDE_BEGIN in lines:
        start = lines.index(GIT_EXCLUDE_BEGIN)
        end = lines.index(GIT_EXCLUDE_END) if GIT_EXCLUDE_END in lines else len(lines) - 1
        lines = lines[:start] + lines[end + 1:]
    lines = [line for line in lines if line.strip()]

    if managed_paths:
        lines += [GIT_EXCLUDE_BEGIN, *sorted(managed_paths), GIT_EXCLUDE_END]

    new_content = ("\n".join(lines) + "\n") if lines else ""
    if new_content == existing:
        return

    if dry_run:
        print(f"[dry-run] would update {exclude_file} ({len(managed_paths)} managed path(s))")
        return

    exclude_file.parent.mkdir(parents=True, exist_ok=True)
    exclude_file.write_text(new_content, encoding="utf-8")
    print(f"updated {exclude_file} ({len(managed_paths)} managed path(s))")


# ---------------------------------------------------------------------------
# projects/<name>/ -> target repo (second hop, via the anchor)
# ---------------------------------------------------------------------------

def project_entries(anchor: Path, repo_name: str) -> list[str]:
    project_dir = anchor / "projects" / repo_name
    if not project_dir.is_dir():
        return []
    return sorted(p.name for p in project_dir.iterdir() if p.name != ".gitkeep")


def sync_repo(anchor: Path, repo_name: str, repo_path: Path, dry_run: bool = False) -> None:
    entries = project_entries(anchor, repo_name)
    if not entries:
        print(f"  [skip] no files under projects/{repo_name}/ to link")
        return
    for doc in entries:
        source = anchor / "projects" / repo_name / doc
        target = repo_path / doc
        link_with_backup(source, target, dry_run=dry_run, prefix="  ")


def ensure_anchor(anchor_str: str, target: Path, dry_run: bool = False) -> Path:
    """Make sure `anchor_str` is a symlink pointing at `target`.

    This is the second-hop symlink's anchor: wherever ai-documents is
    actually checked out, `anchor` always points to it. Per-repo symlinks
    then point through `anchor`, not straight at `target`, so re-cloning
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


def install(config: dict, only: str | None = None, dry_run: bool = False) -> None:
    target = repo_root()
    anchor = ensure_anchor(config["anchor"], target, dry_run=dry_run)

    print("syncing projects/_common/ ...")
    managed = sync_common(config, target, dry_run=dry_run)
    update_git_exclude(target, managed, dry_run=dry_run)

    repos = config["repos"]
    if only:
        repos = [r for r in repos if r["name"] == only]
        if not repos:
            raise ConfigError(f"no repo named {only!r} in repo.yaml")

    if not repos:
        print("no repos registered in repo.yaml yet -- add one under 'repos:' and re-run")
        return

    print("resolving repo paths...")
    resolved = resolve_paths(config, anchor)

    for entry in repos:
        name = entry["name"]
        repo_path = resolved.get(name)
        print(f"{name}" + (f" ({repo_path})" if repo_path else " (unresolved)"))
        if repo_path is None:
            continue
        if not repo_path.is_dir():
            print(f"  [skip] path does not exist: {repo_path}")
            continue
        sync_repo(anchor, name, repo_path, dry_run=dry_run)

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
import subprocess
from pathlib import Path

DEFAULT_ANCHOR = "/opt/ai-documents"

# Directory names never descended into while scanning search_paths.
PRUNE_DIR_NAMES = {
    "node_modules", "venv", ".venv", "dist", "build", "__pycache__",
    ".cache", "target", "vendor", ".next", ".astro",
}

PATH_CACHE_NAME = "path.json"

GIT_EXCLUDE_BEGIN = "# >>> ai-documents: common-derived symlinks (auto-generated, do not edit) >>>"
GIT_EXCLUDE_END = "# <<< ai-documents: common-derived symlinks <<<"

# _common/ files whose per-repo copy is JSON-merged instead of symlinked
# straight through, when a matching *.override.json sits next to them
# under projects/<name>/ -- see merge_json_files() / sync_common().
MERGE_JSON_FILENAMES = {"settings.json"}


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


def resolve_paths(config: dict, anchor_dir: Path, dry_run: bool = False) -> dict[str, Path | None]:
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

    if dry_run:
        print(f"[dry-run] would write {anchor_dir / PATH_CACHE_NAME}")
    else:
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


def deep_merge(base, override):
    """Recursively merge `override` onto `base`, returning a new value.

    dict values merge key-by-key; list values are concatenated (base
    items first) with exact duplicates dropped; anything else -- scalars,
    or a type mismatch between base/override -- and `override` wins
    outright.
    """
    if not isinstance(base, dict) or not isinstance(override, dict):
        return override
    merged = dict(base)
    for key, value in override.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = deep_merge(existing, value)
        elif isinstance(existing, list) and isinstance(value, list):
            combined = list(existing)
            combined += [item for item in value if item not in combined]
            merged[key] = combined
        else:
            merged[key] = value
    return merged


def merge_json_files(base_path: Path, override_path: Path) -> str:
    """Deep-merge `override_path`'s JSON onto `base_path`'s (base may be
    absent), returning the merged document serialized with a trailing
    newline."""
    base = json.loads(base_path.read_text(encoding="utf-8")) if base_path.is_file() else {}
    override = json.loads(override_path.read_text(encoding="utf-8"))
    merged = deep_merge(base, override)
    return json.dumps(merged, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def write_with_backup(content: str, target: Path, dry_run: bool = False, prefix: str = "  ") -> None:
    """Like link_with_backup, but writes generated text content instead
    of creating a symlink -- used for the merged JSON files sync_common
    produces. A pre-existing symlink is replaced outright (it's just a
    stale plain mirror from before an override existed); a pre-existing
    real file is backed up only if its content actually differs."""
    if target.is_symlink():
        if dry_run:
            print(f"{prefix}[dry-run] would replace symlink {target} with generated file")
            return
        target.unlink()
    elif target.exists():
        try:
            if target.read_text(encoding="utf-8") == content:
                print(f"{prefix}[ok]   {target}")
                return
        except OSError:
            pass
        backup = _backup_path(target)
        if dry_run:
            print(f"{prefix}[dry-run] would back up {target} -> {backup}, then write generated file")
            return
        shutil.move(str(target), str(backup))
        print(f"{prefix}[backup] {target} -> {backup}")

    if dry_run:
        print(f"{prefix}[dry-run] would write generated file -> {target}")
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print(f"{prefix}[merge] {target}")


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

    A file named in MERGE_JSON_FILENAMES (currently just settings.json) is
    special-cased: if projects/<name>/ already has a sibling
    `<stem>.override.json` at that same path (a real, repo-specific file
    the user maintains by hand), the two are deep-merged (see
    merge_json_files) and the result is written as a real file instead of
    symlinked, so repo-specific settings survive alongside _common's.

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

            if rel.name in MERGE_JSON_FILENAMES:
                override = target.with_name(f"{target.stem}.override{target.suffix}")
                if override.is_file():
                    merged = merge_json_files(source, override)
                    write_with_backup(merged, target, dry_run=dry_run, prefix="  [common] ")
                    managed.append(str(target.relative_to(ai_documents_root)))
                    continue

            link_with_backup(source, target, dry_run=dry_run, prefix="  [common] ")
            managed.append(str(target.relative_to(ai_documents_root)))
    return managed


def update_git_exclude(repo_dir: Path, managed_paths: list[str], dry_run: bool = False) -> None:
    """Keep projects/_common/-derived symlinks out of this repo's own git
    tracking via its per-clone `.git/info/exclude` (not `.gitignore`,
    which is committed and shared -- these paths are local-machine
    bookkeeping regenerated on every run, not repo content).
    """
    git_dir = repo_dir / ".git"
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

def project_entries(checkout: Path, repo_name: str) -> list[str]:
    project_dir = checkout / "projects" / repo_name
    if not project_dir.is_dir():
        return []
    return sorted(p.name for p in project_dir.iterdir() if p.name != ".gitkeep")


def sync_repo(checkout: Path, repo_name: str, repo_path: Path, dry_run: bool = False) -> None:
    entries = project_entries(checkout, repo_name)
    if not entries:
        print(f"  [skip] no files under projects/{repo_name}/ to link")
        return
    for doc in entries:
        source = checkout / "projects" / repo_name / doc
        target = repo_path / doc
        link_with_backup(source, target, dry_run=dry_run, prefix="  ")


def anchor_checkout(anchor_dir: Path) -> Path:
    return anchor_dir / "checkout"


def _sudo_provision_anchor(anchor_dir: Path) -> None:
    """One-time, interactive: create anchor_dir (under root-owned /opt by
    default) and hand ownership to the current user, so every later run
    can manage `anchor_dir/checkout` without sudo. Prompts via sudo's own
    password prompt -- only runs when anchor_dir doesn't exist yet.
    """
    print(f"one-time setup: creating {anchor_dir} (needs sudo)")
    uid, gid = os.getuid(), os.getgid()
    try:
        subprocess.run(["sudo", "mkdir", "-p", str(anchor_dir)], check=True)
        subprocess.run(["sudo", "chown", f"{uid}:{gid}", str(anchor_dir)], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise ConfigError(
            f"failed to create {anchor_dir} via sudo -- create it manually, then re-run:\n"
            f'  sudo mkdir -p "{anchor_dir}" && sudo chown "$(whoami)":"$(whoami)" "{anchor_dir}"'
        ) from e


def ensure_anchor(anchor_dir: Path, target: Path, dry_run: bool = False) -> Path:
    """Make sure `anchor_dir/checkout` is a symlink pointing at `target`,
    returning that symlink's path.

    `anchor_dir` itself (default /opt/ai-documents) is a plain, user-owned
    directory -- NOT a symlink -- because its parent (/opt) is root-owned
    and a normal user can never repoint an entry living directly inside
    it. Putting one more level of indirection (`checkout`) inside a
    directory the user does own sidesteps that: only the one-time setup
    below needs privilege, every later repoint is a normal file op.

    `checkout` is the second-hop symlink's target: wherever ai-documents
    is actually checked out, `checkout` always points to it. Per-repo
    symlinks point through `checkout`, not straight at `target`, so
    re-cloning ai-documents elsewhere only requires re-running install
    (which just repoints this one link) instead of touching every
    managed repo.
    """
    if not anchor_dir.exists():
        if dry_run:
            print(f"[dry-run] would create {anchor_dir} (one-time, via sudo)")
        else:
            try:
                anchor_dir.mkdir(parents=True)
            except PermissionError:
                _sudo_provision_anchor(anchor_dir)
    elif not os.access(anchor_dir, os.W_OK):
        raise ConfigError(
            f"{anchor_dir} exists but isn't writable by you -- run this once, then re-run:\n"
            f'  sudo chown "$(whoami)":"$(whoami)" "{anchor_dir}"'
        )

    checkout = anchor_checkout(anchor_dir)

    if checkout.is_symlink():
        current = checkout.resolve()
        if current == target:
            return checkout
        if dry_run:
            print(f"[dry-run] would repoint {checkout} -> {target} (was -> {current})")
            return checkout
        checkout.unlink()
        checkout.symlink_to(target, target_is_directory=True)
        print(f"repointed {checkout} -> {target} (was -> {current})")
        return checkout

    if checkout.exists():
        raise ConfigError(
            f"{checkout} already exists and is not a symlink -- move or remove it manually, then re-run"
        )

    if dry_run:
        print(f"[dry-run] would create {checkout} -> {target}")
        return checkout

    checkout.symlink_to(target, target_is_directory=True)
    print(f"created {checkout} -> {target}")
    return checkout


def install(config: dict, only: str | None = None, dry_run: bool = False) -> None:
    target = repo_root()
    anchor_dir = Path(config["anchor"]).expanduser()
    checkout = ensure_anchor(anchor_dir, target, dry_run=dry_run)

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
    resolved = resolve_paths(config, anchor_dir, dry_run=dry_run)

    for entry in repos:
        name = entry["name"]
        repo_path = resolved.get(name)
        print(f"{name}" + (f" ({repo_path})" if repo_path else " (unresolved)"))
        if repo_path is None:
            continue
        if not repo_path.is_dir():
            print(f"  [skip] path does not exist: {repo_path}")
            continue
        sync_repo(checkout, name, repo_path, dry_run=dry_run)

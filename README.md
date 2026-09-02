# ai-documents

Central place for the `CLAUDE.md` / `.claude/` files scattered across every
project repo, so they don't have to be maintained separately in each one.

## How it works

- `repo.yaml` lists the repos this manages: a `name`, a `path` on disk, and
  which `docs` (top-level files or directories, e.g. `CLAUDE.md`, `.claude`)
  to sync into it.
- The actual content lives under `docs/<name>/` in this repo.
- `install.sh` symlinks `docs/<name>/<doc>` into `<path>/<doc>` for every
  registered repo.

### Why a two-hop symlink

This repo can be cloned to different paths on different machines. If each
target repo's symlink pointed straight at wherever `ai-documents` happened
to be checked out, moving or re-cloning it would break every link it made.

Instead, `install.sh` first makes sure a stable **anchor** path (default
`~/.local/share/ai-documents`, configurable via `anchor:` in `repo.yaml`)
is a symlink to this checkout. Every per-repo symlink then points through
the anchor, not directly at this checkout:

```
<repo>/CLAUDE.md  →  ~/.local/share/ai-documents/docs/<repo>/CLAUDE.md  →  (this repo)/docs/<repo>/CLAUDE.md
```

Re-cloning `ai-documents` somewhere else and re-running `install.sh` only
repoints the anchor (one symlink); nothing in the managed repos needs to
change.

## Usage

```bash
# preview what would happen, changes nothing
./install.sh --dry-run

# symlink CLAUDE.md/.claude into every repo listed in repo.yaml
./install.sh

# only sync one repo
./install.sh --only portfolio

# pull the latest docs from this repo, then re-sync everything
./update.sh

# remove the symlinks this tool created (leaves docs/ and any .bak-* files alone)
./uninstall.sh
```

Requires `python3` and `git`; no other dependencies.

## Adding a repo

1. `mkdir -p docs/<name>` and add its `CLAUDE.md` / `.claude/` there.
2. Add an entry under `repos:` in `repo.yaml`:
   ```yaml
   repos:
     - name: <name>
       path: ~/Develop/example/<name>
       docs:
         - CLAUDE.md
         - .claude
   ```
3. `./install.sh --only <name>`

## Known limitations (draft state)

- `repo.yaml` uses a deliberately restricted YAML subset (see the comment
  at the top of the file, enforced by `scripts/lib.py`) instead of a real
  YAML parser -- no external dependency, but no nested structures beyond
  what's documented there either.
- Removing a `docs:` entry or a whole repo from `repo.yaml` does not
  auto-remove its old symlink; run `./uninstall.sh --only <name>` first.
- If a target path already has a real (non-symlink) file where a doc would
  go, install backs it up to `<file>.bak-<timestamp>` next to it rather
  than overwriting it.

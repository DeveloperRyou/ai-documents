# ai-documents

Central place for the `CLAUDE.md` / `.claude/` files scattered across every
project repo, so they don't have to be maintained separately in each one.

## How it works

- `repo.yaml` lists the repos this manages by **git remote**, not by local
  path -- `install.sh` scans `search_paths` for a clone whose remote
  matches, and caches the result per machine in `<anchor>/path.json`.
- The actual content lives under `projects/<name>/` in this repo, plus a
  shared `projects/_common/` that gets mirrored into every repo.
- `install.sh` symlinks the top level of `projects/<name>/` into the
  matching repo -- whatever files/folders are there, no explicit list
  needed in `repo.yaml`.

### Two symlink hops, plus a `_common` mirror step before them

This repo can be cloned to different paths on different machines. If each
target repo's symlink pointed straight at wherever `ai-documents` happened
to be checked out, moving or re-cloning it would break every link it made.

So `install.sh` first makes sure a stable **anchor** path (default
`~/.local/share/ai-documents`, configurable via `anchor:` in `repo.yaml`)
is a symlink to this checkout, and every per-repo symlink points through
the anchor instead of straight at this checkout. Before that, every file
under `projects/_common/` is mirrored into each repo's `projects/<name>/`
folder, so the top-level walk that follows picks it up automatically:

```
projects/_common/CLAUDE.md
  → (mirrored)   projects/portfolio/CLAUDE.md
  → (anchor hop) ~/.local/share/ai-documents/projects/portfolio/CLAUDE.md
  → (repo hop)   <portfolio path>/CLAUDE.md
```

Re-cloning `ai-documents` somewhere else and re-running `install.sh` only
repoints the anchor (one symlink); nothing in the managed repos needs to
change. See `projects/README.md` for the `_common/` mirroring rules.

## Usage

```bash
# preview what would happen, changes nothing
./install.sh --dry-run

# resolve every repo's path by git remote, sync _common/, then symlink
# projects/<name>/ into every repo listed in repo.yaml
./install.sh

# only sync one repo
./install.sh --only portfolio

# git pull this repo, then re-run the full install
./update.sh

# remove the symlinks this tool created in target repos
# (leaves projects/ and any .bak-* files alone)
./uninstall.sh
```

Requires `python3` and `git`; no other dependencies.

## Adding a repo

1. Add an entry under `repos:` in `repo.yaml`:
   ```yaml
   repos:
     - name: <name>
       remote: https://github.com/<owner>/<name>.git
   ```
2. Make sure `<name>` is cloned somewhere under one of `search_paths:`.
3. `mkdir -p projects/<name>` and add anything specific to that repo there
   (it inherits everything under `projects/_common/` automatically).
4. `./install.sh --only <name>`

## Known limitations (draft state)

- `repo.yaml` uses a deliberately restricted YAML subset (see the comment
  at the top of the file, enforced by `scripts/lib.py`) instead of a real
  YAML parser -- no external dependency, but no nested structures beyond
  what's documented there either.
- If a remote is cloned in more than one place under `search_paths`, the
  first one `os.walk` happens to visit wins.
- Removing a repo from `repo.yaml`, or a file from `projects/<name>/`,
  does not auto-remove its old symlink in the target repo; run
  `./uninstall.sh --only <name>` first.
- If a target path already has a real (non-symlink) file where a synced
  entry would go, install backs it up to `<file>.bak-<timestamp>` next to
  it rather than overwriting it -- same for `_common/` mirroring into
  `projects/<name>/`.

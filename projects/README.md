# projects/

Each registered repo in `repo.yaml` has a matching folder here:

```
projects/
  _common/
    CLAUDE.md
    .claude/commands/...
  portfolio/
    ...
  ai-documents/
    ...
```

## `_common/` (shared across every repo)

Every *file* under `projects/_common/` (recursively; directories themselves
are never symlinked, only the files inside them) gets mirrored into every
registered repo's `projects/<name>/` folder as a symlink, before anything
is linked out to the actual target repos. This happens automatically on
every `install.sh`/`update.sh` run.

These mirrored symlinks live inside `projects/<name>/` in this repo, but
are excluded from git tracking via `.git/info/exclude` (not `.gitignore`
-- that stays local to this clone, regenerated on every run) so they
don't get committed.

If a repo already has a real (non-symlink) file at the same relative
path, `_common` still wins: the real file is backed up to
`<file>.bak-<timestamp>` next to it and replaced with the common symlink.
Put anything you don't want a repo to inherit from `_common` at a
different path instead.

## `<repo-name>/` (per-repo)

`install.sh` walks the **top level** of `projects/<repo-name>/` (which by
then also contains whatever got mirrored in from `_common/`) and symlinks
each entry -- whole files or whole directories -- into the matching path
inside that repo, e.g. `projects/portfolio/CLAUDE.md` ->
`<portfolio path>/CLAUDE.md`, `projects/portfolio/.claude` ->
`<portfolio path>/.claude`.

## Adding a new repo

1. Add an entry under `repos:` in `repo.yaml` (`name` + `remote`).
2. `mkdir -p projects/<name>` and add anything specific to that repo
   there (it'll pick up everything from `_common/` automatically).
3. `./install.sh --only <name>` (or `--dry-run` first to preview).

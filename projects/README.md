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

### `_common/CLAUDE.md` content -> `.claude/RULES.md` + an import line

A repo's own `CLAUDE.md` (`projects/<name>/CLAUDE.md`) is *not* something
`_common` can safely also provide under that same filename -- it would
just overwrite each repo's actual project-specific content on the next
sync. Instead, shared rules live in `projects/_common/.claude/RULES.md`
(mirrored like any other `_common` file), and each repo's own `CLAUDE.md`
pulls it in with a one-line import near the top:

```
@.claude/RULES.md
```

Add that line to any new repo's `projects/<name>/CLAUDE.md` when you
create it.

### `settings.json` merging

`.claude/settings.json` has the same problem as `CLAUDE.md`: if
`_common` provides one, a repo can't also keep its own real
`.claude/settings.json` at that path -- there's only one file there. So
`settings.json` (matched by filename, wherever it appears under
`_common`) is special-cased in `sync_common`: if
`projects/<name>/.claude/settings.override.json` exists (a real,
repo-specific file you maintain by hand in this repo), it's deep-merged
onto `_common`'s `settings.json` -- object keys merge recursively, list
values are concatenated with duplicates dropped, scalars are overridden
-- and the result is written as a real generated
`projects/<name>/.claude/settings.json` (git-excluded like the rest of
`_common`'s mirrored output). No override file present -> plain symlink,
same as everything else.

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

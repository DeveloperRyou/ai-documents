# docs/

Each registered repo in `repo.yaml` has a matching folder here:

```
docs/
  <repo-name>/
    CLAUDE.md
    .claude/
      ...
```

`install.sh` symlinks `docs/<repo-name>/<doc>` into `<repo path>/<doc>` for
every `doc` listed under that repo's `docs:` entry. Edit the files here, run
`update.sh` (or `install.sh`) from wherever you use Claude Code, and every
registered repo picks up the change through its symlink.

To add a new repo:

1. `mkdir -p docs/<repo-name>` and put its `CLAUDE.md` / `.claude/` there
   (copy an existing one as a starting point, or write from scratch).
2. Add an entry for it under `repos:` in `repo.yaml`.
3. Run `./install.sh --only <repo-name>` (or `--dry-run` first to preview).

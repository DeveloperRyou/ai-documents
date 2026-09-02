# ai-documents

@.claude/RULES.md

## Workflow

- Commit and push directly to `main` -- no feature branches or PRs for
  this repo.

This is the repo that manages itself: it registers other repos'
`CLAUDE.md`/`.claude` (and its own, via this file) and symlinks them in
by remote, not by hardcoded path.

- Repos are matched by git remote (`repo.yaml`'s `remote:`), resolved by
  scanning `search_paths:` and cached per machine in `<anchor>/path.json`
  (gitignored -- never commit resolved local paths).
- `projects/_common/` is mirrored file-by-file into every repo's
  `projects/<name>/` before the per-repo sync runs; those mirrored
  symlinks are excluded from git via `.git/info/exclude`, regenerated on
  every `install.sh`/`update.sh` run -- not `.gitignore`.
- `scripts/lib.py` has no external dependencies on purpose (no PyYAML,
  no `yq`): `repo.yaml` is parsed with a small hand-rolled parser that
  only understands the restricted shape documented at the top of the
  file. Don't add YAML features without also extending that parser.
- Symlinks are two-hop by design: `<repo>/CLAUDE.md` -> anchor -> this
  checkout, so re-cloning `ai-documents` elsewhere only means re-running
  `install.sh` to repoint the anchor -- nothing in managed repos changes.

# Common rules (managed by ai-documents)

- `.claude/` in this repo is a symlink managed by the `ai-documents` repo
  (https://github.com/DeveloperRyou/ai-documents), not real content that
  lives here. If something under `.claude/` needs to change, don't edit
  it in this repo -- edit it in `ai-documents` instead, under
  `projects/<this-repo>/.claude/` for a change specific to this repo, or
  `projects/_common/.claude/` if it should apply to every managed repo --
  then follow `ai-documents`'s own modification rule (commit and push
  straight to `main`, no branch/PR) and re-run `install.sh`/`update.sh`
  to propagate the change back here.

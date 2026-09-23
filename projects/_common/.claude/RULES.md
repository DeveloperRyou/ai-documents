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
- After finishing a task (a code change, an investigation, anything the
  user asked for), give the final report to the user in Korean, kept
  brief -- what changed and what's next, not a restatement of the whole
  session.
- Session size is the main cost driver: every turn re-reads the whole
  history, so a 500k-token session pays ~500k tokens per tool call. When
  the user starts unrelated work, or context passes ~200k tokens (the
  `context-watch` hook injects a `[context-watch]` note when either
  happens), first write a note with the `handoff` skill, then suggest in
  one line continuing in a fresh session (`/clear`) -- or `/compact` if
  the current task is still mid-flight. You can't run either yourself;
  suggest once, and drop it if the user declines.
- Keep bulky output out of the main context: screenshots, full-page
  images, long logs, and whole large files stay for the rest of the
  session once read. Grep for the location first and read with
  `offset`/`limit`; don't re-read a file just edited to verify it; never
  `Read` a saved PNG unless the user asked to see it; pipe long command
  output through `tail`/`grep`. For work that inherently produces bulky
  output (visual checks, log triage), use a script or subagent that
  returns only a verdict.
- Local LLM (`local-llm` skill) runs via a direct Bash call to its
  `run.py` -- never through a subagent that exists only to call it. It
  pays off where it keeps work *out of* the main context (multi-role
  review, image pre-checks, hook-side classification), not where it just
  replaces an edit you could make directly.

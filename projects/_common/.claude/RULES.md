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
- Output format (output tokens are the priciest; the user reads only
  the final report, and details already live in the PR/commit/issue):
  - Between tool calls, work silently. Write a line only when a finding
    changes the plan, or as a one-line status when asked for one.
  - Final report: Korean, at most ~6 short lines, in this order -- the
    result in one line; what the user must check or decide; the next
    step. Link only what the user opens next (the PR, not also the
    issue it closes).
  - Leave out of chat: restating the request or decisions the user
    already made; a list of passed checks (say "lint/build 통과" in one
    phrase); file-by-file changes; tool hiccups already recovered from;
    cleanup trivia; reviewer false positives. Verification evidence and
    design detail go in the PR body -- point to it, don't repeat it.
  - Still say, in one line, anything unresolved or skipped that changes
    what the user should do (a failing check, an unverified path, an
    assumption they didn't approve).
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

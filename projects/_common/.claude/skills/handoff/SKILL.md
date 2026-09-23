---
name: handoff
description: Use when a session should end so work can continue in a fresh one -- the context-watch hook flagged a large context or a topic switch, the user says they're wrapping up / switching tasks, or asks to "save where we are". Writes a <=10-line handoff note (branch/worktree, open PR, decided things, remaining TODOs) that a new session reads instead of the old transcript. Also use at the start of a session when the user says "continue"/"이어서" to read the latest note back.
---

# Handoff note

A long session's cost is dominated by re-reading its own history every
turn, so the cheapest continuation is a fresh session that starts from
a short note instead of the whole transcript. This skill is that note.

## Writing one

1. Gather facts, don't recall them: `git branch --show-current`,
   `git worktree list`, `gh pr list --author @me --state open` (for the
   repo you're in), and the issue number if the work is tied to one.
2. Write **at most 10 lines** to `~/.claude/handoffs/<repo-name>.md`
   (`<repo-name>` = basename of the main checkout, e.g. `portfolio`),
   overwriting the previous note for that repo:

   ```
   # <repo-name> handoff -- <YYYY-MM-DD HH:MM>
   Task: <one line: what the user is trying to get done>
   Where: branch <b> (worktree <path>), PR #<n> <open|draft>, issue #<n>
   Decided: <user decisions that must not be re-litigated, ;-separated>
   Done: <what's finished and verified>
   Next: <the next concrete step>
   Open questions: <anything waiting on the user, or "none">
   Dev server: <running on :4321 from <branch> | not running>
   ```

   Only facts a fresh session can't cheaply re-derive belong here --
   no file contents, diffs, screenshots, or logs (it can `git diff`).
   Design decisions the user stated in chat ("chips in English", "no
   hover on non-link cards") are the most valuable lines: they exist
   nowhere else.
3. If the work is tied to an issue and the note has decisions worth
   keeping past this branch, also post the `Decided:` line as an issue
   comment (`gh issue comment <n>`). Skip this for throwaway state.
4. Tell the user, in one line, that the note is saved and they can
   `/clear` and say "이어서" (or `/handoff`) to resume.

## Resuming from one

Read `~/.claude/handoffs/<repo-name>.md`, confirm the branch/worktree
still exists (`git worktree list`), and continue from `Next:`. Don't
re-open files or re-run checks the note marks as done unless something
contradicts it.

## Common Mistakes

- **Writing a session summary instead of a handoff.** The note is for
  resuming, not a history -- 10 lines, facts only.
- **Saving it in the session scratchpad.** That directory is
  per-session; a new session can't find it. Use `~/.claude/handoffs/`.
- **Omitting user decisions** because they "seem obvious". A fresh
  session will re-ask or, worse, undo them.

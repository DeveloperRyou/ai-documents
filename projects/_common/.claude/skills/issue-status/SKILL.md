---
name: issue-status
description: Use when asked for a status check on a repo's open issues/PRs, or "what should I work on next" -- lists open PRs and flags what's blocking (failing checks, waiting on review/merge), then lists open issues ranked by rough effort so the next pick is obvious. Read-only reporting; not for filing an issue (`backlog-issue`) or driving one to a PR (`resolve-issue`).
---

# Issue/PR status check

Answers "where do things stand" and "what should I pick up next" without
taking any action itself -- it reports, it doesn't merge, close, or file
anything. Came out of a pattern of nearly every session opening with some
version of this question and getting a fresh, one-off `gh` investigation
each time.

**REQUIRED SUB-SKILL:** Use `gh` for the GitHub CLI invocations below.

**Not for:** filing a new issue (use `backlog-issue`), or actually
implementing/fixing one (use `resolve-issue`). This skill's output is the
input to those, not a replacement for them.

## Step-by-step

1. **Open PRs first** -- these are closer to done and often block other
   work: `gh pr list --state open --json number,title,isDraft,mergeable,statusCheckRollup,reviewDecision,url -L 20`.
   For each, flag it if checks are failing, if it's a draft, or if it's
   green and just waiting on a human look (this repo's workflow keeps a
   dev server up on 4321 for exactly that -- see the target repo's own
   CLAUDE.md before assuming that convention elsewhere).
2. **Open issues next**: `gh issue list --state open --json number,title,labels,body,url -L 30`.
   If the repo already labels issues by size/effort, use those labels --
   don't invent a scheme it doesn't have. If it doesn't, estimate rough
   effort from the issue body (number of files/areas implied, whether the
   acceptance criteria are concrete or still exploratory).
3. **Optional: rank with `jev`** when there are enough open issues that
   eyeballing effort is unreliable -- batch all of them into one `score`
   call (one key per issue in `questions`, same rubric) rather than one
   call per issue. Treat the result as a ranking aid, not gospel; a
   `score` answer is a probability distribution, not a verdict (see the
   `jev` skill's Common Mistakes).
4. **Report**, split into:
   - *Needs attention now* -- open PRs with failing checks, or green and
     waiting on the user's own review/merge call.
   - *Ready to pick up next* -- open issues, easiest/clearest first.
   Include numbers and URLs so the user (or a follow-up `resolve-issue`/
   `ship-pr` call) can act on a specific item without re-looking it up.

## Common Mistakes

- **Taking action.** This skill only reads and reports -- merging,
  closing, or commenting belongs to `ship-pr`/`resolve-issue`, triggered
  as a separate, explicit follow-up.
- **Inventing an effort scale the repo doesn't have.** Read whatever
  labels actually exist before falling back to a heuristic or `jev`.
- **One `jev` call per issue.** Batch them into a single call's
  `questions` map -- same rubric, one key per issue -- instead of paying
  the round-trip cost per issue.
- **Forgetting `-R owner/repo`** when invoked from outside the target
  repo's working directory, or on a machine with multiple repos in play.

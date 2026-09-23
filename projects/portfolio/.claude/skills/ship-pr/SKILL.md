---
name: ship-pr
description: Use when the user has reviewed a PR (typically at the local 4321 preview) and says to merge/ship it -- squash-merges, confirms the linked issue actually closed (closing it explicitly if not), removes the branch/worktree, and stops the now-stale dev server. Picks up exactly where `resolve-issue` leaves off (an open PR); not for opening the PR itself.
---

# Ship a reviewed PR

This repo squash-merges (merge commits are single-parent, titled
`<title> (#N)`) and has `delete_branch_on_merge` turned **off** at the
repo level, so branch/worktree cleanup never happens automatically --
someone has to say "merge it" and then separately remember to close the
issue, delete the branch, and stop the stale dev server. This skill folds
those into the one "ship it" request instead of four separate ones.

**REQUIRED SUB-SKILL:** Use `gh` for the GitHub CLI invocations below.

**Not for:** opening the PR in the first place (that's `resolve-issue`'s
last step), or merging something the user hasn't actually looked at --
this is the "yes, ship it" step, not a substitute for their review.

## Step-by-step

1. **Identify the PR.** Use the number if given; otherwise infer it from
   the branch/worktree currently in play (`gh pr view --json number` from
   inside that worktree, or `gh pr list` matched against the branch name).
2. **Check status first.** `gh pr checks <n>`. If anything is failing,
   stop and report it -- don't merge a red PR just because the user said
   "merge it," unless they explicitly say to override a specific failing
   check.
3. **Merge.** `gh pr merge <n> --squash --delete-branch` -- squash to
   match this repo's existing history, `--delete-branch` because the repo
   won't do it for you.
4. **Confirm the linked issue closed.** If the PR body used a closing
   keyword (`Fixes #N` / `Closes #N`), GitHub closes it automatically on
   merge -- verify with `gh issue view <n> --json state` rather than
   assuming. If it's still open (no closing keyword was present, or the
   keyword pointed at the wrong number), close it explicitly:
   `gh issue close <n> --comment "Fixed by #<pr-number>"`.
5. **Clean up local state.** If the work happened in a separate git
   worktree (the `resolve-issue` convention), `git worktree remove
   <path>`. Delete the local branch if it's still checked out anywhere
   (`git branch -d <branch>`) -- the remote copy is already gone from
   step 3's `--delete-branch`.
6. **Stop the stale dev server.** Per this repo's CLAUDE.md workflow, a
   server left running on 4321 should reflect the *current* branch; once
   this branch is merged and deleted, that's no longer true.
   `npx astro dev stop`. Only start a new one on `main` (or whatever's
   next) if the next task actually calls for it -- don't restart it
   speculatively.
7. **Report back**: the merge commit URL/SHA, and the issue number
   confirmed closed.

## Common Mistakes

- **Merging past a failing check** because the user said "merge it" --
  surface the failure and get an explicit override first.
- **Skipping `--delete-branch`.** This repo doesn't auto-delete on merge;
  omitting the flag leaves a stale branch behind every time.
- **Assuming a closing keyword worked without checking.** `gh issue view
  --json state` is one call -- cheaper than leaving an issue silently
  open after its PR merged.
- **Leaving the dev server pointed at a branch that no longer exists**
  after step 3/5 -- the next person to check 4321 sees a dead preview.

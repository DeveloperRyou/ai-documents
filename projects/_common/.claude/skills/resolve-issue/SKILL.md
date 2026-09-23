---
name: resolve-issue
description: Use when asked to resolve, fix, or close out a specific GitHub issue end-to-end (implementation through PR). Drives a fix / local multi-role review / fix loop -- the review is a single direct `local-llm` `run.py review` call, gated on its exit code -- until no blocker-severity findings remain, then opens the PR.
---

# Resolve GitHub issue

Turns a GitHub issue into a merge-ready PR through a fix / review loop.
The coordinator makes the fix directly; the review is a local model's
multi-role pass, so the coordinator isn't grading its own work alone.
The review is **not** a judgment call the coordinator can skip -- it's a
mandatory step every iteration, until it comes back clean.

**REQUIRED SUB-SKILL:** Use `gh` for the GitHub CLI invocations below.

**Not for:** vague/exploratory issues ("investigate why X is slow"), issues
spanning many unrelated files, or anything security-critical enough that a
7-9B local model reviewing itself isn't good enough -- for those, do the
work directly and use `/code-review` instead of this pipeline.

## The loop

```
1. Intake      -- read the issue, confirm scope, find affected files
2. Branch      -- create an isolated worktree + branch (unless repo convention says otherwise)
3. Fix         -- edit directly (Edit; sed/codemod for mechanical replacements)
4. Review      -- MANDATORY: one `run.py review` call (3 roles in parallel, merged, exit-code gated)
5. Blockers?   -- yes: fix them (step 3), repeat (cap: 4 rounds)
               -- no: continue
6. Verify      -- run the repo's own tests/build/lint if any exist
7. Commit, push, open PR -- carry forward remaining concerns/nits in the PR body
```

### 1. Intake

`gh issue view <number>` (or the issue URL). Pull title, body, and labels.
If the body follows Why/What/Acceptance-Criteria (see the `backlog-issue`
skill's format), that Acceptance Criteria section is what step 4's
`spec` review role checks against -- keep it verbatim, you'll pass it into
every review round. Locate the affected file(s) with Explore/Grep. If the
issue is too vague to produce concrete acceptance criteria from, stop and
ask rather than guessing at scope.

### 2. Branch (in an isolated worktree)

Check the target repo's own `CLAUDE.md`/`RULES.md` for its workflow
convention first -- follow it if it says something specific (e.g. commit
straight to main, no PR). Otherwise the branch name is
`fix/issue-<number>-<slug>`.

Do the work in a **separate git worktree**, not the repo's shared
checkout -- `git worktree add <path> -b fix/issue-<number>-<slug>` (use
`superpowers:using-git-worktrees` if it's available for the mechanics).
The shared checkout is frequently mid-flight on something else entirely
-- a different feature on another branch, or just uncommitted edits
sitting in the working directory -- and `git status` can't tell those
apart from what this loop produces once both are unstaged in the same
tree. That ambiguity is exactly what risks a wrong file getting swept
into step 7's commit, or (worse) discarded by a careless `git checkout
--`/`reset --hard` later in the loop. A dedicated worktree makes this
loop's `git status` only ever show what this loop touched. Creating and
removing a worktree is local and reversible; no need to pause for
confirmation. Remove it (`git worktree remove <path>`) once the PR is
open and merged; leave it in place if the loop stops early so the state
stays inspectable.

### 3. Fix (directly)

Make the change yourself with Edit. For a mechanical replacement across
files (a class prefix, a renamed import), use `sed`/a codemod and check
the result with `git diff --stat` + a grep -- not a model rewriting whole
files. The `local-llm` coder is only for drafting a genuinely **new**
file from scratch (see that skill); describing an edit to it costs about
as much as making it and adds a verification pass.

On round 2+, fix exactly the `blocker` lines the last review printed --
not a vague "improve this."

### 4. Review (mandatory, one direct call)

```
git diff main... > <scratchpad>/round<N>.diff
python3 .claude/skills/local-llm/scripts/run.py review \
  --files <scratchpad>/round<N>.diff \
  --role spec="Only check whether this change satisfies these acceptance criteria, nothing else:
<criteria verbatim>" \
  --role correctness --role simplicity \
  --context "<issue title/why; anything already verified by build/browser>" \
  --out-dir <scratchpad>/review_r<N>
```

Run it in the **foreground** with Bash -- no Agent/subagent wrapper, no
background job to wait on. It runs the three roles in parallel, writes
`<role>.json` + `merged.json`, prints one summary line plus one line per
blocker, and exits 0 (no blockers) or 1 (blockers remain). Read
`merged.json` only if you need a concern/nit for the PR body.

### 5. Gate on blockers

Exit 0: proceed to step 6. Exit 1: go back to step 3, scoped to the
printed blockers.

**Round cap: 4.** If blockers still remain after 4 rounds, stop the loop,
report the remaining blockers and what's been tried, and ask the user how
to proceed instead of continuing to spin.

**Exception: a blocker that contradicts evidence you already hold.** The
reviewer is a 7-9B local model working from a diff alone -- it can't run
a build or a browser. If you (the coordinator) already have direct,
reproducible verification of the actual behavior (e.g. you ran the app
and inspected it, checked compiled/built output, ran a test) and a
blocker's stated mechanism directly contradicts that evidence, don't feed
it back into another fix round on faith. First re-run your own
verification once to make sure it wasn't stale or the wrong branch/state.
If it still holds, treat the blocker as a false positive: skip the round,
and instead of silently dropping it, put the finding, why it's a false
positive, and the concrete evidence that overrides it in the PR body
(the "Known non-blocking items" section from step 7) so a human reviewer
can double check the call. Do not use this to wave away findings you
haven't actually gone and re-verified -- it's for confirmed contradictions
with hard evidence, not for findings you'd merely prefer weren't blockers.

### 6. Verify

Run whatever the repo already uses to check itself (tests, build, lint --
check `package.json`/`Makefile`/CI config for the actual commands, don't
guess). This is the coordinator's job directly, not delegated -- local
models don't run tools. If nothing verifiable exists, say so in the PR
instead of silently skipping it.

### 7. Commit, push, open PR

Commit referencing the issue (`Fixes #<number>`), push, and
`gh pr create`. In the PR body, list any `concern`/`nit` findings from the
final merged review as a short "Known non-blocking items" section so a
human reviewer sees them -- they were surfaced, not silently dropped, just
not treated as ship-blocking. Invoking this skill is the authorization to
push and open the PR as its terminal step; don't pause to re-confirm that
part.

## Common Mistakes

- **Skipping the multi-role split and running one generic review pass.**
  A single call splits attention across bug/security/style/spec at once and
  is measurably weaker at each than three calls each told to focus on one
  lens. `run.py review` defaults to all three -- don't narrow it to one.
- **Dispatching subagents to call the local model.** Each one costs a
  full Claude context plus a "still waiting" turn to collect it; in past
  runs that overhead outweighed what the local model saved. One
  foreground Bash call.
- **Routing a mechanical edit through a model.** A `sm:` -> `lg:` swap
  across four files took seven local-coder dispatches once; `sed` does
  it in one command.
- **Letting the loop run past 4 rounds "because it's close."** That's the
  local model not converging -- escalate to the user instead of burning
  more rounds.
- **Treating `concern`/`nit` as blocking.** Only `blocker` gates the loop.
  Carry the rest forward in the PR body for a human to weigh in on.
- **Spinning fix rounds against a false-positive blocker.** If a
  blocker's stated mechanism is directly contradicted by verification you
  already ran (build output, live app behavior), re-verify once and, if it
  holds, override with the evidence documented in the PR instead of
  looping -- see the round-cap exception above.
- **Branching inside the repo's shared checkout instead of an isolated
  worktree.** Whatever unrelated work is mid-flight there (another
  branch, uncommitted edits) shows up in your `git status` indistinguishably
  from this loop's own changes, risking a stray file getting committed or,
  worse, destroyed by a later destructive git command. Always
  `git worktree add` a fresh directory for the issue branch.

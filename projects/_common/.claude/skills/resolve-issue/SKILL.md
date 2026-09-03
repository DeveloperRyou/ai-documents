---
name: resolve-issue
description: Use when asked to resolve, fix, or close out a specific GitHub issue end-to-end (implementation through PR). Drives a mandatory fix / multi-role-review / fix loop through the local-coder and local-code-reviewer subagents until no blocker-severity findings remain, then opens the PR.
---

# Resolve GitHub issue

Turns a GitHub issue into a merged-ready PR by cycling a local model through
implementation and review, instead of the coordinator writing and grading its
own work. The whole point is that the fix and the review are **not**
judgment calls the coordinator can skip -- both are mandatory pipeline
steps, every iteration, until the review comes back clean.

**REQUIRED SUB-SKILL:** Use `gh` for the GitHub CLI invocations below.

**Not for:** vague/exploratory issues ("investigate why X is slow"), issues
spanning many unrelated files, or anything security-critical enough that a
7-9B local model reviewing itself isn't good enough -- for those, do the
work directly and use `/code-review` instead of this pipeline.

## The loop

```
1. Intake      -- read the issue, confirm scope, find affected files
2. Branch      -- create a working branch (unless repo convention says otherwise)
3. Fix         -- MANDATORY: dispatch local-coder for each affected file
4. Review      -- MANDATORY: dispatch local-code-reviewer 3x in parallel (multi-role)
5. Aggregate   -- scripts/aggregate_review.py merges the 3 reports, gates on blockers
6. Blockers?   -- yes: feed them back into step 3, repeat (cap: 4 rounds)
               -- no: continue
7. Verify      -- run the repo's own tests/build/lint if any exist
8. Commit, push, open PR -- carry forward remaining concerns/nits in the PR body
```

### 1. Intake

`gh issue view <number>` (or the issue URL). Pull title, body, and labels.
If the body follows Why/What/Acceptance-Criteria (see the `backlog-issue`
skill's format), that Acceptance Criteria section is what step 4's
`spec` review role checks against -- keep it verbatim, you'll pass it into
every review round. Locate the affected file(s) with Explore/Grep. If the
issue is too vague to produce concrete acceptance criteria from, stop and
ask rather than guessing at scope.

### 2. Branch

Check the target repo's own `CLAUDE.md`/`RULES.md` for its workflow
convention first -- follow it if it says something specific (e.g. commit
straight to main, no PR). Otherwise create `fix/issue-<number>-<slug>` and
work there. Branch creation is local and reversible; no need to pause for
confirmation.

### 3. Fix (mandatory local-coder dispatch)

For each affected file, dispatch `local-coder` (subagent_type
`"local-coder"`) -- not written directly by the coordinator. Give it:

- The file's **current** full contents (read it first -- on a later round
  this must be the already-partially-fixed version, not the original).
- The issue's Why/What/Acceptance Criteria (or title/body if unstructured).
- On round 2+: the specific `blocker` entries from the last merged review
  that concern this file, verbatim, as the thing to fix -- not a vague
  "improve this."

Independent files can be dispatched in parallel (multiple `Agent` calls in
one message). local-coder writes straight to the target file; there's
nothing further to apply.

### 4. Review (mandatory multi-role local-code-reviewer dispatch)

Dispatch `local-code-reviewer` **three times, in parallel**, on the same
changed file(s), each with a different `[Focus]`:

| Role | Focus text |
|---|---|
| `spec` | "Only check whether this change actually satisfies the issue's acceptance criteria below, nothing else:\n<criteria verbatim>" |
| `correctness` | "Only bugs, edge cases, and security issues." |
| `simplicity` | "Only unnecessary complexity, duplication, and style/convention mismatches with the rest of the file." |

Save each JSON report to the scratchpad directory (e.g.
`review_spec.json`, `review_correctness.json`, `review_simplicity.json`).

### 5. Aggregate and gate

```
python3 .claude/skills/resolve-issue/scripts/aggregate_review.py \
  spec=<review_spec.json> correctness=<review_correctness.json> simplicity=<review_simplicity.json> \
  --out <scratchpad>/merged_review.json
```

Exit code 0 means zero `blocker` findings -- proceed to step 7. Exit code 1
means blockers remain -- read `merged_review.json`'s `issues.blocker` list
and go back to step 3, scoped to just those.

**Round cap: 4.** If blockers still remain after 4 rounds, stop the loop,
report the remaining blockers and what's been tried, and ask the user how
to proceed instead of continuing to spin.

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
  lens. Always three parallel calls, not one.
- **Feeding round 2 the original file instead of the round-1 fix.** local-coder
  has no memory between dispatches -- if you don't pass the current state,
  it redrafts from scratch and can undo the previous round's fix.
- **Letting the loop run past 4 rounds "because it's close."** That's the
  local model not converging -- escalate to the user instead of burning
  more rounds.
- **Treating `concern`/`nit` as blocking.** Only `blocker` gates the loop.
  Carry the rest forward in the PR body for a human to weigh in on.

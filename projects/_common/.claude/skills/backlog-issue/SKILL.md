---
name: backlog-issue
description: "Write a new GitHub issue for the backlog in Why-What-Acceptance format, then file it with `gh issue create`. Use when asked to open/file/create a backlog issue, ticket, or work item on GitHub."
---
# Backlog issue (GitHub)

Turn a feature idea or piece of work into a backlog-ready GitHub issue --
a Why/What/Acceptance-Criteria item, filed with `gh issue create`.
Structure adapted from phuryn/pm-skills' `wwas` skill (MIT license) with
a straight-to-GitHub-issue step folded in.

**Use when:** asked to open/file/create a GitHub issue for a backlog
item or feature. Not for a bug report needing a repro -- follow whatever
bug-report convention the repo already has for those.

**Draft, not gospel:** this is a starting shape. If the repo already has
its own issue conventions (template, label scheme, required sections),
follow those instead of this format.

**Always write the issue in English** -- title and body -- even if the
request or the surrounding conversation is in another language. This
applies regardless of what language the repo's other issues happen to be
in.

## Step-by-step

1. Confirm the target repo (`gh repo view` if ambiguous) and check
   `.github/ISSUE_TEMPLATE/` for an existing template to use instead of
   this one.
2. Draft the item in English, using the template in `reference.md`:
   - **Why** -- 1-2 sentences connecting it to the actual goal or problem
     driving the request. If there's no real strategic reason given,
     ask rather than invent one.
   - **What** -- 1-2 paragraphs, concise. A reminder for the
     conversation, not a full spec. Link designs/docs if any exist.
   - **Acceptance Criteria** -- 3-5 bullets, observable/testable
     outcomes, not implementation steps.
   - Keep the item independent (deliverable on its own, in any order
     relative to other backlog items) and sized for roughly one sprint
     -- split it into multiple issues if it isn't.
3. Title: short, action-oriented, no ticket-number prefix (GitHub adds
   the number itself).
4. File it with `gh issue create --title "<title>" --body "..."` (see
   `reference.md` for the exact body template and a worked example).
   Add `--label` / `--milestone` / `--assignee` only if asked for, or if
   the repo's existing open issues show a convention worth matching.
5. Report the issue URL back -- don't just say "done".

See `reference.md` for the full body template and a worked example.

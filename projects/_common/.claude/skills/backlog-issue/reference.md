# Issue body template

Always in English, even when the request or conversation was in another
language.

```markdown
## Why
<1-2 sentences: the actual goal or problem this serves. Strategic
context, not restated implementation.>

## What
<1-2 paragraphs. A reminder of what was discussed, not a full spec.
Link designs/docs if any exist. Leave implementation detail for the
work itself.>

## Acceptance Criteria
- <observable/testable outcome>
- <observable/testable outcome>
- <observable/testable outcome>
```

Fill-in rules:

- **Why** -- ties to a real goal or problem. If the request didn't give
  one, ask before inventing one.
- **What** -- concise; a reminder, not a spec. Skip sections that don't
  apply rather than leaving them empty.
- **Acceptance Criteria** -- 3-5 bullets, each an outcome someone could
  verify without reading the code (a behavior, a number, a visible
  state) -- not a checklist of implementation steps.
- Title -- short, action-oriented, no ticket-number prefix (GitHub adds
  the number).

## Worked example

**Title:** Real-time spending tracker

```markdown
## Why
Users need immediate feedback on spending to make conscious budget
decisions -- supports the app's core "reduce overspending" goal.

## What
Add a tracker that updates as expenses are logged, showing current-week
spending against the set budget. Designs: [Figma link]. This is a
reminder of the discussion, not a full spec -- details emerge during
implementation.

## Acceptance Criteria
- Spending totals update within 2s of logging an expense
- Budget progress shown as a progress bar
- Remaining budget visible at a glance
- Multiple expense categories handled correctly
```

## Filing command

```bash
gh issue create --title "<title>" --body "$(cat <<'EOF'
## Why
...

## What
...

## Acceptance Criteria
- ...
EOF
)"
```

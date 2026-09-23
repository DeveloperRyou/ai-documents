---
name: visual-iterate
description: Use after any visual/UI edit in this repo (layout, spacing, color, responsive breakpoints) before handing it back to the user -- drives a self-check loop through `scripts/visual-check.py`, which screenshots light/dark/mobile in its own headless browser and returns only a text report (overflow, low-contrast text, measured boxes/alignment), so images stay out of the main context. Not a substitute for the user's own final look -- it just means their first look already reflects a self-reviewed attempt.
---

# Visual self-check loop

A September 2026 About-page redesign session needed 15+ rounds of
"here's a screenshot, this is wrong" before the result met the user's
bar -- and every screenshot read in that session stayed in context for
every later turn, which is a large part of why it reached 700k tokens.
This loop front-loads the obvious misses onto the agent, **as numbers
and text, not images**.

**REQUIRED:** the dev server on port 4321 (`npm run dev` if it isn't
already -- see this repo's CLAUDE.md for the daemon commands).

## Loop

1. Make the change.
2. Run the check on the affected route -- and its `/ko` and `/ja` twins
   if the change touches markup that's physically duplicated per locale
   (see CLAUDE.md's i18n note):

   ```
   python3 .claude/skills/visual-iterate/scripts/visual-check.py /about \
     --selector "<the element you changed>" \
     --out-dir <scratchpad>/vc<N>
   ```

   Default shots: light desktop, dark desktop, light mobile (390px) --
   dark mode and mobile are where this repo's past regressions lived
   (dark-mode contrast from hand-picked hex values; PRs #22/#23 were
   mobile-breakpoint fixes). Exit 0 = every shot OK, 1 = something to
   look at.
3. Read the report, not the images:
   - `overflow` -- page wider than the viewport, and which element pokes out.
   - `low contrast` -- WCAG ratio with the actual colors, alpha-blended
     over the real background. Fix by picking a token from
     `src/styles/theme.css`, never an eyeballed hex.
   - `--selector` lines -- box, font, colors, padding/gap, and
     `child center-Y spread`: the px difference between the vertical
     centers of the element's children. For a row that should be
     vertically centered (header icons, a label + chip row), anything
     above ~1px is the misalignment.
   For a one-off measurement the script doesn't cover, use
   `browser_evaluate` (`getBoundingClientRect`/`getComputedStyle`) and
   return just the numbers.
4. Fix and re-run until it exits 0, then tell the user it's ready at
   `localhost:4321`. The PNGs are saved in `--out-dir` if the user wants
   to see them -- give them the path rather than reading the image yourself.

## When numbers aren't enough

Some requests are about overall look ("feels cramped", "chip colors
clash") that no measurement captures. In order of preference:

1. `--vision --ask "<what the change should look like>"` adds a local
   vision model's verdict per shot. It's a **hint**: the 9B model has
   flagged phantom misalignments on clean pages, so it never flips a
   shot to CHECK on its own -- corroborate with a measurement.
2. Delegate the look to a subagent (`Agent`, `model: sonnet`): give it
   the PNG paths from `--out-dir` and the user's request, and have it
   return pass/fail plus one line per problem. The images land in its
   context, not yours.
3. Only if both are inconclusive, look at a single shot yourself -- the
   viewport-sized one for the failing theme/width, never full-page
   (`--shot-selector "<el>"` to crop to the element).

## Common Mistakes

- **Taking screenshots with the Playwright MCP tools and reading them
  in the main context.** Each one stays for the rest of the session.
  Use the script; use MCP only for interaction the script can't do
  (clicking a toggle open), and keep it to `browser_evaluate` numbers.
- **`Read`-ing the saved PNGs "just to be sure".** Same cost. Use the
  report, or delegate (see above).
- **`--full-page` by default.** Only when the problem is specifically
  below the fold -- viewport shots are smaller for both you and the
  vision model.
- **Silencing a finding with `--ignore`** that the user hasn't
  accepted. It exists for known, accepted exceptions, not for making a
  red check go green.
- **Looping past 3-4 rounds on the same spot without convergence.** Stop
  and ask the user -- this loop catches obvious misses, it doesn't
  resolve genuine design ambiguity alone.
- **Skipping the locale twins** when the change lives in a
  locale-duplicated page file rather than a shared component.

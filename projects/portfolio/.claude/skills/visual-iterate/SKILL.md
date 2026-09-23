---
name: visual-iterate
description: Use after any visual/UI edit in this repo (layout, spacing, color, responsive breakpoints) before handing it back to the user -- drives a self-check loop (screenshot via the Playwright MCP tools in light+dark theme and a mobile width, compare against the request, fix, re-screenshot) instead of shipping the first attempt and waiting for the user's live 4321 look to catch what's wrong. Not a substitute for the user's own final look -- it just means their first look already reflects a self-reviewed attempt.
---

# Visual self-check loop

A September 2026 About-page redesign session needed 15+ rounds of
"here's a screenshot, this is wrong" before the result met the user's
bar -- every round was the user doing the checking the agent could have
done first. This skill front-loads a couple of those rounds onto the
agent instead.

**REQUIRED:** the dev server running on port 4321 (`npm run dev` if it
isn't already -- see this repo's CLAUDE.md for the daemon-management
commands). Use the Playwright MCP browser tools (`browser_navigate`,
`browser_resize`, `browser_take_screenshot`) to drive it.

## Loop

1. Make the change.
2. Navigate to the affected route on `localhost:4321` -- and its `/ko`
   and `/ja` twins too if the change touches markup that's physically
   duplicated per locale (see CLAUDE.md's i18n note on
   `src/pages/ko`/`src/pages/ja`), since a shared-component fix can look
   right in `en` and still be broken in a locale copy that drifted.
3. Screenshot the default theme, then switch `data-theme` (the site's own
   theme toggle) and screenshot dark mode too. This repo has a documented
   history of dark-mode contrast regressions from hand-picked hex values
   going unreadable against `--background` -- check both themes every
   time, not just the one you happened to build in.
4. Resize to a mobile width and screenshot again -- two of this repo's
   last few merged PRs (#22, #23) were mobile-breakpoint fixes, so mobile
   is a known trouble spot, not a formality. Minimum three shots: light
   desktop, dark desktop, mobile.
5. Compare each screenshot against the actual request -- spacing,
   alignment, contrast -- and against `src/pages/styleguide.astro`'s
   tokens rather than an eyeballed value. If anything's off, fix it and
   go back to step 2.
6. Only once all three pass, tell the user it's ready at `localhost:4321`
   -- attaching the screenshots is optional but means their own check
   starts from something already verified, not from zero.

## Common Mistakes

- **Screenshotting only light/desktop and calling it done.** Dark mode
  and mobile are exactly where this repo's past regressions lived.
- **Reporting "done" without having navigated the live page at all.** A
  diff read is not a visual check -- CSS cascades and responsive
  breakpoints don't show up in source.
- **Looping past 3-4 rounds on the same spot without convergence.** Stop
  and ask the user instead of guessing further -- this loop catches
  obvious misses, it doesn't resolve genuine design ambiguity alone.
- **Skipping the locale twins** when the change lives in a
  locale-duplicated page file rather than a shared component.

# portfolio

@.claude/RULES.md

Personal blog (https://portfolio.developerryou.workers.dev/), migrated from Next.js to Astro
using the AstroPaper theme. Deployed on Cloudflare Workers (static assets, `wrangler.jsonc`).

## Commands

- `npm run dev` -- starts a background daemon (Astro 7); manage it with
  `npx astro dev stop` / `status` / `logs`, not by re-running `dev` and
  expecting it to block in the foreground.
- `npm run build` -- `astro check` (type-check) then `astro build`, then
  builds the pagefind search index and copies it into `public/`.
- `npm run lint` / `npm run format` -- eslint / prettier; `no-console` is
  an eslint error, not a warning.
- No test suite in this repo.
- If you edit `content.config.ts` (collection schema) while `astro dev` is
  already running, the server can go on serving a stale content store even
  after it logs "Synced content" -- a renamed/new frontmatter field
  silently not showing up is this, not a code bug. Fix with
  `npx astro dev stop && rm -rf .astro && npm run dev`.

## Workflow

- After opening a PR (or otherwise finishing a visual/UI change), start
  the dev server (`npm run dev`) on the PR's branch and leave it running
  on port 4321, without waiting to be asked -- the user checks changes
  there before merging. If a server from an earlier branch is already
  running, stop it first (`npx astro dev stop`) so 4321 reflects the
  current branch.
- Drafting, reviewing, or translating a post under `src/content/posts/`
  follows `docs/writing-guide.md` (topics, templates, voice, AI-tell
  checklist, frontmatter, and the ko draft -> review ->
  `/humanize-scan` + `/humanize-korean` -> en/ja translation flow) --
  read it first, every time. One post = one GitHub issue labelled
  `writing`.

## Architecture

- Content lives in `src/content/posts/*.md` and `src/content/pages/*.md`
  (Astro content collections, see `src/content.config.ts`).
- i18n: en (default) / ko / ja, via Astro's built-in i18n routing. Since
  Astro's static i18n does **not** auto-duplicate routes per locale, every
  route under `src/pages/` is physically duplicated under `src/pages/ko/`
  and `src/pages/ja/` -- keep all three in sync when adding a new route.
- Because routes are physically duplicated per locale, any component or
  script that has no locale-specific text belongs in `src/components/`
  (shared across all three locale trees), not copy-pasted into each
  locale's route folder -- e.g. `src/components/post/` holds the post
  detail page's sub-components (`EditPost`, `ShareLinks`,
  `AdjacentPostNav`, `BackButton`, `BackToTopButton`) and
  `ArticleEnhancements` (the scroll-progress/heading-links/code-copy/
  lightbox client script). Only markup that actually differs per locale
  (translated strings, a `getStaticPaths` hardcoded to that locale) should
  live inside a locale-specific page file.
- Locale-suffixed content files use hyphens (`about-ko.md`, not
  `about.ko.md`): Astro's content-collection loader slugs filenames with
  github-slugger, which strips periods, so a dot-suffixed filename would
  collide with the default-locale entry.
- Post slugs go through `src/utils/slugify.ts` + `getPostPaths.ts`, not
  Astro's default: Latin titles use `slugify` (`"E2E Testing"` ->
  `"e2e-testing"`), anything containing non-Latin characters (Korean/
  Japanese titles) uses `lodash.kebabcase` instead, which preserves those
  characters rather than stripping them.
- Config is split in two: `astro-paper.config.ts` is the user-facing
  source of truth (site info, feature flags, socials); `src/config.ts`
  resolves it with defaults into `ResolvedAstroPaperConfig`. Import from
  `@/config` everywhere except the config file itself.
- `ogImage` in post frontmatter must stay a plain string or be omitted --
  `image().or(z.string())` in `content.config.ts` eagerly resolves
  `public/`-relative strings through Astro's image pipeline and throws.
  Use `coverImage` (plain string) for card thumbnails instead.
- The About page (`about*.md` in the `pages` collection) keeps its
  career/education/activities/outsourcing history as structured frontmatter
  arrays (`career`, `education`, `activities`, `outsourcing` -- see the
  `timelineEntry`/`projectCardEntry` schemas in `content.config.ts`), not
  markdown prose -- markdown in the body is only the free-text intro.
  `src/pages/about.astro` (and its `ko`/`ja` copies) render each array
  through a dedicated `src/components/about/` component instead of
  `<Content />`: `Timeline` for career/education (date-column + border-row
  list), `Cards` for plain facts like activities (static, no hover -- it
  goes nowhere on click), `ProjectCards` for outsourcing (thumbnail +
  `link`, the only one styled hoverable/clickable, since a card only earns
  a hover affordance if it actually navigates somewhere). Each section is
  skipped entirely (not rendered with an empty heading) when its array is
  absent or empty, so an in-progress/empty category just doesn't show up.
- Site-wide theme tokens live in `src/styles/theme.css` (`--background`,
  `--accent`, etc., re-exposed to Tailwind v4 via `@theme inline` as
  `--color-*` so e.g. `bg-accent` works) -- most are redefined per
  `[data-theme="light"]`/`[data-theme="dark"]`. Never hand-pick a hex for
  new UI (an earlier chip used arbitrary `amber-900`/`slate-800` and
  became unreadable against the dark theme's background); add a token to
  `theme.css` instead, sourced from a real palette, not eyeballed.
  Base tokens (`--background`, `--foreground`, `--muted*`, `--border*`,
  `--accent*`) are Radix Colors' `slate` (neutrals) and `blue` (accent)
  scales (https://www.radix-ui.com/colors, npm `@radix-ui/colors`), each
  hex annotated with its step in `theme.css` -- light values from the
  light scale, dark values from the dark scale, using Radix's step roles
  (1 background, 3 subtle surface, 6 border, 8 hovered border, 11
  secondary text / text-safe accent, 12 primary text).
  Category/tag-style colors (`--chip-blue`, `--chip-brown` + their
  `-foreground` pair, currently used by the About page's "Company"/
  "Project" `Chip`) come from the light `blue`/`brown` scales, step 11,
  with white text: step 9 ("solid") was tried first but white on it is
  only ~3.3:1, below WCAG AA for small text. White-on-chip contrast
  doesn't depend on the page, so these live under a plain `:root` block
  with no dark override. Pull more colors from the same scales if
  another category color is needed later, rather than picking a new hex
  by eye -- and check white-text contrast before using a lighter step.
  Hover affordances stay neutral: a clickable card steps its border up
  from `--border` to `--border-strong` (Radix Themes' Card "surface"
  recipe) -- no accent-colored border, colored/foreground shadow, or
  lift.
- `src/pages/styleguide.astro` is a living, Storybook-style reference of
  the site's tokens and components (colors, fonts, buttons, chips, cards,
  timeline) -- open it after touching any of those instead of eyeballing
  contrast on a real page. It's a dev tool, not reader content, so on
  purpose it's a single page, not triplicated under `ko`/`ja`, and it's
  linked only from the bottom of `Sidebar.astro` (not the main nav). Keep
  it caption-free: no explanatory prose under a section heading ("Defined
  in X", "src/components/Y.astro", usage notes) -- just the live rendered
  example. A label is only added where it'd otherwise be ambiguous which
  example is which (e.g. the per-font-specimen tags), never to explain
  rationale or point at source files.

# Compact instructions

When compacting, keep: current branch/worktree, open PR and issue
numbers, every design or scope decision the user stated (verbatim where
short), what's done and verified, and the next step. Drop: screenshots
and image descriptions, command/build/log output, file contents and
diffs (re-derivable with git), and superseded attempts.

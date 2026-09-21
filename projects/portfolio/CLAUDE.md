# portfolio

@.claude/RULES.md

Personal blog (developerryou.pages.dev), migrated from Next.js to Astro
using the AstroPaper theme. Deployed on Cloudflare Pages.

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

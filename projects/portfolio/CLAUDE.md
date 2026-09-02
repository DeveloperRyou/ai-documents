# portfolio

Personal blog (developerryou.pages.dev), migrated from Next.js to Astro
using the AstroPaper theme. Deployed on Cloudflare Pages.

- Content lives in `src/content/posts/*.md` and `src/content/pages/*.md`
  (Astro content collections, see `src/content.config.ts`).
- i18n: en (default) / ko / ja, via Astro's built-in i18n routing. Since
  Astro's static i18n does **not** auto-duplicate routes per locale, every
  route under `src/pages/` is physically duplicated under `src/pages/ko/`
  and `src/pages/ja/` -- keep all three in sync when adding a new route.
- Locale-suffixed content files use hyphens (`about-ko.md`, not
  `about.ko.md`): Astro's content-collection loader slugs filenames with
  github-slugger, which strips periods, so a dot-suffixed filename would
  collide with the default-locale entry.
- `ogImage` in post frontmatter must stay a plain string or be omitted --
  `image().or(z.string())` in `content.config.ts` eagerly resolves
  `public/`-relative strings through Astro's image pipeline and throws.
  Use `coverImage` (plain string) for card thumbnails instead.
- `npm run dev` starts a background daemon (Astro 7); manage it with
  `npx astro dev stop` / `status` / `logs`, not by re-running `dev` and
  expecting it to block in the foreground.

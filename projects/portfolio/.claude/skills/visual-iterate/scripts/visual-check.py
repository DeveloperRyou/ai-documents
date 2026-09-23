#!/usr/bin/env python3
"""Screenshot + measure a page in light/dark/mobile and return a TEXT
report, so the images never enter the coordinator's context.

Per shot it collects, with a real headless Chromium (Playwright):
  - horizontal overflow (page wider than the viewport, and which elements)
  - low-contrast text (WCAG ratio < 4.5, < 3 for large text) against the
    element's effective background
  - for each --selector: every match's box, font-size, colors, and --
    across a match's direct children -- the vertical-center spread, which
    is what "icons aren't vertically centered in the header" looks like
    as a number
  - console errors
and, with --vision, asks local-llm's `vision` model for visible defects
against --ask (hints only -- never gates the verdict). Screenshots are saved
under --out-dir for the user (or a subagent) to open if needed.

Stdlib-only Python; Playwright (node) is installed once into
~/.cache/visual-check, reusing the Chromium build already downloaded for
the Playwright MCP server (PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD).

Usage:
  visual-check.py /about --selector header --selector ".timeline li" \
      --ask "chips sit in one column aligned with their labels" \
      --out-dir <scratchpad>/vc1
  visual-check.py /ko/about --shots dark-desktop,light-mobile --vision
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys

PLAYWRIGHT_VERSION = "1.62.1"  # must match a Chromium build in ~/.cache/ms-playwright
TOOL_DIR = pathlib.Path.home() / ".cache" / "visual-check"
HERE = pathlib.Path(__file__).parent
RUN_PY = HERE.parent.parent / "local-llm" / "scripts" / "run.py"

SHOTS = {
    "light-desktop": ("light", 1280, 800),
    "dark-desktop": ("dark", 1280, 800),
    "light-mobile": ("light", 390, 844),
    "dark-mobile": ("dark", 390, 844),
}

NODE_SCRIPT = r"""
const { chromium } = require('playwright');
const cfg = JSON.parse(process.env.VISUAL_CHECK_CFG);

function measure({ selectors, ignore }) {
  const ignored = el => ignore.some(sel => el.closest(sel));
  // Computed colors can be oklab()/color-mix() etc., so let a canvas
  // normalize any CSS color to sRGB rgba instead of regex-parsing it.
  const cv = document.createElement('canvas').getContext('2d', { willReadFrequently: true });
  const rgba = c => { cv.clearRect(0, 0, 1, 1); cv.fillStyle = '#000'; cv.fillStyle = c; cv.fillRect(0, 0, 1, 1);
    const d = cv.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3] / 255]; };
  const over = (fg, bg) => fg.slice(0, 3).map((v, i) => v * fg[3] + bg[i] * (1 - fg[3]));
  const lum = ([r, g, b]) => {
    const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m); return (x + 0.05) / (y + 0.05); };
  const bgOf = el => {
    for (let e = el; e; e = e.parentElement) {
      const c = rgba(getComputedStyle(e).backgroundColor);
      if (c[3] > 0.9) return c.slice(0, 3);
    }
    return [255, 255, 255];
  };
  const visible = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0.1; };
  const label = el => (el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') +
    (typeof el.className === 'string' && el.className.trim() ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : ''));

  const vw = window.innerWidth;
  const overflow = [];
  if (document.documentElement.scrollWidth > vw + 1) {
    for (const el of document.querySelectorAll('body *')) {
      if (!visible(el) || ignored(el)) continue;
      const r = el.getBoundingClientRect();
      if (r.right > vw + 1 && !(el.parentElement && el.parentElement.getBoundingClientRect().right > vw + 1)) {
        overflow.push({ el: label(el), right: Math.round(r.right) });
        if (overflow.length >= 5) break;
      }
    }
  }

  const lowContrast = [], seen = new Map();
  for (const el of document.querySelectorAll('body *')) {
    const own = [...el.childNodes].filter(n => n.nodeType === 3 && n.textContent.trim()).map(n => n.textContent.trim()).join(' ');
    if (!own || !visible(el) || ignored(el)) continue;
    const s = getComputedStyle(el);
    const bg = bgOf(el);
    const fg = over(rgba(s.color), bg);
    const size = parseFloat(s.fontSize), bold = +s.fontWeight >= 700;
    const need = size >= 24 || (size >= 18.66 && bold) ? 3 : 4.5;
    const r = ratio(fg, bg);
    if (r >= need) continue;
    const key = `${label(el)}|${s.color}|${bg}`;
    if (seen.has(key)) { seen.get(key).count++; continue; }
    const hit = { el: label(el), text: own.slice(0, 40), ratio: +r.toFixed(2), need, count: 1,
      fg: `rgb(${fg.map(Math.round).join(', ')})`, bg: `rgb(${bg.join(', ')})` };
    seen.set(key, hit); lowContrast.push(hit);
    if (lowContrast.length >= 8) break;
  }

  const selected = {};
  for (const sel of selectors) {
    const out = [];
    for (const el of [...document.querySelectorAll(sel)].slice(0, 8)) {
      const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
      const kids = [...el.children].filter(visible);
      const centers = kids.map(k => { const kr = k.getBoundingClientRect(); return kr.top + kr.height / 2; });
      out.push({
        visible: visible(el),
        box: [r.x, r.y, r.width, r.height].map(Math.round),
        font: s.fontSize, color: s.color, bg: s.backgroundColor, padding: s.padding, gap: s.gap,
        children: kids.length,
        childCenterYSpread: centers.length > 1 ? +(Math.max(...centers) - Math.min(...centers)).toFixed(1) : null,
      });
    }
    selected[sel] = out.length ? out : 'NO MATCH';
  }
  return { scrollWidth: document.documentElement.scrollWidth, viewport: vw, overflow, lowContrast, selected };
}

(async () => {
  const browser = await chromium.launch();
  const results = [];
  for (const shot of cfg.shots) {
    const ctx = await browser.newContext({ viewport: { width: shot.width, height: shot.height }, colorScheme: shot.theme });
    await ctx.addInitScript(t => { try { localStorage.setItem('theme', t); } catch (e) {} }, shot.theme);
    const page = await ctx.newPage();
    // Astro's dev toolbar floats over the bottom of every page in `astro dev`.
    await ctx.addInitScript(() => document.addEventListener('DOMContentLoaded', () => {
      const st = document.createElement('style'); st.textContent = 'astro-dev-toolbar{display:none!important}';
      document.head.appendChild(st);
    }));
    const errors = [];
    page.on('console', m => { if (m.type() === 'error') errors.push(m.text().slice(0, 200)); });
    page.on('pageerror', e => errors.push(String(e).slice(0, 200)));
    try {
      await page.goto(cfg.url, { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(300);
      const m = await page.evaluate(measure, { selectors: cfg.selectors, ignore: cfg.ignore });
      const file = `${cfg.outDir}/${shot.name}.png`;
      const target = cfg.shotSelector ? page.locator(cfg.shotSelector).first() : page;
      await target.screenshot({ path: file, ...(cfg.shotSelector ? {} : { fullPage: cfg.fullPage }) });
      results.push({ shot: shot.name, file, consoleErrors: errors.slice(0, 5), ...m });
    } catch (e) {
      results.push({ shot: shot.name, error: String(e).slice(0, 300) });
    }
    await ctx.close();
  }
  await browser.close();
  console.log(JSON.stringify(results));
})();
"""

VISION_PROMPT = """You are checking one screenshot of a web page ({shot}) for visible defects.
The developer's intent for this change: {ask}
Report only concrete, visible problems: overlapping or clipped text, elements misaligned with their
neighbours, unreadable text/background contrast, content spilling past the edge, broken or collapsed
layout, or anything that contradicts the intent above. Do not comment on taste or suggest redesigns.
If nothing is wrong, reply with exactly: OK
Otherwise reply with at most 4 short bullet lines, each naming where on the page the problem is."""


def ensure_playwright():
    if (TOOL_DIR / "node_modules" / "playwright").is_dir():
        return
    TOOL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"installing playwright@{PLAYWRIGHT_VERSION} into {TOOL_DIR} (one-time)...", file=sys.stderr)
    subprocess.run(["npm", "install", "--silent", "--no-audit", "--no-fund", f"playwright@{PLAYWRIGHT_VERSION}"],
                   cwd=TOOL_DIR, check=True, env={**os.environ, "PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD": "1"})


def vision_verdict(shot, image, ask):
    prompt = VISION_PROMPT.format(shot=shot, ask=ask or "(none given -- just look for defects)")
    proc = subprocess.run([sys.executable, str(RUN_PY), "call", "--model", "vision", "--images", image,
                           "--user-text", prompt], capture_output=True, text=True, timeout=180)
    if proc.returncode != 0:
        return f"(vision check failed: {proc.stderr.strip()[-200:]})"
    return proc.stdout.strip()


def main():
    ap = argparse.ArgumentParser(description="Text-only visual check of a page in several themes/viewports")
    ap.add_argument("path", help="route like /about, or a full URL")
    ap.add_argument("--base", default="http://localhost:4321")
    ap.add_argument("--shots", default="light-desktop,dark-desktop,light-mobile",
                    help=f"comma-separated, from: {', '.join(SHOTS)}")
    ap.add_argument("--selector", action="append", default=[], help="CSS selector to measure (repeatable)")
    ap.add_argument("--ignore", action="append", default=[],
                    help="CSS selector exempt from contrast/overflow checks -- only for a finding the user already accepted")
    ap.add_argument("--shot-selector", help="screenshot only this element instead of the viewport")
    ap.add_argument("--full-page", action="store_true", help="full-page screenshot (larger; viewport by default)")
    ap.add_argument("--ask", help="what the change is supposed to look like; given to the vision model")
    ap.add_argument("--vision", action="store_true",
                    help="also ask the local vision model for visible defects (noisy hints, see SKILL.md)")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    ensure_playwright()
    out_dir = pathlib.Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    url = args.path if args.path.startswith("http") else args.base.rstrip("/") + "/" + args.path.lstrip("/")
    shots = []
    for name in args.shots.split(","):
        theme, w, h = SHOTS[name.strip()]
        shots.append({"name": name.strip(), "theme": theme, "width": w, "height": h})
    cfg = {"url": url, "shots": shots, "selectors": args.selector, "ignore": args.ignore, "shotSelector": args.shot_selector,
           "fullPage": args.full_page, "outDir": str(out_dir)}

    proc = subprocess.run(["node", "-e", NODE_SCRIPT], capture_output=True, text=True, timeout=300,
                          env={**os.environ, "NODE_PATH": str(TOOL_DIR / "node_modules"),
                               "VISUAL_CHECK_CFG": json.dumps(cfg)})
    if proc.returncode != 0:
        sys.exit(f"browser run failed:\n{proc.stderr.strip()[-1500:]}")
    results = json.loads(proc.stdout.strip().splitlines()[-1])

    flagged = 0
    print(f"visual-check {url}")
    for r in results:
        if "error" in r:
            flagged += 1
            print(f"\n[{r['shot']}] ERROR {r['error']}")
            continue
        if args.vision:
            r["vision"] = vision_verdict(r["shot"], r["file"], args.ask)
        # Vision output is a hint, not a gate -- a 9B model flags phantom
        # misalignments on clean pages, so it never turns a shot into CHECK.
        issues = bool(r["overflow"] or r["lowContrast"] or r["consoleErrors"])
        flagged += issues
        print(f"\n[{r['shot']}] {'CHECK' if issues else 'OK'}  ({r['file']})")
        if r["overflow"]:
            print(f"  overflow: page {r['scrollWidth']}px > viewport {r['viewport']}px; "
                  + ", ".join(f"{o['el']}→{o['right']}px" for o in r["overflow"]))
        for c in r["lowContrast"]:
            print(f"  low contrast {c['ratio']} (<{c['need']}): {c['el']} \"{c['text']}\" {c['fg']} on {c['bg']}"
                  + (f" (x{c['count']})" if c["count"] > 1 else ""))
        for e in r["consoleErrors"]:
            print(f"  console error: {e}")
        for sel, items in r["selected"].items():
            if items == "NO MATCH":
                print(f"  {sel}: NO MATCH")
                continue
            for i, it in enumerate(items):
                spread = f", child center-Y spread {it['childCenterYSpread']}px" if it["childCenterYSpread"] is not None else ""
                print(f"  {sel}[{i}]: box {it['box']}{'' if it['visible'] else ' (hidden)'}, font {it['font']}, "
                      f"color {it['color']}, bg {it['bg']}, padding {it['padding']}, gap {it['gap']}{spread}")
        if r.get("vision"):
            print("  vision (unverified hint): " + r["vision"].replace("\n", "\n    "))

    (out_dir / "report.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(results) - flagged}/{len(results)} shots OK -- full report: {out_dir / 'report.json'}")
    sys.exit(1 if flagged else 0)


if __name__ == "__main__":
    main()

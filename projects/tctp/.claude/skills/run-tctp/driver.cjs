// TCTP 브라우저 드라이버 — run.sh 가 NODE_PATH 를 맞춰 부른다. 직접 부르지 말 것.
// 쓰임: run.sh drill <id> [--sec N|--end] [--seed N]
//       run.sh game <scenario> [--sec N] [--seed N] [--view 2d|iso|3d|split] [--truth]
//       run.sh menu
// 결과: 표준출력에 HUD·판정·콘솔 오류, 스크린샷은 $SHOTS (기본 /tmp/tctp-shots) 에.
const { chromium } = require("playwright");
const fs = require("node:fs");
const path = require("node:path");

const BASE = process.env.TCTP_URL ?? "http://localhost:5175";
const SHOTS = process.env.SHOTS ?? "/tmp/tctp-shots";
const TICKS_PER_SEC = 4; // 1틱 = 0.25초 (core/time.ts)

const errors = [];
const [mode, target, ...rest] = process.argv.slice(2);
const opt = (name) => {
  const i = rest.indexOf(`--${name}`);
  return i < 0 ? undefined : (rest[i + 1] ?? true);
};

async function main() {
  fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  page.on("pageerror", (e) => errors.push(String(e)));

  let shot;
  if (mode === "drill") {
    const q = new URLSearchParams({ debug: "drills", drill: target });
    if (opt("seed")) q.set("seed", opt("seed"));
    await page.goto(`${BASE}/?${q}`);
    await page.waitForSelector(".lab-hud", { state: "attached", timeout: 15000 });
    await page.waitForFunction(() => /틱/.test(document.querySelector(".lab-hud")?.textContent ?? ""));
    // 드릴 길이(초)는 HUD "0.00s / 30s · 틱 0 ..." 에서 읽는다
    const hud0 = await page.textContent(".lab-hud");
    const total = Number(/\/ ([\d.]+)s/.exec(hud0)[1]);
    const sec = opt("end") ? total : Number(opt("sec") ?? total);
    // 일시정지 상태에서 → 키 = 1틱. page.keyboard.press 는 한 번에 한 프레임을 기다려 120틱에도 몇 분 걸린다 —
    // window 에 keydown 을 직접 n 번 쏘면 한 번에 끝난다
    const ticks = Math.round(sec * TICKS_PER_SEC);
    await page.evaluate((n) => {
      for (let i = 0; i < n; i++) dispatchEvent(new KeyboardEvent("keydown", { code: "ArrowRight" }));
    }, ticks);
    await page.waitForTimeout(500); // 다음 프레임에 HUD·판정이 다시 그려진다
    console.log("HUD:", await page.textContent(".lab-hud"));
    const checks = await page.$$eval(".lab-checks li", (lis) =>
      lis.map((li) => `${li.className || "pending"}\t${li.querySelector(".lab-check-body span")?.textContent}\t${li.querySelector(".lab-live")?.textContent}`),
    );
    console.log(`checks (${checks.length}):\n${checks.join("\n")}`);
    shot = path.join(SHOTS, `drill-${target}-${sec}s.png`);
  } else if (mode === "game") {
    const q = new URLSearchParams({ scenario: target });
    for (const k of ["seed", "view"]) if (opt(k)) q.set(k, opt(k));
    if (opt("truth")) q.set("truth", "1");
    await page.goto(`${BASE}/?${q}`);
    await page.waitForSelector("#hud");
    // 게임은 실시간 루프 — 그냥 기다린다
    await page.waitForTimeout(Number(opt("sec") ?? 3) * 1000);
    console.log("HUD:", (await page.textContent("#hud"))?.replace(/\s+/g, " ").slice(0, 400));
    shot = path.join(SHOTS, `game-${target}.png`);
  } else if (mode === "menu") {
    await page.goto(`${BASE}/`);
    await page.waitForSelector("#menu:not([hidden])");
    console.log("menu:", (await page.textContent("#menu"))?.replace(/\s+/g, " ").slice(0, 400));
    shot = path.join(SHOTS, "menu.png");
  } else {
    console.error("usage: run.sh drill <id> [--sec N|--end] [--seed N] | game <scenario> [--sec N] [--seed N] [--view v] [--truth] | menu");
    process.exit(2);
  }
  await page.screenshot({ path: shot });
  console.log("screenshot:", shot);
  console.log(errors.length ? `console errors:\n${errors.join("\n")}` : "console errors: none");
  await browser.close();
  process.exit(errors.length ? 1 : 0);
}

main().catch((e) => {
  console.error(String(e).split("\n")[0]);
  // 확인장이 안 뜨면 대개 모듈 오류다 (다른 세션이 고치던 중 등) — 페이지 오류를 같이 보여 준다
  if (errors.length) console.error(`page errors:\n${errors.join("\n")}`);
  process.exit(1);
});

// 드릴을 시드·시각별로 돌려 병사 상태·시야·발견 확률을 덤프한다 (화면 없이, 실제 장비 데이터).
// 레포 루트에서: node --preserve-symlinks --import tsx .claude/skills/sim-probe/probe.ts <drill> [옵션]
//   --seed N          드릴 시드 대신
//   --at 5,12,12.25   이 시각(초)들에 덤프 (기본: 끝)
//   --every S         S 초마다 덤프 (--at 대신)
//   --ids 0,1         이 병사만 (기본: 전원)
//   --pair 0:1        관측자:대상 시야·발견 요인 (여러 번 가능)
//   --log             덤프 사이에 쌓인 w.log 를 함께
//   --json            사람이 읽는 줄 대신 JSON
import { DRILLS, DrillRun, detectFactors, secToTicks, type Soldier, type World, visibility } from "@tctp/sim";
import { loadDb } from "../../../packages/tools/src/content";

const args = process.argv.slice(2);
const id = args[0];
const opt = (name: string) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 ? args[i + 1] : undefined;
};
const all = (name: string) => args.flatMap((a, i) => (a === `--${name}` ? [args[i + 1]!] : []));

const drill = DRILLS.find((d) => d.id === id);
if (!drill) {
  console.error(`드릴 없음: ${id}\n있는 드릴: ${DRILLS.map((d) => d.id).join(" ")}`);
  process.exit(2);
}
const db = loadDb();
const run = new DrillRun(drill, db.equipment, opt("seed") === undefined ? drill.seed : Number(opt("seed")));
const every = opt("every");
const times = every
  ? Array.from({ length: Math.floor(drill.sec / Number(every)) }, (_, k) => (k + 1) * Number(every))
  : (opt("at")?.split(",").map(Number) ?? [drill.sec]);
const ids = opt("ids")?.split(",").map(Number);
const pairs = all("pair").map((p) => p.split(":").map(Number) as [number, number]);
const json = args.includes("--json");
const showLog = args.includes("--log");

const deg = (r: number) => Math.round((r * 180) / Math.PI);
const f = (n: number, d = 1) => n.toFixed(d);

function soldierRow(s: Soldier) {
  return {
    id: s.id,
    side: s.side,
    xy: `${f(s.x)},${f(s.y)}`,
    posture: s.posture,
    status: s.status,
    action: s.action?.kind ?? "-",
    stress: f(s.stress),
    stressLevel: s.stressLevel,
    stamina: f(s.stamina),
    winded: f(s.winded),
    blood: f(s.blood),
    facing: deg(s.facing),
    look: deg(s.look),
    wounds: s.wounds.map((wd) => `${wd.part}:${wd.severity}`).join(" ") || "-",
    loaded: s.loaded.primary,
  };
}

function pairRow(w: World, a: number, b: number) {
  const o = w.soldiers[a]!;
  const t = w.soldiers[b]!;
  const fac = detectFactors(w, o, t);
  const known = w.contacts[o.side].find((c) => c.id === b);
  return {
    pair: `${a}→${b}`,
    visibility: f(visibility(w, o, t), 3),
    ...Object.fromEntries(Object.entries(fac).map(([k, v]) => [k, typeof v === "number" ? Number(v.toFixed(4)) : v])),
    known: known ? (known.visible ? "보임" : "놓침") : "모름",
  };
}

let logFrom = 0;
const out: unknown[] = [];
for (const sec of times) {
  const tick = secToTicks(sec);
  while (run.w.tick < tick && !run.done) run.step();
  const w = run.w;
  const soldiers = w.soldiers.filter((s) => !ids || ids.includes(s.id)).map(soldierRow);
  const prs = pairs.map(([a, b]) => pairRow(w, a, b));
  const log = showLog ? w.log.slice(logFrom).map((l) => `${f(l.tick / 4, 2)}s ${l.side ?? ""} ${l.text}`) : [];
  logFrom = w.log.length;
  if (json) out.push({ sec: w.tick / 4, tick: w.tick, soldiers, pairs: prs, log });
  else {
    console.log(`── ${f(w.tick / 4, 2)}s (틱 ${w.tick}) · ${drill.id} · 시드 ${run.seed}`);
    if (soldiers[0]) console.log("  ", Object.keys(soldiers[0]).join(" | "));
    for (const s of soldiers) console.log("  ", Object.values(s).join(" | "));
    for (const p of prs) console.log("  ", Object.entries(p).map(([k, v]) => `${k}=${v}`).join(" "));
    for (const l of log) console.log("   log", l);
  }
}
run.runToEnd();
const checks = drill.checks.map((c, i) => `${run.results[i] ? "✓" : "✗"} ${c.label}`);
if (json) console.log(JSON.stringify({ drill: drill.id, seed: run.seed, dumps: out, checks }, null, 1));
else console.log(`── 판정 (끝까지)\n   ${checks.join("\n   ")}`);

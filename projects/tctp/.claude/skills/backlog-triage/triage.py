#!/usr/bin/env python3
"""TCTP 백로그 한눈에: 열린 이슈를 design 상태 → priority → size 순으로 묶고, 손볼 것을 따로 뽑는다.
레포 루트에서: python3 .claude/skills/backlog-triage/triage.py [--area perception] [--ready]
  --area X   area:X 만
  --ready    design:ready 만 (바로 착수 가능)
"""
import json, re, subprocess, sys

args = sys.argv[1:]
area = args[args.index("--area") + 1] if "--area" in args else None
only_ready = "--ready" in args

def gh(*a):
    return json.loads(subprocess.check_output(["gh", *a], text=True))

issues = gh("issue", "list", "--state", "open", "-L", "300", "--json", "number,title,labels,body")
closed = {i["number"] for i in gh("issue", "list", "--state", "closed", "-L", "500", "--json", "number")}
log = subprocess.check_output(["git", "log", "--format=%h %s", "-n", "400"], text=True)
closes = {}
for line in log.splitlines():
    for n in re.findall(r"closes #(\d+)", line, re.I):
        closes.setdefault(int(n), line.split()[0])

def lab(i, prefix):
    return [l["name"].split(":", 1)[1] for l in i["labels"] if l["name"].startswith(prefix + ":")]

DESIGN = ["ready", "needs-decision", "needs-research", "blocked", "?"]
PRIO = {"high": 0, "medium": 1, "low": 2}
SIZE = {"S": 0, "M": 1, "L": 2, "XL": 3}

rows, fix = [], []
for i in issues:
    n = i["number"]
    d = (lab(i, "design") or ["?"])[0]
    p = (lab(i, "priority") or ["?"])[0]
    s = (lab(i, "size") or ["?"])[0]
    t = (lab(i, "type") or ["?"])[0]
    a = lab(i, "area")
    missing = [k for k, v in (("type", t), ("area", a), ("design", d), ("size", s), ("priority", p)) if v in ("?", [])]
    if missing:
        fix.append(f"#{n} 라벨 없음: {', '.join(missing)} — {i['title']}")
    if n in closes:
        fix.append(f"#{n} 커밋 {closes[n]} 에 closes 가 있는데 열려 있음 (push 전이거나 닫기 누락) — {i['title']}")
    if d == "blocked":
        refs = [int(x) for x in re.findall(r"#(\d+)", i["body"] or "") if int(x) != n]
        done = [r for r in refs if r in closed]
        if refs and len(done) == len(refs):
            fix.append(f"#{n} blocked 인데 본문이 가리키는 #{', #'.join(map(str, refs))} 가 모두 닫힘 → ready 후보")
    if area and area not in a:
        continue
    if only_ready and d != "ready":
        continue
    rows.append((DESIGN.index(d) if d in DESIGN else 9, PRIO.get(p, 3), SIZE.get(s, 4), n, d, p, s, t, "/".join(a) or "?", i["title"]))

rows.sort()
cur = None
for _, _, _, n, d, p, s, t, a, title in rows:
    if d != cur:
        cur = d
        print(f"\n## design:{d}")
    print(f"#{n:<4} {p:<6} {s:<2} {t:<8} {a:<22} {title}")
print(f"\n열린 이슈 {len(issues)}개 (표시 {len(rows)})")
if fix:
    print("\n## 손볼 것")
    print("\n".join(fix))

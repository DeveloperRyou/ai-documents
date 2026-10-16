---
name: run-tctp
description: Run, start, launch, screenshot, or visually check TCTP in a browser -- replay a drill in the 행동 확인장 (`?debug=drills&drill=<id>`) to a given second and read its checks, open a scenario in the game view, or capture the menu. Use for "확인장 확인", "드릴 재생해서 화면 봐", "게임 띄워서 스크린샷", or confirming a sim change on screen (not just tests).
---

TCTP는 Vite 웹앱입니다. 에이전트는 `.claude/skills/run-tctp/run.sh` 하나로 띄우고 조작합니다. 이 스크립트가 dev 서버(5175)를 필요할 때만 띄우고, headless Chromium(playwright)으로 페이지를 열어 HUD·판정·콘솔 오류를 출력하고 스크린샷을 남깁니다.
경로는 모두 레포 루트(`tctp/`) 기준입니다.

## Prerequisites

Node ≥ 22, `npm install` 완료. playwright는 프로젝트 의존성이 아닙니다. `run.sh`가 처음 실행될 때 `~/.cache/tctp-run`에 `playwright@1.62.1`을 설치하고, 브라우저가 없으면 `playwright install chromium`도 합니다. 따로 할 일은 없습니다.

## Run (agent path)

```bash
# 드릴: 지정 초까지(또는 --end 로 끝까지) 틱을 진행 → HUD, 확인 항목 판정, 스크린샷
.claude/skills/run-tctp/run.sh drill move --end
.claude/skills/run-tctp/run.sh drill move --sec 10 --seed 3

# 게임: 시나리오를 열고 실시간으로 N초 기다린 뒤 HUD와 스크린샷
.claude/skills/run-tctp/run.sh game bd1-react-to-contact --sec 3 --seed 7   # --view 2d|iso|3d|split, --truth

# 메뉴
.claude/skills/run-tctp/run.sh menu
```

출력 예 (드릴):

```
HUD: 40.00s / 40s · 틱 160 · 시드 1 · ×1
checks (2):
pass	이동 중 상태 = moving	False      ← 판정(pass/fail/pending) · 항목 · 지금 틱의 값
pass	도착 후 행동 비움·정지	True
screenshot: /tmp/tctp-shots/drill-move-40s.png
console errors: none
```

- 스크린샷은 `/tmp/tctp-shots/`에 저장됩니다(`SHOTS=`로 바꿀 수 있음). 콘솔 오류가 있으면 종료 코드가 1입니다.
- 스크린샷은 메인 컨텍스트에서 `Read`하지 않습니다. 화면 판정은 로컬 비전 모델로 합니다:
  `python3 .claude/skills/local-llm/scripts/run.py call --model vision --images /tmp/tctp-shots/<파일>.png --user-text "<볼 것>"`
- 드릴 id 목록: `grep -o 'id: "[^"]*"' packages/sim/src/drills/drills.ts`
- dev 서버 로그(스크립트가 띄웠을 때): `/tmp/tctp-dev.log`. 서버 끄기: `lsof -ti:5175 -sTCP:LISTEN | xargs -r kill`

## Run (human path)

```bash
npm run dev   # → http://localhost:5175 (?debug=drills, ?scenario=...). Ctrl-C 로 끈다
```

## Test

```bash
npm run check   # typecheck + Biome + Vitest (드릴 e2e 포함). 185 tests 통과 확인
```

## Gotchas

- **없는 드릴 id는 조용히 첫 드릴(`move`)로 바뀝니다.** 오류가 나지 않으니, 출력의 확인 항목이 기대한 드릴의 것인지 꼭 봅니다.
- **`page.keyboard.press("ArrowRight")`를 반복하면 너무 느립니다.** 한 번 누를 때마다 프레임을 기다려서 160틱에 몇 분이 걸립니다. 드라이버는 `window`에 `keydown`(code `ArrowRight`)을 직접 n번 쏴서 1초 안에 끝냅니다. 확인장은 일시정지 상태로 열리고, → 한 번이 1틱(0.25초)입니다.
- **`.lab-hud`는 `visible` 대기로 잡히지 않습니다.** `state: "attached"`로 기다린 뒤 HUD 글에 "틱"이 나올 때까지 기다립니다.
- **게임 화면은 실시간 루프입니다.** 틱을 빨리 감을 방법이 없어서 `--sec`만큼 실제로 기다립니다.
- **다른 세션이 같은 작업 트리를 고치는 중이면 Vite 모듈이 깨질 수 있습니다.** 예: `does not provide an export named 'heard'`. 이때 확인장은 빈 화면이고 `.lab-hud` 대기가 시간 초과됩니다. 드라이버가 page errors를 같이 출력하니, 코드 탓인지 고치던 중인 탓인지 가려서 잠시 뒤 다시 돌립니다.
- **dev 서버를 `pkill -f <패턴>`으로 끄지 않습니다.** 패턴이 에이전트 자신의 셸 명령줄에도 걸려서 그 셸이 같이 죽습니다(exit 144). 포트로 끕니다(위 명령).

## Troubleshooting

- **`page.waitForSelector: Timeout ... waiting for locator('.lab-hud')`**: 페이지 모듈 오류입니다. 함께 찍힌 `page errors:`를 봅니다. 위 "다른 세션" 항목과 같은 경우가 대부분입니다.

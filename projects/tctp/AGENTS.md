# AGENTS.md — TCTP (Tactical Command Training Program, 실 개발)

분대 단위 직접 지휘 전술 시뮬. 첫 제품 = **분대**. 소대 지휘는 이후 단계.
설계는 `docs/DESIGN.md`, 현재 코드 구조는 `docs/ARCHITECTURE.md`, 객체 정의는 `docs/objects/`, 수치 계산 식·난수는 `docs/calc/`.
`poc/` 는 종료된 POC 보관소다. **import 하지 말 것** — 필요하면 옮겨 와서 다듬는다 (기록은 `docs/POC.md`).

## 명령어
```bash
npm run dev          # 클라이언트 http://localhost:5175 — 메뉴. 게임 직행 ?scenario=bd1-react-to-contact (&seed=7 &view=2d|iso|3d|split &truth=1)
                     # 행동 확인장 ?debug=drills (&drill=<id>) — sim/src/drills.ts 의 드릴을 틱 단위로 재생
npm run check        # typecheck + lint(Biome) + test(Vitest). 커밋 전 통과시킬 것
npm run format       # Biome 자동 수정
npm run build        # 클라이언트 빌드 (CI 는 check + build)
npx vitest run packages/sim/src/world.test.ts   # 테스트 파일 하나 (-t "<이름>" 으로 골라 돌리기)
npm run headless -- 1 --n 10 --sec 120 [--scenario id]
npm run fetch-map -- <id> <남> <서> <북> <동> [이름]   # content/maps/<id>.json (--from-cache, --no-elev)
```

## 구조
- npm workspaces. 패키지끼리는 `@tctp/sim`, `@tctp/sim/<파일>` 로 가져온다 (소스 TS 를 그대로 씀, 빌드 단계 없음).
- `packages/sim`: tsconfig 에 DOM·node 타입이 없다. 시뮬에서 `window`, `document`, `fs`, `performance` 등을 쓰면 타입 오류가 나는 게 정상.
- `packages/client`: 입력 → `Command` → `Session`(sim, 고정 틱 루프) → `Snapshot` → `Renderer` 구현이 그린다. 렌더러는 `World` 를 보지 않는다 (교체 방법은 `docs/ARCHITECTURE.md` "프런트엔드 경계").
- `packages/render3d`: Three.js 3D 렌더러 POC (`?view=3d`). 지도에 층수·지붕 정보가 없어 건물 높이는 바닥 면적으로 어림한다.
- `packages/tools`: Node 전용 도구. `content/` 를 읽고 쓴다.
- `content/maps/raw/` 는 OSM·고도 원본 캐시 (git 제외).
- 틱 흐름: 상태는 `step(world, cmds)`(`sim/src/world.ts`) 안에서만 바뀌고, 명령은 `applyCommand`(`command.ts`)로 들어가 병사 행동(`Action`, `action.ts`)이 되고, 행동이 매 틱 진행된다 (구조: `docs/objects/action.md`). 클라이언트는 틱마다 낸 명령을 `commandLog` 에 쌓은 뒤 `step` 을 부른다. 테스트·headless 는 `runReplay` + `stateHash`(`replay.ts`)로 결정성을 비교한다.
- 콘텐츠: `content/campaign.json`(과정 사다리) → `scenarios/*.json` → `orgs/*.json`(편제) → `equipment.json`(화기·탄약). 병사는 `buildSoldiers`(`scenario.ts`)로 편제에서 세운다. 지도는 `rasdorf.json` 하나.
- 정보 안개: `World.contacts`(진영별 아는 적, `vision.ts`) → `snapshot` 이 거른다. 렌더러에 실제 적 위치를 넘기지 말 것 (`?truth=1` 디버그만).
- `CLAUDE.md`, `AGENTS.md`, `docs/`, `.claude/` 는 ai-documents 레포(`projects/tctp/`)를 가리키는 심볼릭 링크다. 수정은 링크를 따라가 그쪽 레포에서 커밋·푸시한다.

## 원칙
- **결정성**: 시드 RNG(`rng.ts`)만 쓴다 (`Math.random()` 금지). 시간은 정수 `tick` (1틱 = 0.25초, `time.ts`. 튜닝 수치는 초 단위로 적고 `secToTicks` 로 바꾼다). 같은 지도·시드·명령 기록 → 같은 `stateHash`.
- **명령은 데이터**: 플레이어·AI 모두 `Command` 를 내고, 시뮬은 틱 시작 때 적용한다. 리플레이·사후검토·버그 재현은 명령 기록(`TimedCommand[]`)으로 한다.
- **같은 사람 객체**: 아군·적 모두 `Soldier`. 진영과 장비만 다르다. 적 AI 도 플레이어와 같은 `Command` 만 쓴다.
- **실제 지도, 연속 좌표**: 헥스 없음. 미터 좌표 (x 동쪽, y 남쪽, 원점 북서). 사람 = 지름 1m 실척.
- **최소 명령 단위 = 분대** (분할하면 조). 개인 선택은 정보 확인용.
- **정보 안개**: 클라이언트는 아군이 아는 적만 그린다 (실제 위치는 디버그 표시로만).
- **튜닝 수치는 이름 붙은 상수**로 (`MOVE` 처럼). 매직 넘버 금지.
- 개인 수치는 상태값 + **장비·자원** 위주. 능력치·신상·특성 확장은 하지 않는다 (사용자 결정).
- 지도 출처 표기 필수 (OSM ODbL, 고도, 위성).

## 작업 방식
- 사용자가 요청한 범위만 바꾼다. 특히 요청 밖 UI 변경 금지 — 제안만 한다.
- 시뮬 규칙을 바꾸면 테스트를 추가하고, 밸런스에 영향이 있으면 headless 로 전후를 비교해 보고한다.
- 개인 개발이다. 브랜치·PR 없이 작업 단위가 끝나면 (`npm run check` 통과 후) `main` 에 바로 커밋한다.
- 코드를 커밋할 때마다 `docs/`(객체 필드를 바꾸면 `docs/objects/`, 튜닝 상수·식·난수 굴림을 바꾸면 `docs/calc/` 도)·`AGENTS.md`·`README.md` 를 최신화해야 하는지 판단하고, 필요하면 같은 작업에서 고친다 (`docs/`·`AGENTS.md` 는 ai-documents 쪽에 커밋).

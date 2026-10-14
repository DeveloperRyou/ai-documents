# AGENTS.md — TCTP (Tactical Command Training Program, 실 개발)

분대 단위 직접 지휘 전술 시뮬. 첫 제품 = **분대**. 소대 지휘는 이후 단계 (POC 에서 구현할 것이 더 많다고 판단).
POC 는 `poc/` 에 보관만 한다. **POC 코드를 import 하지 말 것** — 필요한 것은 옮겨 와서 다듬는다 (설계 근거는 `docs/DESIGN.md`).

## 명령어
```bash
npm run dev          # 클라이언트 http://localhost:5175 (?seed=7)
npm run check        # typecheck + lint(Biome) + test(Vitest). 커밋 전 통과시킬 것
npm run format       # Biome 자동 수정
npm run build        # 클라이언트 빌드 (CI 는 check + build)
npx vitest run packages/sim/src/world.test.ts   # 테스트 파일 하나 (-t "<이름>" 으로 골라 돌리기)
npm run headless -- 1 --n 10 --sec 120
npm run fetch-map -- <id> <남> <서> <북> <동> [이름]   # content/maps/<id>.json (--from-cache, --no-elev)
```

## 구조
- npm workspaces. 패키지끼리는 `@tctp/sim`, `@tctp/sim/<파일>` 로 가져온다 (소스 TS 를 그대로 씀, 빌드 단계 없음).
- `packages/sim`: tsconfig 에 DOM·node 타입이 없다. 시뮬에서 `window`, `document`, `fs`, `performance` 등을 쓰면 타입 오류가 나는 게 정상.
- `packages/client`: 입력 → `Command` → 고정 틱 루프 → 그리기. 그리기는 상태를 읽기만 한다.
- `packages/tools`: Node 전용 도구. `content/` 를 읽고 쓴다.
- `content/maps/raw/` 는 OSM·고도 원본 캐시 (git 제외).
- 틱 흐름: 상태는 `step(world, cmds)`(`sim/src/world.ts`) 안에서만 바뀌고, 명령은 `applyCommand`(`command.ts`)로 들어간다. 클라이언트는 틱마다 낸 명령을 `commandLog` 에 쌓은 뒤 `step` 을 부른다. 테스트·headless 는 `runReplay` + `stateHash`(`replay.ts`)로 결정성을 비교한다.
- 현재 지도는 `content/maps/rasdorf.json` 하나로 고정, `content/scenarios/` 는 비어 있고 분대 편성은 클라이언트·headless 에 임시 하드코딩.
- `CLAUDE.md`, `AGENTS.md`, `docs/`, `.claude/` 는 ai-documents 레포(`projects/tctp/`)를 가리키는 심볼릭 링크다. 수정은 링크를 따라가 그쪽 레포에서 커밋·푸시한다.

## 원칙 (POC 에서 확정된 것)
- **결정성**: 시드 RNG(`rng.ts`)만 쓴다 (`Math.random()` 금지). 시간은 정수 `tick` (1틱 = 0.1초). 같은 지도·시드·명령 기록 → 같은 `stateHash`.
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
- 코드를 커밋할 때마다 `docs/`·`AGENTS.md`·`README.md` 를 최신화해야 하는지 판단하고, 필요하면 같은 작업에서 고친다 (`docs/`·`AGENTS.md` 는 ai-documents 쪽에 커밋).

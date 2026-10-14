# 아키텍처 — 현재 코드 기준

지금 코드가 어떻게 짜여 있는지 정리한 문서. 왜 그렇게 정했는지와 앞으로 옮겨 올 시뮬 모델은 [`DESIGN.md`](DESIGN.md) 에 있다.
코드가 바뀌면 이 문서도 같이 고친다.

## 패키지와 의존 방향

```
content/  (지도·시나리오 JSON)
   ▲ 읽기                ▲ 쓰기 (fetch-map)
   │                     │
@tctp/client ──▶ @tctp/sim ◀── @tctp/tools
 (브라우저)      (순수 TS)       (Node)
```

| 패키지 | 실행 환경 | 하는 일 |
|---|---|---|
| `@tctp/sim` | 어디서나 (lib `ES2022`, types 없음) | 상태 타입, 1틱 진행, 명령 적용, 고정 틱 세션, 화면용 스냅샷, 리플레이·해시, 시드 RNG, 지도 형식 |
| `@tctp/client` | 브라우저 (Vite, Canvas 2D) | 입력을 `Command` 로 바꿔 `Session` 에 넣고, `Snapshot` 을 `Renderer` 로 그린다 |
| `@tctp/tools` | Node (`tsx`) | OSM·고도로 지도 생성, 화면 없이 시뮬 실행 |

- 의존은 항상 `sim` 쪽으로만 향한다. `sim` 은 다른 패키지와 `content/` 를 모른다. 지도는 호출하는 쪽이 읽어서 `createWorld` 에 넘긴다.
- 빌드 단계는 없다. `@tctp/sim` 의 `exports` 가 `src/*.ts` 를 바로 가리키고, `@tctp/sim/<파일>` 로 모듈 하나만 가져올 수도 있다 (`fetch-osm`·`elevation` 은 `@tctp/sim/map` 의 타입만 가져온다).
- `sim` 의 tsconfig 는 DOM·Node 타입을 빼 두어서, 브라우저·Node API 를 쓰면 타입 검사에서 막힌다.
- 클라이언트는 Vite 별칭 `@content` 로 `content/` 의 JSON 을 번들에 넣는다. tools 는 파일 경로로 `content/` 를 직접 읽고 쓴다.

## 시뮬 코어 (`packages/sim/src`)

| 파일 | 내용 |
|---|---|
| `types.ts` | `World` (지도, RNG, 정수 `tick`, `soldiers`, `log`), `Soldier`, `Side` |
| `world.ts` | `createWorld`, `step`, 시간 상수(`DT = 0.1`, `TICKS_PER_SEC = 10`), 튜닝 상수 `MOVE` |
| `command.ts` | `Command` 유니온(`move`, `stop`), `TimedCommand`, `applyCommand` |
| `replay.ts` | `runReplay`(명령 기록 재생), `stateHash`(FNV-1a 상태 지문) |
| `rng.ts` | mulberry32 RNG. 상태가 숫자 하나라 해시·세이브에 그대로 담긴다 |
| `map.ts` | `MapData` 형식 (면·선 지물, 지명, 고도 격자) |
| `session.ts` | `Session`: 명령 접수(`issue`), 실제 시간 → 고정 틱 진행(`advance`, 상한 `LOOP.maxFrame`), `commandLog`, 일시정지 |
| `snapshot.ts` | `snapshot(world, viewer)`: 렌더러용 순수 데이터 (JSON 직렬화 가능, `World` 와 참조 공유 없음). 정보 안개를 거르는 자리 |

### 프런트엔드 경계

```
프런트엔드 ──Command──▶ Session.issue
          ◀─Snapshot── Session.snapshot(viewer)      지도(MapData)는 판 시작 때 한 번
          Session.advance(실제 경과 초)
```

- 프런트엔드는 `World` 를 직접 읽지 않는다. 오가는 것은 `Command`·`Snapshot`·`MapData` 뿐이고 셋 다 JSON 이다.
- 같은 TS 안에서 그리는 방식만 바꿀 때 (Three.js 2.5D 등): 클라이언트의 `Renderer` 구현을 새로 만들어 `main.ts` 에서 바꿔 끼운다.
- 다른 언어로 렌더링할 때: sim 을 Node(또는 JS 엔진 내장) 호스트에서 `Session` 으로 돌리고, 위 세 JSON 을 WebSocket·IPC 로 주고받는다. 아직 이 호스트는 없다.
- `Snapshot` 의 이동 목표(`dest`)는 보는 진영 병사만 담긴다. 정보 안개는 아직 없어서 병사는 전부 담긴다.

### 1틱의 흐름

```
step(world, commands)
  1. commands 를 순서대로 applyCommand  ← 상태를 바꾸는 입구는 여기뿐
  2. world.tick++
  3. updateMovement: dest 가 있는 병사를 MOVE.walk × DT 만큼 직선 이동, MOVE.arrive 안이면 정지
```

- 명령은 상태를 직접 바꾸지 않고, 틱 시작 때 `step` 안에서만 적용된다. 그래서 `(지도, 시드, 초기 편성, TimedCommand[])` 만 있으면 같은 판을 다시 만들 수 있다.
- `stateHash` 는 tick, RNG 상태, 병사 id·위치(mm 반올림)를 섞는다. 상태에 새 필드를 넣으면 해시에도 넣어야 결정성 테스트가 그 필드를 검사한다.
- `Soldier` 는 지금 위치·방향·이동 목표·소속(분대/조)만 가진다. 장비·자원·상태값은 아직 없다 (DESIGN.md 의 "시뮬 모델" 표가 옮겨 올 목록).

## 클라이언트 (`packages/client/src`)

| 파일 | 내용 |
|---|---|
| `main.ts` | 진입점. 임시 편성, 입력 → `Command`, `Session` 진행, HUD. 렌더러는 인터페이스로만 쓴다 |
| `renderer.ts` | `Renderer` 인터페이스: `setMap`·`resize`·`draw(RenderView)`, 화면 ↔ 지도(`screenToMap`·`pickSoldier`), 시점(`lookAt`·`pan`·`zoomAt`). 카메라·투영은 구현이 가진다 |
| `canvas2d.ts` | `Canvas2DRenderer`: 지금 쓰는 2D 탑뷰 구현. `Snapshot` 만 읽는다 |
| `iso25d.ts` | `Iso25DRenderer`: 2.5D 등각 투영 POC. 고도 격자로 지형·지물·병사를 들고 건물은 고정 높이로 세운다. 가림 처리는 묶음별 먼 것부터 그리기뿐이다 |
| `camera.ts` | 2D 탑뷰용 지도 미터 ↔ 화면 픽셀 변환, 커서 기준 확대 |

```
마우스·키 ─▶ issue(cmd) ─▶ pending[]
requestAnimationFrame:
  session.advance(경과 실시간)
     acc += 경과 (정지 중 0, 최대 LOOP.maxFrame)
     acc 가 0.1초 이상인 동안: pending 을 commandLog 에 {tick, cmd} 로 기록 → step(world, pending) → pending 비움
  snapshot = session.snapshot("blue") → renderer.draw({snapshot, selected}) → HUD
```

- 조작: 좌클릭 = 분대 선택 (한 명을 누르면 같은 분대 전원), 우클릭 = 이동, 휠 = 확대, 가운데 드래그 = 지도 이동, Space = 일시정지.
- `commandLog` 는 리플레이·버그 재현용으로 쌓기만 하고, 아직 저장하거나 내보내지는 않는다.
- 시드는 URL `?seed=` 로 받는다 (기본 1).
- 렌더러는 URL `?view=` 로 고른다: `2d` (기본), `iso` (2.5D POC), `split` (둘을 나란히, 같은 세션·선택을 공유).
- 정보 안개는 아직 없다. 지금은 모든 병사를 그린다.

## 도구 (`packages/tools/src`)

| 파일 | 명령 | 내용 |
|---|---|---|
| `fetch-osm.ts` | `npm run fetch-map` | Overpass 에서 bbox 의 지물을 받아 미터 좌표 `MapData` 로 변환해 `content/maps/<id>.json` 에 저장. 원본은 `content/maps/raw/` 에 캐시 (`--from-cache` 로 재변환만) |
| `elevation.ts` | (fetch-osm 이 호출) | AWS Terrain Tiles (terrarium PNG) 를 받아 고도 격자로 재표본화. PNG 디코더는 직접 구현 |
| `headless.ts` | `npm run headless` | 시드마다 `createWorld` + `runReplay` 를 돌려 `stateHash` 와 소요 시간을 출력 |

## 데이터

- `content/maps/rasdorf.json` 이 유일한 지도이고, 클라이언트·headless 둘 다 이 이름으로 고정돼 있다.
- `content/scenarios/` 는 비어 있다. 분대 편성(9명, 1조 5 / 2조 4)은 `client/main.ts` 와 `tools/headless.ts` 에 각각 하드코딩돼 있고, headless 의 명령도 고정 스크립트 하나다.
- 지도 좌표: 원점 = 북서쪽 모서리, x 동쪽, y 남쪽 (화면 방향과 같음). 고도는 base64 Int16LE, 0.1m 단위.

## 테스트

- Vitest, `packages/*/src/**/*.test.ts`. `sim/src/world.test.ts` (이동·도착 정지, 같은 시드 + 같은 명령 기록 → 같은 해시), `sim/src/session.test.ts` (고정 틱 분할·상한, 정지 중 명령 보류, 세션 기록 리플레이 = 같은 해시, 스냅샷 JSON 왕복·참조 분리·타 진영 `dest` 제외).
- CI (`.github/workflows/ci.yml`): push·PR 마다 `npm run check` (typecheck + Biome + Vitest) 와 `npm run build`.

# 아키텍처 — 현재 코드 기준

지금 코드가 어떻게 짜여 있는지 정리한 문서. 왜 그렇게 정했는지와 앞으로 옮겨 올 시뮬 모델은 [`DESIGN.md`](DESIGN.md) 에 있다.
객체별 필드·단위·현재 값은 [`objects/`](objects/README.md).
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
| `types.ts` | `World` (지도, 지형 격자, RNG, 정수 `tick`, `soldiers`, 진영별 `contacts`, `log`), `Soldier` (이름·직책·몸 크기·휴대 장비·하중·자세·상태·부위별 체력·스트레스·지구력·위치), `Contact`, `Side` |
| `time.ts` | 시간 상수 `DT = 0.25`, `TICKS_PER_SEC = 4`, `secToTicks`. 튜닝 수치는 초 단위로 적고 틱으로 바꾼다 (DT 를 바꿔도 다른 상수는 그대로) |
| `world.ts` | `createWorld`, `step`, 튜닝 상수 `MOVE` (시간 상수 재노출) |
| `soldier.ts` | 기본 몸 `BODY`, 휴대 무게 한도 `checkCarry`, 몸 상태: 자세별 높이·기본 속도, 심리 단계 `stressLevelOf`, 하중 `loadOf`, 속도 `speedOf`, `damage`·`addStress`, 매 틱 `updateBody` (지구력·상태·스트레스). 튜닝 상수 `POSTURE_HEIGHT`·`BASE_SPEED`·`LOAD`·`STAMINA`·`STRESS`·`HEALTH` |
| `command.ts` | `Command` 유니온(`move`, `stop`, `posture`), `TimedCommand`, `applyCommand`, 혼란 중 미룬 명령 `applyDueOrders` |
| `replay.ts` | `runReplay`(명령 기록 재생), `stateHash`(FNV-1a 상태 지문) |
| `rng.ts` | mulberry32 RNG. 상태가 숫자 하나라 해시·세이브에 그대로 담긴다 |
| `map.ts` | `MapData` 형식 (면·선 지물, 지명, 고도 격자) |
| `terrain.ts` | 지형 격자: 지도의 면·선 지물을 1m 칸으로 굽고(`terrainOf`, 지도마다 한 번), 종류별 성질 표 `TERRAIN` (지물 높이·시야 감쇠·은폐·엄폐·이동 배율). 고도 base64 디코드와 쌍선형 `elevAt` |
| `vision.ts` | 시선 `lineOfSight` (능선 차단·지물 감쇠), 시야각 `fovFactor`, 발견 확률 `detectChance`, 탐지 주기마다 `updateVision` 으로 `contacts` 갱신. 튜닝 상수 `VISION` |
| `equipment.ts` | 화기(`Weapon`: 직사/곡사·탄약·유효사거리)·탄약(`Ammo`: 관통력·폭발·폭발 반경·제압 반경)·장구(`Gear`: 무게) 형식, `LoadoutItem`, 화기 칸 `WEAPON_SLOTS`(주 1·보조 1), 검사 `checkLoadout` (칸 초과 포함) |
| `org.ts` | 편제 `OrgTemplate` (공통 장구 `kit`, 조 → 직책 → 휴대 장비, 출처·추정 메모), `strengthOf`, `checkOrg` |
| `scenario.ts` | 시나리오 형식, `ContentDb`, `buildSoldiers` (편제·대형·이름으로 병사 생성) |
| `session.ts` | `Session`: 명령 접수(`issue`), 실제 시간 → 고정 틱 진행(`advance`, 상한 `LOOP.maxFrame`), `commandLog`, 일시정지 |
| `snapshot.ts` | `snapshot(world, viewer, {truth})`: 렌더러용 순수 데이터 (JSON 직렬화 가능, `World` 와 참조 공유 없음). 정보 안개: 모르는 적은 빠지고, 아는 적은 `contact` = seen(실제 위치)·last(마지막 위치), 적의 이름·직책은 비운다. `truth` 는 디버그용 |

### 프런트엔드 경계

```
프런트엔드 ──Command──▶ Session.issue
          ◀─Snapshot── Session.snapshot(viewer)      지도(MapData)는 판 시작 때 한 번
          Session.advance(실제 경과 초)
```

- 프런트엔드는 `World` 를 직접 읽지 않는다. 오가는 것은 `Command`·`Snapshot`·`MapData` 뿐이고 셋 다 JSON 이다.
- 같은 TS 안에서 그리는 방식만 바꿀 때 (Three.js 2.5D 등): 클라이언트의 `Renderer` 구현을 새로 만들어 `main.ts` 에서 바꿔 끼운다.
- 다른 언어로 렌더링할 때: sim 을 Node(또는 JS 엔진 내장) 호스트에서 `Session` 으로 돌리고, 위 세 JSON 을 WebSocket·IPC 로 주고받는다. 아직 이 호스트는 없다.
- `Snapshot` 의 이동 목표(`dest`)는 보는 진영 병사만 담긴다.

### 1틱의 흐름

```
step(world, commands)
  1. commands 를 순서대로 applyCommand  ← 상태를 바꾸는 입구는 여기뿐
     applyDueOrders: 혼란·위축으로 미뤄 둔 명령 중 때가 된 것 적용
  2. world.tick++
  3. updateMovement: 움직일 수 있는 병사(무력화·제압 아님)만, dest 쪽으로 speedOf(자세·하중·지구력·다리) × 선 칸의 move 배율 × DT 만큼 직선 이동. 다음 칸이 통행 불가면 그 자리, MOVE.arrive 안이면 정지
  4. updateBody: 지구력 소모·회복, status 결정 (제압·패닉·무력화면 엎드림, 위협 인지면 앉음), 스트레스 감소 → 심리 단계 갱신
  5. updateVision: VISION.interval(1초) 틱마다 진영별로 적을 본다 (무력화·패닉 병사는 관측자에서 빠지고, 발견 확률에 심리 단계 배율)
       이미 보던 적 → 아무 관측자나 시선 투과율 ≥ VISION.track 이면 계속 봄
       아니면 관측자 id 순서로 detectChance 를 굴려 발견 (world.rng, 결정적)
       못 보면 마지막 위치를 VISION.memory 틱 동안 기억, 처음 발견하면 log 에 남김
```

- 명령은 상태를 직접 바꾸지 않고, 틱 시작 때 `step` 안에서만 적용된다. 그래서 `(지도, 시드, 초기 편성, TimedCommand[])` 만 있으면 같은 판을 다시 만들 수 있다.
- `stateHash` 는 tick, RNG 상태, 병사 id·위치(mm 반올림)·자세·상태·스트레스·심리 단계·미뤄 둔 명령 틱·지구력·하중·부위별 체력, 진영별 contacts(id·틱·보임)를 섞는다. 상태에 새 필드를 넣으면 해시에도 넣어야 결정성 테스트가 그 필드를 검사한다.
- `Soldier` 는 위치·방향·이동 목표·소속(분대/조)과 이름·직책·몸 크기·휴대 장비, 몸 상태(하중·자세·상태·부위별 체력·스트레스·지구력)를 가진다 ([objects/soldier.md](objects/soldier.md)). 장비는 id 로만 들고, 성능은 `ContentDb.equipment` 에서 찾는다 (하중은 편성 때 계산해 둔다).
- 지형 격자는 지도에서만 만들어지고 바뀌지 않아 해시에 넣지 않는다. 1199 × 1001 칸 기준 굽기에 약 60ms.

## 클라이언트 (`packages/client/src`)

| 파일 | 내용 |
|---|---|
| `main.ts` | 진입점. `?scenario=<id>` 가 있으면 게임, 없으면 메뉴 |
| `content.ts` | `content/` 를 번들에 넣어 `ContentDb`·시나리오·캠페인으로 묶음. 지도는 시나리오를 고를 때 따로 불러옴 |
| `menu.ts` | 메뉴 화면: 과정 고르기(TACTICAL·COMMAND·STAFF) → 제대 과정·훈련 목록·브리핑/편제/장비 탭 → 훈련 시작 |
| `game.ts` | 게임 화면: 시나리오로 병사를 세우고, 입력 → `Command`, `Session` 진행, HUD. 렌더러는 인터페이스로만 쓴다 |
| `renderer.ts` | `Renderer` 인터페이스: `setMap`·`resize`·`draw(RenderView)`, 화면 ↔ 지도(`screenToMap`·`pickSoldier`), 시점(`lookAt`·`pan`·`zoomAt`). 카메라·투영은 구현이 가진다 |
| `canvas2d.ts` | `Canvas2DRenderer`: 지금 쓰는 2D 탑뷰 구현. `Snapshot` 만 읽는다. 마지막 위치만 아는 적은 흐리게 (`contactAlpha`) |
| `iso25d.ts` | `Iso25DRenderer`: 2.5D 등각 투영 POC. 시뮬과 같은 고도(`elevAt`)로 지형·지물·병사를 들고 건물은 고정 높이로 세운다. 가림 처리는 묶음별 먼 것부터 그리기뿐이다 |
| `camera.ts` | 2D 탑뷰용 지도 미터 ↔ 화면 픽셀 변환, 커서 기준 확대 |

```
마우스·키 ─▶ issue(cmd) ─▶ pending[]
requestAnimationFrame:
  session.advance(경과 실시간)
     acc += 경과 (정지 중 0, 최대 LOOP.maxFrame)
     acc 가 DT(0.25초) 이상인 동안: pending 을 commandLog 에 {tick, cmd} 로 기록 → step(world, pending) → pending 비움
  snapshot = session.snapshot(scenario.player) → renderer.draw({snapshot, selected}) → HUD
```

- 조작: 좌클릭 = 분대 선택 (한 명을 누르면 같은 분대 전원), 우클릭 = 이동, 휠 = 확대, 가운데 드래그 = 지도 이동, Space = 일시정지, Esc = 메뉴.
- `commandLog` 는 리플레이·버그 재현용으로 쌓기만 하고, 아직 저장하거나 내보내지는 않는다.
- 시드는 URL `?seed=` 로 받는다 (기본 = 시나리오의 seed). `?truth=1` 이면 정보 안개를 끄고 모르는 적도 흐리게 그린다 (디버그).
- 렌더러는 URL `?view=` 로 고른다: `2d` (기본), `iso` (2.5D POC), `split` (둘을 나란히, 같은 세션·선택을 공유).

## 도구 (`packages/tools/src`)

| 파일 | 명령 | 내용 |
|---|---|---|
| `fetch-osm.ts` | `npm run fetch-map` | Overpass 에서 bbox 의 지물을 받아 미터 좌표 `MapData` 로 변환해 `content/maps/<id>.json` 에 저장. 원본은 `content/maps/raw/` 에 캐시 (`--from-cache` 로 재변환만) |
| `elevation.ts` | (fetch-osm 이 호출) | AWS Terrain Tiles (terrarium PNG) 를 받아 고도 격자로 재표본화. PNG 디코더는 직접 구현 |
| `content.ts` | | `content/` 를 파일 경로로 읽어 `ContentDb`·시나리오·지도로 (`loadDb`, `loadScenario`, `loadMap`) |
| `headless.ts` | `npm run headless` | 시나리오(`--scenario`, 기본 배틀 드릴 1)를 시드마다 돌려 `stateHash`, 진영별 첫 발견 시각, 아는 적 수, 소요 시간을 출력. 명령은 임시로 "플레이어 부대 전원이 적 부대 위치로 이동" |

## 데이터

- `content/maps/rasdorf.json` 이 유일한 지도. 시나리오가 `map` 으로 가리킨다.
- `content/campaign.json`: 과정(TACTICAL·COMMAND·STAFF) → 제대 과정 → 훈련(시나리오 id) 목록, 잠김 표시.
- `content/scenarios/*.json`: 지도·시드·플레이어 진영·시작 화면·브리핑·부대(편제 id, 위치, 방위각, 대형 column/line, 간격). 지금은 `bd1-react-to-contact` 하나.
- `content/orgs/*.json`: 편제 (`rok-rifle-squad` 8명, `kpa-infantry-squad` 12명). `content/equipment.json`: 화기·탄약 목록. `content/names.json`: 이름 생성용 성·이름.
- 지도 좌표: 원점 = 북서쪽 모서리, x 동쪽, y 남쪽 (화면 방향과 같음). 고도는 base64 Int16LE, 0.1m 단위.

## 테스트

- Vitest, `packages/*/src/**/*.test.ts`. `sim/src/world.test.ts` (이동·도착 정지, 같은 시드 + 같은 명령 기록 → 같은 해시), `sim/src/session.test.ts` (고정 틱 분할·상한, 정지 중 명령 보류, 세션 기록 리플레이 = 같은 해시, 스냅샷 JSON 왕복·참조 분리·타 진영 `dest` 제외, 정보 안개), `sim/src/soldier.test.ts` (하중 합·하중 속도 감소, 자세 속도·높이, 지구력 소모·회복·지친 속도, 포복 소모, 심리 단계 문턱·패닉 회복 문턱, 위협 인지 앉기, 혼란 명령 지연, 제압 고착과 해제, 패닉 명령 거부·관측 불가, 심리 단계 발견 배율, 다리 부상 포복, 무력화·사망), `sim/src/vision.test.ts` (지형 굽기·고도 디코드, 시선 차단·감쇠·능선, 발견·등 뒤·건물 너머·기억과 망각, 통행 불가 칸), `tools/src/content.test.ts` (편제 인원 8·12, 전원 하중 ≤ 몸무게 × 0.45, 시나리오의 편제·장비 참조, 시작 위치 통행 가능, 이름 중복 없음). 공용 도우미는 `sim/src/test-util.ts`.
- CI (`.github/workflows/ci.yml`): push·PR 마다 `npm run check` (typecheck + Biome + Vitest) 와 `npm run build`.

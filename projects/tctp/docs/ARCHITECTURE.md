# 아키텍처 — 현재 코드 기준

지금 코드가 어떻게 짜여 있는지 정리한 문서. 왜 그렇게 정했는지와 앞으로 옮겨 올 시뮬 모델은 [`DESIGN.md`](DESIGN.md) 에 있다.
객체별 필드·단위·현재 값은 [`objects/`](objects/README.md), 수치 계산 식과 난수는 [`calc/`](calc/README.md).
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
| `@tctp/render3d` | 브라우저 (Three.js WebGL) | 3D 렌더러 POC: 고도 메시 지면(지물을 칠한 텍스처), 박공지붕 건물, 숲·산울타리·담장, 관절 인형 병사(자세·걸음 애니메이션), 해·그림자·안개. 클라이언트 `Renderer` 를 구조적으로 맞추고 `Snapshot`·`MapData` 만 읽는다 |
| `@tctp/tools` | Node (`tsx`) | OSM·고도로 지도 생성, 화면 없이 시뮬 실행 |

- 의존은 항상 `sim` 쪽으로만 향한다. `sim` 은 다른 패키지와 `content/` 를 모른다. 지도는 호출하는 쪽이 읽어서 `createWorld` 에 넘긴다.
- 빌드 단계는 없다. `@tctp/sim` 의 `exports` 가 `src/*.ts` 를 바로 가리키고, `@tctp/sim/<폴더>/<파일>` 로 모듈 하나만 가져올 수도 있다 (`fetch-osm`·`elevation` 은 `@tctp/sim/terrain/map` 의 타입만 가져온다).
- `sim` 의 tsconfig 는 DOM·Node 타입을 빼 두어서, 브라우저·Node API 를 쓰면 타입 검사에서 막힌다.
- 클라이언트는 Vite 별칭 `@content` 로 `content/` 의 JSON 을 번들에 넣는다. tools 는 파일 경로로 `content/` 를 직접 읽고 쓴다.

## 시뮬 코어 (`packages/sim/src`)

도메인별 폴더로 나눈다. 테스트(`*.test.ts`)는 대상 파일 곁에 둔다. 바깥에서는 `@tctp/sim`([`index.ts`](../packages/sim/src/index.ts) 가 전부 다시 내보냄) 또는 `@tctp/sim/<폴더>/<파일>` 로 가져온다.
1틱은 [`core/world.ts`](../packages/sim/src/core/world.ts) 의 `step` 이 `command` → `body` → `perception` 순으로 부른다 (아래 "1틱의 흐름").

### [`core/`](../packages/sim/src/core) — 시뮬 뼈대: 상태 타입, 1틱 진행, 시간, 난수, 리플레이

| 파일 | 내용 |
|---|---|
| [`types.ts`](../packages/sim/src/core/types.ts) | `World` (지도, 지형 격자, RNG, 정수 `tick`, `soldiers`, 진영별 `contacts`, `log`), `Soldier` (이름·직책·몸 크기·휴대 장비·하중·자세·상태·부상·혈액·스트레스·지구력·위치), `Wound`, `Contact`, `Side` |
| [`time.ts`](../packages/sim/src/core/time.ts) | 시간 상수 `DT = 0.25`, `TICKS_PER_SEC = 4`, `secToTicks`, 초당 확률 → 틱 확률 `perSecChance`. 튜닝 수치는 초 단위로 적고 틱으로 바꾼다 (DT 를 바꿔도 다른 상수는 그대로) |
| [`world.ts`](../packages/sim/src/core/world.ts) | `createWorld`, `step` (시간 상수 재노출) |
| [`rng.ts`](../packages/sim/src/core/rng.ts) | mulberry32 RNG. 상태가 숫자 하나라 해시·세이브에 그대로 담긴다 |
| [`vary.ts`](../packages/sim/src/core/vary.ts) | 사건별 흔들림 `VARY` (반응 시간·걸음·서는 자리·조준 시간·점사·겨눔·재장전·스트레스), `vary`·`gauss`·`inDisk`. 능력치가 아닌 사건 잡음 |
| [`replay.ts`](../packages/sim/src/core/replay.ts) | `runReplay`(명령 기록 재생), `stateHash`(FNV-1a 상태 지문) |

### [`command/`](../packages/sim/src/command) — 입력 → 병사 행동

| 파일 | 내용 |
|---|---|
| [`command.ts`](../packages/sim/src/command/command.ts) | `Command` 유니온(`move`, `stop`, `posture`), `TimedCommand`, `applyCommand`, 혼란 중 미룬 명령 `applyDueOrders` |
| [`spacing.ts`](../packages/sim/src/command/spacing.ts) | 병사 사이 최소 간격: 겹친 짝 떼기 `separate`(step 이 행동 뒤에 부름), 목표 둘레 먼저 선 병사 곁에서 멈추기 `blockedNear`, 여럿을 한 점으로 보낼 때의 자리 `slotOffset`, 튜닝 상수 `SPACING`. 식은 [calc/movement.md](calc/movement.md) |
| [`action.ts`](../packages/sim/src/command/action.ts) | 병사 행동 `Action`(`move`·`fire`·`reload`·`rest`), 종류별 처리 함수 표 `ACTIONS`, 매 틱 `updateActions`, `destOf`, 튜닝 상수 `MOVE`. 구조는 [objects/action.md](objects/action.md) |

### [`body/`](../packages/sim/src/body) — 몸 상태: 자세·속도·심리, 부상, 늘고 주는 수치

| 파일 | 내용 |
|---|---|
| [`soldier.ts`](../packages/sim/src/body/soldier.ts) | 기본 몸 `BODY`, 휴대 무게 한도 `checkCarry`, 몸 상태: 자세별 높이·기본 속도·약진 속도, 심리 단계 `stressLevelOf`, 하중 `loadOf`, 속도 `speedOf(s, gait)`, 매 틱 `updateBody` (출혈·지구력·상태·자세·스트레스). 기본 상태 전환 `updateBaseState` (감시 ↔ 휴식, #25). 튜닝 상수 `BASE_STATE`·`POSTURE_HEIGHT`·`BASE_SPEED`·`RUSH_SPEED`·`LOAD`·`STAMINA`·`STRESS` |
| [`wound.ts`](../packages/sim/src/body/wound.ts) | 부상: `rollWound`(부위·탄 위력·총탄/파편 → 정도·출혈), 부위 기능 `partLevel`·`armUse`·`legUse`, `isDead`·`isIncapacitated`·`isWeak`. 튜닝 상수 `WOUND` |
| [`rates.ts`](../packages/sim/src/body/rates.ts) | 늘고 주는 몸 수치: 스트레스(`threat`·`addStress`·`shock`·`buddyDown`·`updateStress`), 지구력 `updateStamina`, 출혈 `updateBlood`. 튜닝 상수 `RATES` ([calc/rates.md](calc/rates.md)) |

### [`combat/`](../packages/sim/src/combat) — 사격 판정

| 파일 | 내용 |
|---|---|
| [`fire.ts`](../packages/sim/src/combat/fire.ts) | 화기 트리거 `pullTrigger` → 탄도선 판정(사람·지물·땅), 근탄 제압, 폭발, 부위 피해. 튜닝 상수 `FIRE`, 조준점 `AimPoint` |

### [`perception/`](../packages/sim/src/perception) — 보는 것: 경계 시선, 시야·탐지

| 파일 | 내용 |
|---|---|
| [`hearing.ts`](../packages/sim/src/perception/hearing.ts) | 듣기 (#35): 이번 틱 탄의 총성·폭발음 크기 `loudness`·`soundOf`, 모든 병사가 듣고 스트레스가 오르는 `updateHearing`, 가장 큰 적 소리 `loudestFoe` (돌아보기는 scan.ts) |
| [`scan.ts`](../packages/sim/src/perception/scan.ts) | 경계(시선): 분대 안 자리별 경계 구역 `sectorOf`, 눈 방향 `look` 을 정하는 `updateScan`. 튜닝 상수 `SCAN` |
| [`vision.ts`](../packages/sim/src/perception/vision.ts) | 시선 `lineOfSight` (능선 차단·지물 감쇠, 끊긴 곳 `SightBlock` out), 시야각 `fovFactor`(눈 방향 `look` 기준), 발견 확률 `detectChance` (배율 분해 `detectFactors`), 매 틱 `updateVision` 으로 `contacts` 갱신. 튜닝 상수 `VISION` |

### [`terrain/`](../packages/sim/src/terrain) — 지도 형식과 지형 격자

| 파일 | 내용 |
|---|---|
| [`map.ts`](../packages/sim/src/terrain/map.ts) | `MapData` 형식 (면·선 지물, 지명, 고도 격자) |
| [`terrain.ts`](../packages/sim/src/terrain/terrain.ts) | 지형 격자: 지도의 면·선 지물을 1m 칸으로 굽고(`terrainOf`, 지도마다 한 번), 종류별 성질 표 `TERRAIN` (지물 높이·시야 감쇠·은폐·엄폐·이동 배율). 고도 base64 디코드와 쌍선형 `elevAt` |

### [`content/`](../packages/sim/src/content) — 콘텐츠 형식: 장비·편제·시나리오

| 파일 | 내용 |
|---|---|
| [`equipment.ts`](../packages/sim/src/content/equipment.ts) | 화기(`Weapon`: 직사/곡사·탄약·유효사거리)·탄약(`Ammo`: 관통력·폭발·폭발 반경·제압 반경)·장구(`Gear`: 무게) 형식, `LoadoutItem`, 화기 칸 `WEAPON_SLOTS`(주 1·보조 1), 검사 `checkLoadout` (칸 초과 포함) |
| [`org.ts`](../packages/sim/src/content/org.ts) | 편제 `OrgTemplate` (공통 장구 `kit`, 조 → 직책 → 휴대 장비, 출처·추정 메모), `strengthOf`, `checkOrg` |
| [`scenario.ts`](../packages/sim/src/content/scenario.ts) | 시나리오 형식, `ContentDb`, `buildSoldiers` (편제·대형·이름으로 병사 생성) |

### [`view/`](../packages/sim/src/view) — 프런트엔드와 맞닿는 곳: 고정 틱 세션, 화면용 스냅샷

| 파일 | 내용 |
|---|---|
| [`save.ts`](../packages/sim/src/view/save.ts) | 저장·불러오기 형식 `SaveData`(`SAVE_VERSION`, 시나리오 id·시드·틱·`stateHash`·명령 기록): `makeSave`, `parseSave`(옛·새 버전·빠진 항목은 `SaveError` 로 거부, 옮기기는 `migrate`), `restoreSession`(새 세계에 리플레이 → 해시가 다르면 거부, 정지 상태로) |
| [`session.ts`](../packages/sim/src/view/session.ts) | `Session`: 명령 접수(`issue`), 실제 시간 → 고정 틱 진행(`advance`, 상한 `LOOP.maxFrame`), `commandLog`, 일시정지 |
| [`snapshot.ts`](../packages/sim/src/view/snapshot.ts) | `snapshot(world, viewer, {truth})`: 렌더러용 순수 데이터 (JSON 직렬화 가능, `World` 와 참조 공유 없음). 정보 안개: 모르는 적은 빠지고, 아는 적은 `contact` = seen(실제 위치)·last(마지막 위치), 적의 이름·직책은 비운다. `truth` 는 디버그용 |

### [`drills/`](../packages/sim/src/drills) — 행동 확인장 드릴(e2e)과 테스트 도우미

| 파일 | 내용 |
|---|---|
| [`drills.ts`](../packages/sim/src/drills/drills.ts) | 행동 확인장 드릴 `DRILLS` (작은 평지·고도 + 배치 + 명령 기록 + 확인 항목 `ever`/`always`/`end`/초, 묶음 `DRILL_GROUPS`: 이동·사격·제압·지형 시야·자세·상태 시야·도랑·참호·매복·경계), 진행기 `DrillRun` (확인 항목별 결과·판정 틱). vitest 와 브라우저 `?debug=drills` 가 같이 쓴다 |
| [`test-util.ts`](../packages/sim/src/drills/test-util.ts) | 테스트·드릴용 평지 `flatMap`·고도 `withElev`, 병사 `soldier`·장비 지급 `arm`, 시험용 장비 `testCatalog` |

### 프런트엔드 경계

```
프런트엔드 ──Command──▶ Session.issue
          ◀─Snapshot── Session.snapshot(viewer)      지도(MapData)는 판 시작 때 한 번
          Session.advance(실제 경과 초)
```

- 프런트엔드는 `World` 를 직접 읽지 않는다. 오가는 것은 `Command`·`Snapshot`·`MapData` 뿐이고 셋 다 JSON 이다.
- 같은 TS 안에서 그리는 방식만 바꿀 때 (Three.js 2.5D 등): 클라이언트의 `Renderer` 구현을 새로 만들어 [`main.ts`](../packages/client/src/main.ts) 에서 바꿔 끼운다.
- 다른 언어로 렌더링할 때: sim 을 Node(또는 JS 엔진 내장) 호스트에서 `Session` 으로 돌리고, 위 세 JSON 을 WebSocket·IPC 로 주고받는다. 아직 이 호스트는 없다.
- `Snapshot` 의 이동 목표(`dest`, 이동 행동의 목표)와 남은 경유점(`via`)은 보는 진영 병사만 담긴다.

### 1틱의 흐름

```
step(world, commands)
  1. commands 를 순서대로 applyCommand  ← 상태를 바꾸는 입구는 여기뿐
     applyDueOrders: 혼란·위축으로 미뤄 둔 명령 중 때가 된 것 적용
  2. world.tick++
  3. updateActions: 행동할 수 있는 병사(무력화·제압·패닉 아님)만 id 순서로 행동 처리 함수를 한 걸음 진행, 끝나면 행동 비움
       move: 목표 쪽으로 speedOf(자세·하중·지구력·다리) × 선 칸의 move 배율 × DT 만큼 직선 이동. 다음 칸이 통행 불가면 그 자리, MOVE.arrive 안이면 끝
     → separate: 겹친 병사를 SPACING.min 으로 떼어 놓음 (걷는 병사가 비킴)
  3b. updateHearing: 이번 틱 탄의 총성·폭발음을 병사마다 듣고 스트레스 (적 소리면 적어도 위협 인지 + heardTick, 상한 heardCap, #35)
  4. updateBody: 평온이 깨지면 휴식 그침, 지구력 소모·회복(휴식 중에만 제대로), status 결정 (제압·패닉·무력화면 엎드림, 위협 인지면 앉음), 스트레스 감소 → 심리 단계 갱신 → 기본 상태 전환 (감시 ↔ 휴식, `updateBaseState`, world.stateRng, #25)
  5. updateScan: 병사마다 볼 곳(lookAim)을 정하고 눈(look)을 그쪽으로 돌린다 — 사격 중이면 겨누는 쪽, 직사 탄이 스치면 반응 시간 뒤 어림한 쏜 쪽(곡사는 무시), 적 소리를 들었으면 소리 크기만큼의 확률로 그쪽(총구·폭발점), 아니면 보는 시간이 다 될 때 경계 구역 안 / 아는 적 쪽 (world.lookRng)
  6. updateVision: 매 틱 진영별로 적을 본다 (무력화·패닉 병사는 관측자에서 빠지고, 발견 확률에 심리 단계 배율)
       이미 보던 적 → 아무 관측자나 시선 투과율 ≥ VISION.track 이면 계속 봄
       아니면 관측자 id 순서로 detectChance 를 굴려 발견 (world.rng, 결정적)
       못 보면 마지막 위치를 VISION.memory 틱 동안 기억, 처음 발견하면 log 에 남김
```

- 명령은 상태를 직접 바꾸지 않고, 틱 시작 때 `step` 안에서만 적용된다. 그래서 `(지도, 시드, 초기 편성, TimedCommand[])` 만 있으면 같은 판을 다시 만들 수 있다.
- `stateHash` 는 tick, RNG 상태, 병사 id·위치(mm 반올림)·자세·상태·스트레스·심리 단계·미뤄 둔 명령 틱·지구력·하중·혈액·부상·마지막 위협 틱, 진영별 contacts(id·틱·보임)를 섞는다. 상태에 새 필드를 넣으면 해시에도 넣어야 결정성 테스트가 그 필드를 검사한다.
- `Soldier` 는 위치·방향·이동 목표·소속(분대/조)과 이름·직책·몸 크기·휴대 장비, 몸 상태(하중·자세·상태·부상·혈액·스트레스·지구력)를 가진다 ([objects/soldier.md](objects/soldier.md)). 장비는 id 로만 들고, 성능은 `ContentDb.equipment` 에서 찾는다 (하중은 편성 때 계산해 둔다).
- 지형 격자는 지도에서만 만들어지고 바뀌지 않아 해시에 넣지 않는다. 1199 × 1001 칸 기준 굽기에 약 60ms.

## 클라이언트 (`packages/client/src`)

| 파일 | 내용 |
|---|---|
| [`main.ts`](../packages/client/src/main.ts) | 진입점. `?scenario=<id>` 가 있으면 게임, `?load=1` 이면 저장한 판, 없으면 메뉴 |
| [`content.ts`](../packages/client/src/content.ts) | `content/` 를 번들에 넣어 `ContentDb`·시나리오·캠페인으로 묶음. 지도는 시나리오를 고를 때 따로 불러옴 |
| [`menu.ts`](../packages/client/src/menu.ts) | 메뉴 화면: 과정 고르기(TACTICAL·COMMAND·STAFF) → 제대 과정·훈련 목록·브리핑/편제/장비 탭 → 훈련 시작 |
| [`drills/drills.ts`](../packages/sim/src/drills/drills.ts) | 행동 확인장 화면 (`?debug=drills[&drill=<id>][&seed=<n>]`, 시드를 주면 재생·전체 실행 모두 그 시드): 드릴 목록(묶음별 접기·묶음 실행)·전체 실행(e2e, 통과 수·실패 항목), 재생·속도·한 틱 앞/뒤, 탄 자취·조준선·스트레스 고리·행동 이름표·고른 병사 시야(선 사람을 계속 볼 수 있는 거리, 광선별 `lineOfSight`)·적마다 시선선(투과율·끊긴 곳·발견 %/초)·등고선 덧그리기, 지도 호버 시 지형 값, 확인 항목(판정 시각·지금 값·참/거짓), 병사 카드(자세·상태·행동·스트레스/지구력/혈액/탄창 막대, 고르면 행동 진행·몸·위치·장비·아는 적·적마다 시선과 발견 배율·원본 값, 방금 바뀐 값 강조)·명령 기록·기록. 디버그라 `World` 를 직접 읽는다 |
| [`drill-format.ts`](../packages/client/src/drill-format.ts) | 확인장용 한국어 이름표·행동 설명(`actionView`: 목표·남은 거리·조준/점사 진행)·명령 한 줄 |
| [`drill-profile.ts`](../packages/client/src/drill-profile.ts) | 확인장 시선 단면도: 고른 병사 눈 → 적 겨냥 높이까지 1m 마다 지면(파인 칸은 바닥)·지물 높이(칸 종류 색)·시선·끊긴 곳과 까닭. 세로를 늘려(배율 표시) 수십 cm 차이를 보인다. 적은 지도의 시선선·시선 표 줄·단면도 위 고르기 막대(◀ #id ▶, 적이 둘 이상일 때)로 고르고, 안 고르면 가장 가까운 적 |
| [`drill-timeline.ts`](../packages/client/src/drill-timeline.ts) | 확인장 시간축: 병사별 행동 줄, 고른 병사의 스트레스·지구력·혈액 그래프, 명령·판정 표시. 누르거나 끌면 그 틱으로 간다 (뒤로는 처음부터 다시 돌림) |
| [`game.ts`](../packages/client/src/game.ts) | 게임 화면: 시나리오로 병사를 세우고, 입력 → `Command`, `Session` 진행, HUD. 렌더러는 인터페이스로만 쓴다 |
| [`saveload.ts`](../packages/client/src/saveload.ts) | 저장 칸 하나(localStorage `tctp.save`). 게임 중 Ctrl+S = 저장, Ctrl+O = `?load=1` 로 다시 열어 `startSavedGame` 이 리플레이로 복원. 실패하면 이유를 알리고 메뉴로 |
| [`renderer.ts`](../packages/client/src/renderer.ts) | `Renderer` 인터페이스: `setMap`·`resize`·`draw(RenderView)`, 화면 ↔ 지도(`screenToMap`·`pickSoldier`), 시점(`lookAt`·`pan`·`zoomAt`). 카메라·투영은 구현이 가진다 |
| [`canvas2d.ts`](../packages/client/src/canvas2d.ts) | `Canvas2DRenderer`: 지금 쓰는 2D 탑뷰 구현. `Snapshot` 만 읽는다. 마지막 위치만 아는 적은 흐리게 (`contactAlpha`). `showContours` 로 고도 격자 등고선 (기본 끔, 확인장만 켬) |
| [`iso25d.ts`](../packages/client/src/iso25d.ts) | `Iso25DRenderer`: 2.5D 등각 투영 POC. 시뮬과 같은 고도(`elevAt`)로 지형·지물·병사를 들고 건물은 고정 높이로 세운다. 가림 처리는 묶음별 먼 것부터 그리기뿐이다 |
| [`camera.ts`](../packages/client/src/camera.ts) | 2D 탑뷰용 지도 미터 ↔ 화면 픽셀 변환, 커서 기준 확대 |

```
마우스·키 ─▶ issue(cmd) ─▶ pending[]
requestAnimationFrame:
  session.advance(경과 실시간)
     acc += 경과 (정지 중 0, 최대 LOOP.maxFrame)
     acc 가 DT(0.25초) 이상인 동안: pending 을 commandLog 에 {tick, cmd} 로 기록 → step(world, pending) → pending 비움
  snapshot = session.snapshot(scenario.player) → renderer.draw({snapshot, selected}) → HUD
```

- 조작: 좌클릭 = 분대 선택 (한 명을 누르면 같은 분대 전원), 우클릭 = 이동, Ctrl+우클릭 = 지금 이동 경로 끝에 경유점 이어 붙이기 (`via`, 선택 병사의 경로는 경유점을 지나는 꺾은선으로 그림), 휠 = 확대, 가운데 드래그 = 지도 이동, Space = 일시정지, Ctrl+S = 저장, Ctrl+O = 불러오기, Esc = 메뉴.
- 저장은 시나리오 id + 시드 + `commandLog` 만 적는다 (스냅샷 없음). 불러오기는 처음부터 리플레이하므로 긴 판일수록 느려진다 — 느려지면 스냅샷을 더하고 `SAVE_VERSION` 을 올린다.
- 시드는 URL `?seed=` 로 받는다 (기본 = 시나리오의 seed). `?truth=1` 이면 정보 안개를 끄고 모르는 적도 흐리게 그린다 (디버그).
- 사격 조작: 아는 적 위 우클릭 = 조준사격 (`fire`), Shift+우클릭 = 그 지점 제압사격 (`suppress`, 다시 하면 지점 전환), X = 고른 분대의 사격 그침 (사격·재장전 중인 병사에게 `stop`, 이동사격은 건드리지 않음). 고른 병사의 사격 목표(`fireAt`)는 점선으로, 탄은 `Snapshot.shots` 로 `drawShots`(`renderer.ts`, 2D·2.5D 공용)가 그린다 (탄 자취 `SHOT_FX.tracerSec`, 탄착, 폭발 원). 3D 렌더러는 아직 탄을 그리지 않는다.
- 렌더러는 URL `?view=` 로 고른다: `2d` (기본), `iso` (2.5D POC), `3d` (`@tctp/render3d` POC, Q/E 회전·R/F 기울기), `split` (둘을 나란히, 같은 세션·선택을 공유).

## 도구 (`packages/tools/src`)

| 파일 | 명령 | 내용 |
|---|---|---|
| [`fetch-osm.ts`](../packages/tools/src/fetch-osm.ts) | `npm run fetch-map` | Overpass 에서 bbox 의 지물을 받아 미터 좌표 `MapData` 로 변환해 `content/maps/<id>.json` 에 저장. 원본은 `content/maps/raw/` 에 캐시 (`--from-cache` 로 재변환만) |
| [`elevation.ts`](../packages/tools/src/elevation.ts) | (fetch-osm 이 호출) | AWS Terrain Tiles (terrarium PNG) 를 받아 고도 격자로 재표본화. PNG 디코더는 직접 구현 |
| [`content.ts`](../packages/tools/src/content.ts) | | `content/` 를 파일 경로로 읽어 `ContentDb`·시나리오·지도로 (`loadDb`, `loadScenario`, `loadMap`) |
| [`calc-charts.ts`](../packages/tools/src/calc-charts.ts) | `npm run charts` | 튜닝 상수로 수치 계산 그래프를 그려 `docs/calc/img/*.svg` 로 쓴다 (식은 시뮬과 같게 옮김) |
| [`headless.ts`](../packages/tools/src/headless.ts) | `npm run headless` | 시나리오(`--scenario`, 기본 배틀 드릴 1)를 시드마다 돌려 `stateHash`, 진영별 첫 발견 시각, 아는 적 수, 소요 시간을 출력. 명령은 임시로 "플레이어 부대 전원이 적 부대 위치로 이동" |

## 데이터

- [`content/maps/rasdorf.json`](../content/maps/rasdorf.json) 이 유일한 지도. 시나리오가 `map` 으로 가리킨다.
- [`content/campaign.json`](../content/campaign.json): 과정(TACTICAL·COMMAND·STAFF) → 제대 과정 → 훈련(시나리오 id) 목록, 잠김 표시.
- [`content/scenarios/*.json`](../content/scenarios): 지도·시드·플레이어 진영·시작 화면·브리핑·부대(편제 id, 위치, 방위각, 대형 column/line, 간격). 지금은 `bd1-react-to-contact` 하나.
- [`content/orgs/*.json`](../content/orgs): 편제 (`rok-rifle-squad` 8명, `kpa-infantry-squad` 12명). [`content/equipment.json`](../content/equipment.json): 화기·탄약 목록. [`content/names.json`](../content/names.json): 이름 생성용 성·이름.
- 지도 좌표: 원점 = 북서쪽 모서리, x 동쪽, y 남쪽 (화면 방향과 같음). 고도는 base64 Int16LE, 0.1m 단위.

## 테스트

- Vitest, `packages/*/src/**/*.test.ts`. [`packages/sim/src/core/world.test.ts`](../packages/sim/src/core/world.test.ts) (이동·도착 정지, 같은 시드 + 같은 명령 기록 → 같은 해시), [`packages/sim/src/view/session.test.ts`](../packages/sim/src/view/session.test.ts) (고정 틱 분할·상한, 정지 중 명령 보류, 세션 기록 리플레이 = 같은 해시, 스냅샷 JSON 왕복·참조 분리·타 진영 `dest` 제외, 정보 안개), [`packages/sim/src/view/save.test.ts`](../packages/sim/src/view/save.test.ts) (저장 → 불러오기 = 같은 틱·해시·이어서 진행해도 같음, 옛·새·없는 버전 거부, 다른 판 거부), [`packages/sim/src/body/soldier.test.ts`](../packages/sim/src/body/soldier.test.ts) (하중 합·하중 속도 감소, 자세 속도·높이, 지구력 소모·멈춤 소량 회복·지친 속도, 휴식 회복·휴식 그침·평온 아니면 휴식 거부, 포복 소모, 심리 단계 문턱·패닉 회복 문턱, 위협 인지 앉기, 혼란 명령 지연, 제압 고착과 해제, 패닉 명령 거부·관측 불가, 심리 단계 발견 배율, 다리 부상 포복, 무력화·사망), [`packages/sim/src/perception/vision.test.ts`](../packages/sim/src/perception/vision.test.ts) (지형 굽기·고도 디코드, 시선 차단·감쇠·능선, 발견·등 뒤·건물 너머·기억과 망각, 통행 불가 칸), [`tools/src/content.test.ts`](../packages/tools/src/content.test.ts) (편제 인원 8·12, 전원 하중 ≤ 몸무게 × 0.45, 시나리오의 편제·장비 참조, 시작 위치 통행 가능, 이름 중복 없음). [`packages/sim/src/combat/fire.test.ts`](../packages/sim/src/combat/fire.test.ts) (조준사격·모르는 적·건물 차단·재장전·탄 소진·기관총 제압·엄폐·유탄·결정성), [`tools/src/drills.test.ts`](../packages/tools/src/drills.test.ts) (모든 드릴을 실제 장비로 끝까지 돌려 확인 항목 검사 — 새 행동은 드릴을 더해 확인). 공용 도우미는 [`packages/sim/src/drills/test-util.ts`](../packages/sim/src/drills/test-util.ts).
- CI ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)): push·PR 마다 `npm run check` (typecheck + Biome + Vitest) 와 `npm run build`.

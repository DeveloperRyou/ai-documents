# 월드 `World` · 아는 적 `Contact` · 명령 `Command` · 화면용 `Snapshot`

## 월드 `World` ([`core/types.ts`](../../packages/sim/src/core/types.ts), `createWorld` in [`core/world.ts`](../../packages/sim/src/core/world.ts))
| 필드 | 뜻 |
|---|---|
| `map` | 지도 `MapData` |
| `terrain` | 지형 격자 ([terrain.md](terrain.md)) |
| `rng` | 시드 RNG (mulberry32). 시뮬 안 난수는 이것만 (시선만 아래 `lookRng`) |
| `lookRng` | 시선 고르기 전용 시드 RNG ([`perception/scan.ts`](../../packages/sim/src/perception/scan.ts)). 시선이 사격·피해 난수 흐름을 흔들지 않게 따로 둔다 |
| `catalog` | 장비 카탈로그 (`createWorld` 넷째 인자, 화기·탄약 제원) |
| `tick` | 경과 틱 (정수, 1틱 = 0.25초) |
| `soldiers` | `Soldier[]` ([soldier.md](soldier.md)), `soldiers[id]` |
| `contacts` | 진영별로 아는 적 `Record<Side, Contact[]>` (id 오름차순) |
| `log` | `LogEntry { tick, side \| "system", text }` — 시작, 적 발견, 피격·전사 등 |
| `shots` | 이번 틱에 쏜 탄 `Shot { by, x0, y0, x1, y1, hit, explosive, indirect }` (indirect = 곡사, 맞는 쪽은 쏜 곳을 모름) (화면 효과용, 매 틱 비움, 해시 제외) |

상태는 `step(world, commands)` 안에서만 바뀐다: 명령 적용 → 미뤄 둔 명령(`applyDueOrders`) → `tick++`·`shots` 비움 → 행동(`updateActions`) → 몸 상태(`updateBody`: 출혈·지구력·상태·자세·스트레스) → 경계 시선(`updateScan`) → 탐지(`updateVision`). 순서와 각 단계의 난수는 [../calc/README.md](../calc/README.md) "한 틱 순서".
`stateHash` 는 tick·두 RNG 상태(`rng`·`lookRng`)·병사 위치·몸 방향·시선(`look`·`lookAim`·`lookTick`·돌아볼 틱·`bodyAim`)·자세·상태·행동(종류·필드, 이동의 걸음·이동사격 포함)·스트레스·마지막 위협 틱·근탄 틱들·심리 단계·미뤄 둔 명령 틱·지구력·하중·장전 탄·휴대 수량·혈액·부상(부위·정도·출혈·틱)·contacts 를 섞는다. 새 상태 필드를 넣으면 해시에도 넣는다.

## 아는 적 `Contact` ([`core/types.ts`](../../packages/sim/src/core/types.ts), 갱신은 [`perception/vision.ts`](../../packages/sim/src/perception/vision.ts))
| 필드 | 뜻 |
|---|---|
| `id` | 적 병사 id |
| `x`, `y` | 마지막으로 본 위치 |
| `tick` | 마지막으로 본 틱 |
| `visible` | 지금 보이는지 |

갱신 (`updateVision`, 매 틱):
- 관측자 = 무력화·사망·패닉이 아닌 아군. 진영 안에서는 바로 공유.
- 이미 보던 적: 진영 안 누군가 시선 투과율 ≥ `track`(0.15) 이면 계속 봄.
- 처음 보는 적: 관측자 id 순서로 발견 확률을 굴림 (거리·시야각(`look` 기준)·시선 투과율·은폐·움직임·걷는 관측자·관측자 심리 단계의 곱 = 초당 확률, 상한 0.95. 한 틱에 `perSecChance` 로 바꿔 굴림).
- 못 보게 되면 마지막 위치를 `memory`(30초 = 120틱) 동안 기억 후 잊음.
- 식·상수·계산 예(거리별 발견 확률, 매복)는 [../calc/vision.md](../calc/vision.md). 확인장은 계수마다 값을 보여 준다 (`detectFactors`: 숨음 ×, 걷는 눈 ×).

## 명령 `Command` ([`command/command.ts`](../../packages/sim/src/command/command.ts))
| 종류 | 필드 | 뜻 |
|---|---|---|
| `move` | `ids`, `x`, `y`, `gait?`, `fire?`, `slot?` | 병사들에게 이동 행동을 준다 (진행 중 행동을 덮음). `gait`: `walk`(기본) 걷기 / `rush` 약진. `fire`: `{ target }` 또는 `{ x, y }` 이면 걸으며 쏜다 (이동사격, 조준사격·제압사격과 같은 `FIRE_ORDER`, 약진이면 무시) |
| `stop` | `ids` | 행동을 비운다 |
| `posture` | `ids`, `posture` | 자세 바꾸기 (`stand`·`crouch`·`prone`) |
| `fire` | `ids`, `target`, `slot?` | 아는 적 한 명을 조준사격 (`FIRE_ORDER.aimed`: 화기 조준 시간을 다 쓰고 한 발씩) |
| `suppress` | `ids`, `x`, `y`, `slot?` | 지점을 제압사격 (`FIRE_ORDER.suppress`: 조준 1/4, 화기 점사 발 수, 둘레 4m 쓸어 쏨). 곡사 화기는 다 조준해 한 점에 |
| `reload` | `ids`, `slot?` | 재장전 (더 채울 탄이 없으면 무시) |
| `rest` | `ids` | 제자리 휴식 (평온하지 않으면 무시) |

`slot` 을 빼면 주화기. 칸에 화기가 없으면 사격 명령은 무시된다.

무력화·사망·패닉인 병사는 명령을 받지 않는다. 명령은 반응 시간(0 ~ `VARY.reaction` 0.5초) 뒤에 따르고, 혼란·위축된 병사는 `STRESS.orderDelay`(2초)를 더 기다린다 (`Soldier.order`, 나중 명령이 덮음). 제압된 병사는 받아 두지만 풀릴 때까지 움직이지 않는다.

`TimedCommand { tick, cmd }` — 명령 기록 한 줄. 같은 지도·시나리오·시드 + 같은 기록 → 같은 판 (`runReplay`).

## 화면용 `Snapshot` ([`view/snapshot.ts`](../../packages/sim/src/view/snapshot.ts))
렌더러는 `World` 대신 이것만 읽는다. 순수 데이터 (JSON 직렬화 가능, `World` 와 참조 공유 없음).

`Snapshot { tick, time(초), viewer, soldiers: SoldierView[] }`, 세션에서 꺼내면 `paused`, `commands`(명령 수) 추가.

`SoldierView`: `id, side, name, role, squad, team, x, y, facing, look, dest(이동 행동의 목표), posture, body?, contact?`
- `body`: `{ action(행동 종류), status, wounds([{ part, severity }]), blood(남은 혈액 비율 0~1), stress, stressLevel, stamina, load, speed }` — `speed` 는 지금 낼 수 있는 걷기 속도 (m/s, 지형 계수 전).
- 보는 진영 병사: 전부 담김, `dest`·`body` 포함.
- 적: `contacts` 에 있는 적만. 이름·직책·소속은 빈 문자열, `dest`·`body` 없음.
  `contact = "seen"` 이면 실제 위치·방향·자세, `"last"` 이면 마지막으로 본 위치 (`posture = null`).
- `snapshot(world, viewer, { truth: true })` (디버그 `?truth=1`): 모든 적을 실제 상태로, 모르는 적은 `contact = "hidden"`.

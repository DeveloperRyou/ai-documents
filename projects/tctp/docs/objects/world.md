# 월드 `World` · 아는 적 `Contact` · 명령 `Command` · 화면용 `Snapshot`

## 월드 `World` (`types.ts`, `createWorld` in `world.ts`)
| 필드 | 뜻 |
|---|---|
| `map` | 지도 `MapData` |
| `terrain` | 지형 격자 ([terrain.md](terrain.md)) |
| `rng` | 시드 RNG (mulberry32). 시뮬 안 난수는 이것만 |
| `tick` | 경과 틱 (정수, 1틱 = 0.25초) |
| `soldiers` | `Soldier[]` ([soldier.md](soldier.md)), `soldiers[id]` |
| `contacts` | 진영별로 아는 적 `Record<Side, Contact[]>` (id 오름차순) |
| `log` | `LogEntry { tick, side \| "system", text }` — 시작, 적 발견 등 |

상태는 `step(world, commands)` 안에서만 바뀐다: 명령 적용 → `tick++` → 이동 → 몸 상태(`updateBody`: 지구력·상태·스트레스) → 시야.
`stateHash` 는 tick·RNG·병사 위치·자세·상태·스트레스·지구력·하중·부위별 체력·contacts 를 섞는다. 새 상태 필드를 넣으면 해시에도 넣는다.

## 아는 적 `Contact` (`types.ts`, 갱신은 `vision.ts`)
| 필드 | 뜻 |
|---|---|
| `id` | 적 병사 id |
| `x`, `y` | 마지막으로 본 위치 |
| `tick` | 마지막으로 본 틱 |
| `visible` | 지금 보이는지 |

갱신 (`updateVision`, `VISION.interval` = 1초(4틱)마다):
- 이미 보던 적: 진영 안 누군가 시선 투과율 ≥ `track`(0.15) 이면 계속 봄.
- 관측자 = 무력화·사망하지 않은 아군. 눈높이·표적 높이는 자세별 몸 높이로 계산 ([soldier.md](soldier.md)).
- 처음 보는 적: 관측자 id 순서로 `detectChance` 를 굴림 = `baseChance(0.36) × min(1, (30m / 거리)²) × 시야각 배율 × 시선 투과율 × (1 − 은폐) × 움직이면(status = moving) 2`, 상한 0.95. 0.36 = 0.5초 주기 0.2 를 두 번 굴린 값 (1 − 0.8²).
- 시야각: 정면 120° 안 1, 200° 끝에서 0.25 까지 감소, 그 밖 0. 최대 거리 800m.
- 못 보게 되면 마지막 위치를 `memory`(30초 = 120틱) 동안 기억 후 잊음. 진영 안에서는 바로 공유.

## 명령 `Command` (`command.ts`)
| 종류 | 필드 | 뜻 |
|---|---|---|
| `move` | `ids`, `x`, `y` | 병사들의 이동 목표 지정 |
| `stop` | `ids` | 이동 목표 해제 |
| `posture` | `ids`, `posture` | 자세 바꾸기 (`stand`·`crouch`·`prone`) |

무력화·사망한 병사는 명령을 받지 않는다. 제압된 병사는 받아 두지만 풀릴 때까지 움직이지 않는다.

`TimedCommand { tick, cmd }` — 명령 기록 한 줄. 같은 지도·시나리오·시드 + 같은 기록 → 같은 판 (`runReplay`).

## 화면용 `Snapshot` (`snapshot.ts`)
렌더러는 `World` 대신 이것만 읽는다. 순수 데이터 (JSON 직렬화 가능, `World` 와 참조 공유 없음).

`Snapshot { tick, time(초), viewer, soldiers: SoldierView[] }`, 세션에서 꺼내면 `paused`, `commands`(명령 수) 추가.

`SoldierView`: `id, side, name, role, squad, team, x, y, facing, dest, posture, body?, contact?`
- `body`: `{ status, health, stress, stamina, load, speed }` — `speed` 는 지금 낼 수 있는 속도 (m/s, 지형 배율 전).
- 보는 진영 병사: 전부 담김, `dest`·`body` 포함.
- 적: `contacts` 에 있는 적만. 이름·직책·소속은 빈 문자열, `dest`·`body` 없음.
  `contact = "seen"` 이면 실제 위치·방향·자세, `"last"` 이면 마지막으로 본 위치 (`posture = null`).
- `snapshot(world, viewer, { truth: true })` (디버그 `?truth=1`): 모든 적을 실제 상태로, 모르는 적은 `contact = "hidden"`.

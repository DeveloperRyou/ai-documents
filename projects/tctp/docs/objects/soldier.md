# 병사 `Soldier`

아군·적 모두 같은 객체. 진영과 장비만 다르다. 코드: `packages/sim/src/types.ts`.
시나리오의 편제에서 `buildSoldiers` 가 만든다 ([scenario.md](scenario.md)). 직접 JSON 으로 쓰지 않는다.

| 필드 | 타입 | 뜻 |
|---|---|---|
| `id` | number | 월드 안 번호. 0 부터 부대 순서대로 (`world.soldiers[id]`) |
| `side` | `"blue" \| "red"` | 진영 |
| `name` | string | 이름. `content/names.json` 의 성 + 이름을 시나리오 시드로 골라 부대 안에서 겹치지 않게 |
| `role` | string | 직책 (편제의 `role`: 분대장, 기관총 사수 …) |
| `squad` | string | 소속 분대 = 부대명 (`ForceSpec.name`). 최소 명령 단위 |
| `team` | string | 소속 조 = `"<부대명> <조 이름>"` (예: `1분대 2조`) |
| `size` | `BodySize` | 몸 크기 (m). 피탄 판정용 |
| `loadout` | `LoadoutItem[]` | 휴대 장비 |
| `x`, `y` | number | 위치 (m). 원점 = 지도 북서쪽, x 동쪽, y 남쪽 |
| `facing` | number | 바라보는 방향, 화면 라디안 (0 = 동, 시계방향). 시나리오에서는 방위각(도)으로 주고 `bearingToFacing` 으로 바꾼다 |
| `dest` | `{x, y} \| null` | 이동 목표. 없으면 정지 |

## 몸 크기 `BodySize`

| 필드 | 뜻 | 기본값 (`BODY`, `scenario.ts`) |
|---|---|---|
| `w` | 가로 (어깨 폭) | 0.5 m |
| `d` | 세로 (가슴 두께) | 0.3 m |
| `h` | 높이 (선 자세 키) | 1.75 m |

- 지금 쓰는 곳: 시야 — 눈높이 = `h × VISION.eyeRatio(0.93)`, 겨냥 높이 = `h × VISION.aimRatio(0.7)` ([world.md](world.md)).
- 자세(낮은 자세·포복)가 생기면 `h` 대신 자세별 높이를 쓴다.

## 휴대 장비 `LoadoutItem`

| 필드 | 뜻 |
|---|---|
| `item` | 장비 id ([equipment.md](equipment.md)) |
| `qty` | 수량. 화기는 정 수, 탄약은 발 수 |

- 예: 유탄수 `[{k2,1}, {k201,1}, {556-k100,210}, {40-k200,12}]`.
- `weaponsOf(loadout, catalog)` 로 화기만 뽑는다. `checkLoadout` 은 없는 장비·탄약·0 이하 수량을 오류로 돌려준다.

## 아직 없는 것
제압·사기·부상·출혈·자세·하중. 추가하면 `stateHash`(`replay.ts`)에도 섞어야 결정성 테스트가 검사한다.

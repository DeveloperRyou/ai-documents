# 장비 — 화기 `Weapon`, 탄약 `Ammo`, 장구 `Gear`, 무전기 `Radio`

코드: [`packages/sim/src/content/equipment.ts`](../../packages/sim/src/content/equipment.ts). 데이터: [`content/equipment.json`](../../content/equipment.json) (`{ note, items: Equipment[] }`).
`catalogOf(file)` 가 id → 장비 사전(`EquipmentCatalog`)으로 바꾼다. 수치는 공개 자료 기준 대략값이고 튜닝 대상이다.
사격·제압·부상 판정([`combat/fire.ts`](../../packages/sim/src/combat/fire.ts))이 아래 값을 어떻게 쓰는지는 [../calc/fire.md](../calc/fire.md).

## 화기 `Weapon` (`kind: "weapon"`)

| 필드 | 뜻 |
|---|---|
| `id`, `name` | 식별자, 표시 이름 |
| `fire` | `"direct"` 직사 (조준선으로 바로) / `"indirect"` 곡사 (포물선으로 넘겨 쏨: 유탄·박격포) |
| `slot` | `"primary"` 주화기 (소총·기관총·저격총) / `"secondary"` 보조 (총열 아래 유탄발사기, 대전차 발사관). 병사당 칸마다 1정 (`WEAPON_SLOTS`) |
| `ammo` | 쓰는 탄약 id |
| `range` | 유효사거리 (m) |
| `magazine` | 한 번 장전하는 탄 수 (탄창·탄띠·1발) |
| `mass` | 무게 (kg, 탄 제외) |
| `dispersion` | 산포 (mrad, 표준편차): 다 조준하고 엎드려 쏠 때. 곡사는 사거리 대비 탄착 오차 |
| `baseAimTime` | 기준 조준 시간 (초): 다 조준하는 데 걸리는 시간. 사격 명령의 조준 계수(`FIRE_ORDER.*.aimCoef`)를 곱해 쓴다 |
| `rof` | 발사 속도 (발/분). 점사 안에서 한 틱(0.25초)에 `max(1, round(rof / 60 × 0.25))` 발 |
| `burst` | 제압사격 점사 한 번에 당기는 발 수 (2발 이상이면 ± 1) |
| `reload` | 재장전 시간 (초) |
| `soundRange` | 총성(발사음)이 들리는 거리 (m). 총구에서 크기 1, 이 거리에서 0 (#35, [../calc/rates.md](../calc/rates.md) "듣기"). 추정값: 소총 1000, 기관총 1200, 저격총 1500, 유탄발사기 150, RPG 600 |

## 탄약 `Ammo` (`kind: "ammo"`)

| 필드 | 뜻 |
|---|---|
| `id`, `name` | 식별자, 표시 이름 |
| `caliber` | 구경 (표시용) |
| `mass` | 한 발 무게 (kg) |
| `penetration` | 관통력 (mm 균질압연강판 상당, 근거리) |
| `explosive` | 폭발 여부 |
| `blastRadius` | 폭발 살상 반경 (m). 폭발하지 않으면 0 |
| `casualtyRadius` | 사상 반경 (m, 선택, #31). 살상 반경 너머 이 거리까지 파편이 낮은 확률(`FIRE.blastTail`)로 다친다. 없으면 살상 반경까지만. K200 130 (FM 3-22.31, 꼬리 모양은 추정) |
| `armingDist` | 장전 거리 (m, 선택, #31). 쏜 자리에서 이보다 가까이 떨어진 탄은 터지지 않는다(불발). 없으면 바로 터진다. 40mm 14, PG-7V 8 (추정 선택, 범위는 교범·신관 규격) |
| `suppressionRadius` | 제압 반경 (m). 직사는 탄도선(총구 → 탄착점) 주변, 폭발은 탄착점 주변. 소총탄은 구경이 클수록 넓다: 5.56mm 3, 7.62×39·7.62×54R 6 (#23, 2차 출처) |
| `suppressionCoef` | 구경 계수 (선택, 없으면 1). 근탄 스트레스에 곱한다. 7.62mm 0.6 (#23, 추정: 표 5-7 의 M16:M60 = 35:43 에 맞춤) |
| `damage` | 상처 위력 (소총탄 ≈ 50 기준). 클수록 같은 부위도 더 심하게 다친다 (부상 정도 확률을 무거운 쪽으로 민다, [soldier.md](soldier.md) "부상"). 폭발 파편은 살상 반경 끝에서 × 0.4 |
| `soundRange` | 폭발음이 들리는 거리 (m). 탄착점에서 크기 1, 이 거리에서 0. 폭발하지 않으면 0 (#35). 추정값: 40mm 유탄 1000, PG-7V 1200 |

## 수류탄 `Grenade` (`kind: "grenade"`)

| 필드 | 뜻 |
|---|---|
| `id`, `name`, `mass` | 식별자, 표시 이름, 한 발 무게 (kg) |
| `fuseMin`, `fuseMax` | 신관 지연 범위 (초). 던진 틱에 이 범위에서 정수 틱으로 고른다 |
| `throwRange` | 평균 병사가 서서 던지는 거리 (m). 자세 `THROW.rangeCoef`·하중에 따라 줄어든다 |
| `dispersion` | 던진 자리 산포 (mrad, 표준편차): 던지는 거리에 비례 |
| `basePrepTime` | 기준 투척 준비 시간 (초): 서서 안전핀을 뽑고 던지기까지 |
| `blastRadius`, `suppressionRadius`, `damage`, `soundRange` | 탄약과 같은 뜻 (폭발 모형 `explode` 를 같이 쓴다) |

지닌 수류탄은 `loadout` 의 `qty` (발 수). `grenadeIn(loadout, catalog, id?)` = 수량이 1 이상인 수류탄. 던질 수 있는 거리·식은 [../calc/fire.md](../calc/fire.md) §5a.

함수: `weaponIn(loadout, catalog, slot)` = 칸에 든 화기, `roundsOf(loadout, ammo)` = 지닌 탄 수(장전 탄 포함), `initialLoaded` = 처음 장전 (장전 수와 지닌 탄 중 작은 값). 사격 판정은 [../calc/fire.md](../calc/fire.md).

## 장구 `Gear` (`kind: "gear"`)

싸우는 데 쓰지 않는 휴대품 묶음 (방탄모·방탄복·전투조끼·수통 등). 하중(`Soldier.load`)에만 들어간다.

| 필드 | 뜻 |
|---|---|
| `id`, `name` | 식별자, 표시 이름 |
| `mass` | 무게 (kg) |
| `note` | 무엇이 들었는지 (선택) |

| 장구 | 무게 | 내용 (추정, 군복·전투화·빈 탄창 제외) |
|---|---|---|
| `rok-kit` 국군 개인 전투장구 | 15 kg | 방탄모·방탄복(방탄판 포함)·전투조끼·수통 2·방독면·구급낭 |
| `kpa-kit` 북한군 개인 전투장구 | 6 kg | 철모·탄입대·수통·방독면·잡낭 (방탄복 없음) |

## 무전기 `Radio` (`kind: "radio"`, #45)

무전기는 장비(무게·휴대)다. 같은 그물에 맞춘 무전기끼리 거리 안에서 통신 선이 이어진다 ([comms.md](comms.md)). 값은 모두 `추정`, 근거는 `docs/research/45-59-comms.md` §3·§6.

| 필드 | 뜻 |
|---|---|
| `id`, `name`, `mass` | 식별자, 표시 이름, 무게 (kg) |
| `class` | `handheld`(워키토키) / `backpack`(배낭 무전기). 통신 선 수단 이름이 된다 |
| `r50`, `rmax`, `k` | 알아듣는 비율 1 / (1 + (d / `r50`)^`k`), `rmax` 이상은 0 |
| `nets` | 한 대가 동시에 연결해 둘 수 있는 그물 수 |
| `baseDelay` | 기준 보고 시간 (초) |

| 무전기 | 무게 | `r50` | `rmax` | `k` | `nets` | `baseDelay` |
|---|---|---|---|---|---|---|
| `walkie` 휴대 무전기 | 0.84 kg (PRC-148, 2차) | 800 m | 1.6 km | 4 | 1 | 4초 |
| `backpack-radio` 배낭 무전기 | 10 kg (추정) | 6 km | 12 km | 4 | 2 | 6초 |

어느 그물에 맞췄는지는 `LoadoutItem.nets`(그물 이름 목록, 무전기 한 대의 `nets` × 수량까지만 셈). 없으면 어느 그물에도 닿지 않는다.

## 줍기 (#8)

쓰러진 병사의 `loadout`(화기·탄약·장구 모두)을 `collect` 명령 또는 스스로 줍기로 가져올 수 있다. 규칙은 [action.md](action.md) `collect`. 화기 칸(`WEAPON_SLOTS`)이 차 있으면 화기는 맞바꾼다.

## 보급소 · 건네기 (#38)

- **보급소** `Cache { id, side, x, y, loadout }` ([world.md](world.md) `World.caches`): 시나리오 JSON 의 `caches: [{ side, x, y, loadout: [{ item, qty }] }]` 로 둔다 (탄약은 발 수). `side` 진영만 위치를 알아 `pickup` 으로 줍고, 스냅샷에도 그 진영 것만 (남은 게 있을 때) 담긴다. 줍기는 쓰러진 전우 줍기와 같은 `planTake`·시간. 경계·건드린 흔적(8-64)은 범위 밖.
- **호환 탄**: `equipment.json` 의 화기 `ammo` 와 탄약 `id` 가 같아야 쓴다 (5.56 vs 7.62). 쓸 화기가 없는 탄은 줍지도, 건네받지도 못한다.
- **건네기** `give` 명령: 같은 편 전우에게 탄·장구(화기 제외)를 건넨다. 규칙·시간은 [action.md](action.md) `give`/`receive`. 탄은 발당 `mass` 만 센다 (탄창 몸체·링크 질량은 안 더함).

## 현재 목록

국군 화기 제원은 나무위키 기준 (2026-10-15 확인, 공식 자료로 재확인 필요). K201 유효사거리 350m 는 지역표적 기준 (점표적 150m), K15 무게는 조준경 제외 (장착 시 8.4kg).

| 화기 | 사격 | 칸 | 유효사거리 m | 장전 | 무게 kg | 산포 mrad | 조준 초 | 발/분 | 점사 | 재장전 초 | 쓰는 편제 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| K2 소총 | 직사 | 주 | 600 | 30 | 3.26 | 1.5 | 1 | 700 | 3 | 3 | 국군 |
| K201 유탄발사기 | 곡사 | 보조 | 350 | 1 | 1.62 | 15 | 2 | 5 | 1 | 3 | 국군 |
| K15 경기관총 | 직사 | 주 | 800 | 200 | 7.1 | 2.5 | 1.5 | 800 | 6 | 8 | 국군 |
| AK 자동보총 | 직사 | 주 | 400 | 30 | 3.8 | 2 | 1 | 600 | 3 | 3 | 북한군 |
| G-25 유탄발사기 | 곡사 | 보조 | 400 | 1 | 1.5 | 18 | 2 | 5 | 1 | 3 | 북한군 |
| RPD 경기관총 | 직사 | 주 | 800 | 100 | 7.4 | 2.8 | 1.5 | 700 | 6 | 8 | 북한군 |
| RPG-7 대전차 발사관 | 직사 | 보조 | 300 | 1 | 6.3 | 3 | 2.5 | 4 | 1 | 6 | 북한군 |
| SVD 저격보총 | 직사 | 주 | 800 | 10 | 4.3 | 0.8 | 2 | 30 | 1 | 3 | 북한군 |

| 탄약 | 쓰는 화기 | 한 발 kg | 관통 mm | 폭발 반경 m | 제압 반경 m | 위력 |
|---|---|---|---|---|---|---|
| 5.56mm K100 보통탄 | K2, K15 | 0.012 | 10 | — | 3 | 50 |
| 7.62×39mm 보통탄 | AK, RPD | 0.016 | 8 | — | 4 | 55 |
| 7.62×54mmR 저격탄 | SVD | 0.022 | 12 | — | 5 | 70 |
| 40mm K200 고폭이중목적탄 | K201 | 0.23 | 50 | 5 | 10 | 60 |
| 40mm VOG-25 고폭 유탄 | G-25 | 0.25 | 0 | 6 | 10 | 60 |
| PG-7V 대전차 고폭탄 (85mm) | RPG-7 | 2.2 | 260 | 3 | 8 | 90 |

## 추가하는 법
[`content/equipment.json`](../../content/equipment.json) 의 `items` 에 한 줄 넣는다. 화기는 `slot` 을 정하고, `ammo` 가 가리키는 탄약도 있어야 한다 ([`tools/src/content.test.ts`](../../packages/tools/src/content.test.ts) 가 검사).
화기 없이 던지거나 다른 성질이 필요한 장비(수류탄이 그렇게 들어왔다)는 `kind` 를 늘리는 쪽으로 (지금은 `weapon`·`ammo`·`grenade`·`gear`·`radio` 다섯).

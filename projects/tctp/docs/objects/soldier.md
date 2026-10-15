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
| `size` | `BodySize` | 몸 크기 (m)·몸무게 (kg) |
| `loadout` | `LoadoutItem[]` | 휴대 장비 (편제 공통 장구 `kit` + 직책별) |
| `load` | number | 하중 (kg) = `loadOf(loadout)`. 편성 때 계산, 탄을 쓰면 줄인다 |
| `loaded` | `Record<WeaponSlot, number>` | 화기 칸별 장전된 탄 수 (`loadout` 의 탄 수에 포함). 쏘면 둘 다 1 씩 준다 |
| `posture` | `"stand" \| "crouch" \| "prone"` | 자세: 서기 / 앉아·무릎 / 엎드려 |
| `status` | `SoldierStatus` | 상태 (아래). 매 틱 `updateBody` 가 정한다 |
| `wounds` | `Wound[]` | 부상 목록 (아래). 맞을 때마다 하나씩 쌓인다 |
| `blood` | number | 혈액량 (mL, 처음 5000). 출혈로 준다 |
| `stress` | number | 스트레스 0~100. 화력에 눌린 정도 |
| `threatTick` | number \| null | 마지막으로 위협(근탄·피탄·폭발·전우 피격)을 받은 틱. 조용해진 뒤에야 스트레스가 풀린다 |
| `nearMisses` | number[] | 최근 `volumeWindow`(3초) 안 근탄 틱들. 몰아 날아온 탄일수록 근탄 하나가 더 누른다 ([rates.md](rates.md)) |
| `stressLevel` | `StressLevel` | 심리 단계 (아래). `stress` 와 이전 단계에서 정해진다 |
| `order` | `{tick, cmd} \| null` | 혼란·위축 중 받아 둔 명령. `tick` 이 되면 적용 |
| `stamina` | number | 지구력 0~100 |
| `x`, `y` | number | 위치 (m). 원점 = 지도 북서쪽, x 동쪽, y 남쪽 |
| `facing` | number | 몸이 향한 방향 (이동·사격 방향), 화면 라디안 (0 = 동, 시계방향). 시나리오에서는 방위각(도)으로 주고 `bearingToFacing` 으로 바꾼다 |
| `look` | number | 눈이 보는 방향 (화면 라디안). 탐지 시야각(`fovFactor`)은 이것으로 잰다. 아래 "경계 (시선)" |
| `lookAim` | number | 눈이 돌아가는 목표 방향. `look` 이 매 틱 이쪽으로 따라간다 |
| `lookTick` | number | 다음에 볼 곳을 고를 틱 |
| `glance` | `{ tick, dir } \| null` | 직사 탄이 스쳐 돌아볼 예정 (tick 에 dir 쪽으로) |
| `action` | `Action \| null` | 지금 하는 행동. 없으면 대기 ([action.md](action.md)) |

## 몸 상태 (`soldier.ts`)

수치는 모두 이름 붙은 상수(`POSTURE_HEIGHT`, `BASE_SPEED`, `RUSH_SPEED`, `LOAD`, `STAMINA`, `STRESS`, `WOUND`)이고 대략값이다.
늘고 주는 양(스트레스 증감·지구력 소모와 회복·출혈)과 확률 전환은 [rates.md](rates.md) (`RATES`)에 따로 모아 두었다. 여기에는 문턱과 그 결과만 적는다.

### 상태 `SoldierStatus`
우선순위: `dead` 사망 > `incapacitated` 무력화(부상) > `panicked` 패닉(심리적 무력화) > `suppressed` 제압 > `reloading` 재장전 > `firing` 사격 > `resting` 휴식 > `moving` 이동 > `idle` 정지.
위협 인지·혼란은 이동·사격과 함께 일어나므로 `status` 에 넣지 않고 `stressLevel` 로 본다.
`firing` = 사격 행동 중 (조준 포함), `reloading` = 재장전 행동 중, `resting` = 휴식 행동 중. 이동사격(걸으며 쏨)과 약진은 `moving`.

| 상태 | 조건 | 효과 |
|---|---|---|
| `dead` | 머리 치명상, 또는 피를 50% 넘게 잃음 | 엎드려 쓰러짐, 명령·행동·관측 없음 |
| `incapacitated` | 급소(머리·가슴·복부) 중상 이상, 또는 피를 40% 넘게 잃음 (실신) | 위와 같음 (살아는 있음, 출혈은 계속) |
| `panicked` | `stressLevel = broken` | 엎드려 웅크림, 명령·관측 없음, 행동 버림 |
| `suppressed` | `stressLevel = suppressed` | 엎드림, 행동이 멈춤 (남겨 두었다가 풀리면 이어 감) |
| `moving` | 이번 틱에 움직임 | |
| `idle` | 그 밖 | |

### 부상 `Wound` (`wound.ts`)
체력 숫자는 없다. 맞을 때마다 부상 하나를 굴려 `wounds` 에 쌓는다: `{ part, severity, bleed (mL/초), tick }`.
- 부위 `part`: `head`, `torso`, `abdomen`, `leftArm`, `rightArm`, `leftLeg`, `rightLeg`. 급소(`WOUND.vital`) = 머리·가슴·복부.
- 정도 `severity`: `graze` 찰과 / `light` 경상 / `severe` 중상 / `critical` 치명. 확률표(`WOUND.bullet`, `WOUND.fragment`)에서 부위별로 굴린다.
  - **총탄이 급소에 맞으면 찰과·경상이 없다** → 언제나 중상 이상이라 바로 무력화된다. 머리 치명상(0.9)은 즉사하고, 가슴·복부는 처치가 없으면 출혈로 수 분 안에 죽는다.
  - 파편(폭발)은 급소도 가볍게 다칠 수 있다.
  - 탄 위력(`ammo.damage`, 소총탄 50 기준)이 크면 확률표를 무거운 쪽으로 민다: 균등 난수 u 를 u^(50/위력) 로 바꿔 표에 넣는다.
- 부위 기능 = 그 부위의 가장 심한 부상: 찰과 → 멀쩡, 경상 → 저하, 중상·치명 → 못 씀 (`partLevel`).
- 출혈 속도와 혈액 문턱은 [rates.md](rates.md) "혈액".

| 부위 | 저하 (경상) | 못 씀 (중상·치명) |
|---|---|---|
| 팔 (`armUse`) | 산포 ×1.8, 조준 시간 ×1.4, 재장전 ×1.8 | 한 팔: 산포 ×4, 조준 ×2, 재장전 ×3 (한 손으로 받침). 두 팔: 사격·재장전 불가 |
| 다리 (`legUse`) | 속도 ×0.5, 약진 불가 | 한쪽이라도: 자세와 상관없이 포복 속도 |
| 급소 | (총탄은 없음) | 무력화 |

- 피를 30% 넘게 잃으면 약해진다 (`isWeak`): 속도 ×0.6, 산포 ×1.5, 조준 시간 ×1.3, 약진 불가.
- 맞으면 스트레스가 오르고, 부상 정도에 따른 확률로 바로 패닉(쇼크)에 빠진다. 곁의 전우가 쓰러지면 그 전우들의 스트레스도 오른다 ([rates.md](rates.md)).
- 부상 무력화(`incapacitated`)와 심리적 무력화(`panicked`)는 서로 다른 상태다. 앞은 몸이 꺾인 것이고 뒤는 의지가 꺾인 것이다. 무력화가 우선한다.

### 스트레스 `stress` 와 심리 단계 `stressLevel`
근탄·피탄·폭발·전우 피격이 올리고, 조용해지면 형편(엄폐·전우·출혈)에 따라 흔들리며 준다. 양과 확률은 [rates.md](rates.md) "스트레스". 상태를 정한 뒤 줄어든다.
교범의 화력 심리 효과 순서(위협 → 혼란·위축 → 제압 → 무력화)를 따른다.

| 단계 | 스트레스 | 교범 | 효과 |
|---|---|---|---|
| `calm` 평상 | < 20 | | |
| `alert` 위협 인지 | ≥ 20 | 위협 지각·경각 | 서서 멈춰 있으면 앉는다. 발견 ×1.2. 판단·반격 정상 |
| `shaken` 혼란·위축 | ≥ 45 | 혼란·위축 (제압 직전) | 명령을 `orderDelay`(2초, + 반응 시간) 뒤에 따른다 (OODA 지연). 발견 ×0.6. 반격 정확도·빈도 감소는 사격 판정에서 |
| `suppressed` 제압 | ≥ 70 | 제압 | 엎드림, 이동 불가, 터널 비전 (발견 ×0.3) |
| `broken` 패닉 | 100 에 닿으면 반드시, 제압 단계에서는 초당 확률로. 피격 쇼크로도 빠진다. `rally`(30) 아래에서 초당 확률로 풀림 | 무력화 (심리) | 명령 거부·웅크림·관측 불가. 도주·항복은 AI 가 생기면 |


### 이동 속도 `speedOf(s, gait)` (m/s, 지형 배율 전)
`걸음 기본 속도 × 하중 배율 × 지구력 배율 × 다리 배율 × 실혈 배율`
- 걸음 `gait` ([action.md](action.md)): `walk` 걷기 = 자세별 속도 (서기 1.4 (보통 걸음 ≈ 5 km/h), 앉아 0.8, 포복 0.25). `rush` 약진 = `RUSH_SPEED` 3.5 (서서 뛴다). 다리를 다쳤거나 약해졌으면 약진하지 못해 선 걸음으로 간다.
- 하중 배율: 비율 r = 하중 ÷ 몸무게. `max(0.4, 1 − 0.6 × max(0, r − 0.15))`. 예) 국군 소총수 20.8kg(r 0.30) → ×0.91 = 걷기 1.27 · 약진 3.2 m/s, 기관총 사수 29kg(r 0.41) → ×0.84 = 걷기 1.17 m/s.
- 지구력 배율: 50 이상이면 1, 아래로 내려가면 0 일 때 0.5 까지 선형.
- 다리·실혈 배율: 위 "부상".
- 실제 한 틱 이동 = `speedOf × 선 칸의 move 배율 × 걸음 흔들림 × DT(0.25초)` (이동사격이면 × `MOVE.fireSpeed` 0.5).

### 지구력 `stamina`
- 움직이면 줄고, **휴식** 행동(`rest` 명령) 중에만 제대로 회복한다 (그냥 멈춰 조준·사격·대기하면 아주 조금). 휴식은 평온(`calm`)할 때만 시작하고, 위협을 느끼면 그친다 (`canRest`). 걸음은 몇 시간을 버티고 포복은 몇 분, 약진은 몇 십 초면 지친다. 양은 [rates.md](rates.md) "지구력".

### 자세 `posture`
- 몸 높이 = `size.h × POSTURE_HEIGHT` (서기 1, 앉아 0.6, 엎드려 0.2). 시야의 눈높이·피탄 높이가 이 값을 쓴다 (엎드리면 덜 보이고 덜 본다).
- 바꾸는 명령: `{ kind: "posture", ids, posture }`. 제압·패닉·무력화되면 저절로 엎드리고, 위협을 느끼면 서서 멈춘 병사는 앉는다. 약진하는 동안은 서고, 도착하면 엎드린다.
- 엎드린 몸은 바라보는 방향으로 길게 눕는다 (발 → 머리 = `facing`). 피탄 판정이 이 방향을 쓴다 ([action.md](action.md) "사격 판정").

### 경계 (시선) `look` — `scan.ts`
- 몸 방향(`facing`)과 눈 방향(`look`)이 따로다. 매 틱 행동 다음, 탐지 전에 `updateScan` 이 정한다 (튜닝 `SCAN`). 난수는 시선 전용 `World.lookRng` 만 써서 사격·피해 난수 흐름을 흔들지 않는다.
- 볼 곳(`lookAim`)을 고르면 눈은 고개를 돌리듯 따라간다: 매 틱 남은 각의 `SCAN.ease`(40%), 최고 `SCAN.turnMax`(360°/초).
- 경계 구역: 같은 진영·같은 분대 안 id 순서로 맨 앞 = 정면, 가운데 = 좌·우전방(±`SCAN.flank` 45°) 번갈아, 맨 뒤 = 후방 (`sectorOf`). 맨 뒤도 눈을 옮길 때 `SCAN.rearShare`(40%)만 뒤를 보고 나머지는 앞을 본다.
- 구역 중심 ± `SCAN.sector`(50°) 안을 `SCAN.dwell`(1.5초 ± 60%)마다 이웃한 곳(± `SCAN.step` 35°)으로 훑는다 (이동 중·대기 중 모두).
- 아는 적이 있으면 눈을 옮길 때마다 `SCAN.threat`(85%) 확률로 가장 가까운 아는 적 쪽(± 15°)을 본다.
- 직사 탄(총탄·로켓)이 스쳐 위협을 받으면 반응 시간 `SCAN.reaction`(0.3~1초) 뒤, 총소리로 어림한 쏜 쪽(표준편차 `SCAN.heardError` 25° 어긋남)을 `SCAN.fireDwell`(3초) 본다. 곡사(유탄 등)는 쏜 곳을 모르고 폭발로만 느끼므로 돌아보지 않는다.
- 쏘는 중(사격·이동사격)이면 눈은 겨누는 쪽(= `facing`)에 붙어 있다.
- 분대원이 혼자면 구역이 없어 정면(`facing`)만 본다 (돌아보기는 한다).
- 밸런스: 접적 시나리오(bd1, 적이 정면) 100판 첫 발견 평균이 정면만 볼 때와 비슷하다 (아군 5.85→5.89초, 적 2.46→2.49초). 대신 옆·뒤 적을 찾는다.

## 몸 크기 `BodySize`

| 필드 | 뜻 | 기본값 (`BODY`, `soldier.ts`) |
|---|---|---|
| `w` | 가로 (어깨 폭) | 0.5 m |
| `d` | 세로 (가슴 두께) | 0.3 m |
| `h` | 높이 (선 자세 키) | 1.75 m |
| `mass` | 몸무게 | 70 kg |

- 지금 쓰는 곳: 시야 — 눈높이 = 자세별 몸 높이 × `VISION.eyeRatio(0.93)`, 겨냥 높이 = 자세별 몸 높이 × `VISION.aimRatio(0.7)` ([world.md](world.md)). 하중 비율 — `mass`.

## 휴대 장비 `LoadoutItem`

| 필드 | 뜻 |
|---|---|
| `item` | 장비 id ([equipment.md](equipment.md)) |
| `qty` | 수량. 화기는 정 수, 탄약은 발 수 |

- 예: 국군 유탄수 `[{rok-kit,1}, {k2,1}, {k201,1}, {556-k100,210}, {40-k200,12}]` (`rok-kit` 은 편제 공통 장구).
- `weaponsOf(loadout, catalog)` 로 화기만 뽑는다. `checkLoadout` 은 없는 장비·탄약·0 이하 수량을 오류로 돌려준다.

### 휴대 한도
- 화기 칸: 주화기(`primary`) 1정, 보조(`secondary`) 1정 (`WEAPON_SLOTS`, `equipment.ts`). 탄약·장구는 칸 없이 무게로만 제한.
- 무게: 공통 장구 + 직책 장비 합이 몸무게 × `LOAD.maxRatio`(0.7, 49kg) 를 넘으면 오류 (`checkCarry`). 편제는 교범 접근하중 상한 × `LOAD.limitRatio`(0.45, 31.5kg) 안이어야 한다 (콘텐츠 테스트).
- `checkOrg` 가 구성원마다 둘 다 검사한다. 지금 가장 무거운 구성원도 45% 안.

## 아직 없는 것
응급처치(지혈대·압박, 리더 로직과 함께), 방호구(방탄모·방탄복이 부상을 줄이는 것), 패닉 중 도주·항복, 사기(분대 단위로 둘 예정), 빈 탄창 무게, 적에게 보이는 상태(쓰러짐 등).
상태 필드를 늘리면 `stateHash`(`replay.ts`)에도 섞어야 결정성 테스트가 검사한다.

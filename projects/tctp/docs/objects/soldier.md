# 병사 `Soldier`

아군·적 모두 같은 객체. 진영과 장비만 다르다. 코드: [`packages/sim/src/core/types.ts`](../../packages/sim/src/core/types.ts).
시나리오의 편제에서 `buildSoldiers` 가 만든다 ([scenario.md](scenario.md)). 직접 JSON 으로 쓰지 않는다.

| 필드 | 타입 | 뜻 |
|---|---|---|
| `id` | number | 월드 안 번호. 0 부터 부대 순서대로 (`world.soldiers[id]`) |
| `side` | `"blue" \| "red"` | 진영 |
| `name` | string | 이름. [`content/names.json`](../../content/names.json) 의 성 + 이름을 시나리오 시드로 골라 부대 안에서 겹치지 않게 |
| `role` | string | 직책 (편제의 `role`: 분대장, 기관총 사수 …) |
| `squad` | string | 소속 분대 = 부대명 (`ForceSpec.name`). 최소 명령 단위 |
| `team` | string | 소속 조 = `"<부대명> <조 이름>"` (예: `1분대 2조`) |
| `size` | `BodySize` | 몸 크기 (m)·몸무게 (kg) |
| `loadout` | `LoadoutItem[]` | 휴대 장비 (편제 공통 장구 `kit` + 직책별) |
| `load` | number | 하중 (kg) = `loadOf(loadout)`. 편성 때 계산, 탄을 쓰면 줄인다 |
| `loaded` | `Record<WeaponSlot, number>` | 화기 칸별 장전된 탄 수 (`loadout` 의 탄 수에 포함). 쏘면 둘 다 1 씩 준다 |
| `posture` | `"stand" \| "crouch" \| "prone"` | 자세: 서기 / 앉아·무릎 / 엎드려. 바꾸는 중이면 바꾸기 전 자세 |
| `shift` | `{ to, left, total } \| null` | 자세를 바꾸는 중 (#51): 목표 자세, 남은 틱, 전체 틱. 없으면 null. 도중에는 몸 높이가 두 자세 높이 사이를 선형으로 오가고, 사격을 못 하며, 포복 속도로만 움직인다 |
| `status` | `SoldierStatus` | 상태 (아래). 매 틱 `updateBody` 가 정한다 |
| `wounds` | `Wound[]` | 부상 목록 (아래). 맞을 때마다 하나씩 쌓인다 |
| `blood` | number | 혈액량 (mL, 처음 5000). 출혈로 준다 |
| `stress` | number | 스트레스 0~100. 화력에 눌린 정도 |
| `threatTick` | number \| null | 마지막으로 위협(근탄·피탄·폭발·전우 피격)을 받은 틱. 조용해진 뒤에야 스트레스가 풀린다 |
| `heardTick` | number \| null | 마지막으로 적 총성·폭발음을 들은 틱 (#35, [`perception/hearing.ts`](../../packages/sim/src/perception/hearing.ts)). 회복을 미루지는 않는다 |
| `nearMisses` | number[] | 최근 `volumeWindow`(3초) 안 근탄 틱들. 몰아 날아온 탄일수록 근탄 하나가 더 누른다 ([../calc/rates.md](../calc/rates.md)) |
| `stressLevel` | `StressLevel` | 심리 단계 (아래). `stress` 와 이전 단계에서 정해진다 |
| `order` | `{tick, cmd} \| null` | 혼란·위축 중 받아 둔 명령. `tick` 이 되면 적용 |
| `stamina` | number | 지구력 0~100 |
| `winded` | number | 숨참: 지구력 결손 중 막 움직여 쓴 몫 (0 ~ `RATES.stamina.windedMax` 25). 멈추면 나머지(피로)보다 훨씬 빨리 돌아온다 |
| `x`, `y` | number | 위치 (m). 원점 = 지도 북서쪽, x 동쪽, y 남쪽 |
| `facing` | number | 몸이 향한 방향 (이동·사격 방향, 멈춰 있을 때 위협 쪽으로 돌아섬), 화면 라디안 (0 = 동, 시계방향). 시나리오에서는 방위각(도)으로 주고 `bearingToFacing` 으로 바꾼다 |
| `look` | number | 눈이 보는 방향 (화면 라디안). 탐지 시야각(`fovFactor`)은 이것으로 잰다. 아래 "경계 (시선)" |
| `lookAim` | number | 눈이 돌아가는 목표 방향. `look` 이 매 틱 이쪽으로 따라간다 |
| `lookTick` | number | 다음에 볼 곳을 고를 틱 |
| `glance` | `{ tick, dir } \| null` | 직사 탄이 스쳐 돌아볼 예정 (tick 에 dir 쪽으로) |
| `bodyAim` | `{ dir, started } \| null` | 몸을 돌려 향할 방향 (위협이 고개 한계 밖일 때). started = 고개가 한계 가까이 돌아 몸이 돌기 시작함 (그 뒤로는 끝까지 돈다) |
| `action` | `Action \| null` | 지금 하는 행동. 없으면 감시 ([action.md](action.md)) |
| `restTick` | `number \| null` | 할 일 없이 평온한 감시 병사가 저절로 쉬기 시작할 틱 (아래 "기본 상태"). 조건이 깨지면 null |

## 몸 상태 ([`body/soldier.ts`](../../packages/sim/src/body/soldier.ts))

수치는 모두 이름 붙은 상수(`POSTURE_HEIGHT`, `BASE_SPEED`, `RUSH_SPEED`, `LOAD`, `STAMINA`, `STRESS`, `WOUND`)이고 대략값이다.
늘고 주는 양(스트레스 증감·지구력 소모와 회복·출혈)과 확률 전환은 [../calc/rates.md](../calc/rates.md) (`RATES`)에 따로 모아 두었다. 여기에는 문턱과 그 결과만 적는다.

### 상태 `SoldierStatus`
우선순위: `dead` 사망 > `incapacitated` 무력화(부상) > `panicked` 패닉(심리적 무력화) > `suppressed` 제압 > `reloading` 재장전 > `firing` 사격 > `resting` 휴식 > `moving` 이동 > `watching` 감시.
"대기"(아무것도 아님) 상태는 없다 (#25). 병사는 늘 기본 상태 넷 중 하나다: 휴식 `resting` · 이동 `moving` · 교전 `firing`/`reloading` (제압·패닉 포함) · 감시 `watching`.

### 기본 상태 전환 (`updateBaseState`, [`body/soldier.ts`](../../packages/sim/src/body/soldier.ts), 튜닝 `BASE_STATE`)
- 할 일(행동)·받을 명령이 없고 평온(`calm`)하고 교전이 없으면(`combatFloor = 0`: 아는 적이 500m 안에 없고 60초 안에 적 소리를 못 들음) 감시 상태로 `restTick` 을 정해 두고, 그 틱까지 그대로면 저절로 휴식 행동에 든다. 지연 = `baseRestDelay`(120초) × (1 ± `restDelayVary` 30%) = 84 ~ 156초, `World.stateRng` 로 병사마다 굴려 분대원이 한 틱에 함께 쉬지 않는다. 이동을 마친 병사도 이 규칙으로 감시 → 휴식이 된다.
- 쉬기 시작하면 (명령이든 저절로든) 서 있던 병사는 앉는다 (`crouch`).
- 쉬는 중 평온이 깨지면(근탄·총성) 그 틱에 바로, 교전이 생기면(적을 알게 됨) 반응 시간(0 ~ `VARY.reaction` 1초, `stateRng`) 뒤 휴식을 그치고 감시로 돌아온다.
- 쉬는 병사는 느슨하게 둘러본다: 한 곳 보는 시간 × `SCAN.restDwellCoef`(2), 처음 발견 × `VISION.restObserve`(0.5). 감시·교전은 1.
- 값은 추정이다.

위협 인지·혼란은 이동·사격과 함께 일어나므로 `status` 에 넣지 않고 `stressLevel` 로 본다.
`firing` = 사격 행동 중 (조준 포함), `reloading` = 재장전 행동 중, `resting` = 휴식 행동 중. 이동사격(걸으며 쏨)과 약진은 `moving`.

| 상태 | 조건 | 효과 |
|---|---|---|
| `dead` | 머리 치명상, 또는 피를 50% 넘게 잃음 | 엎드려 쓰러짐, 명령·행동·관측 없음 |
| `incapacitated` | 급소(머리·가슴·복부) 중상 이상, 또는 피를 40% 넘게 잃음 (실신) | 위와 같음 (살아는 있음, 출혈은 계속) |
| `panicked` | `stressLevel = broken` | 엎드려 웅크림, 명령·관측 없음, 행동 버림 |
| `suppressed` | `stressLevel = suppressed` | 엎드림, 행동이 멈춤 (남겨 두었다가 풀리면 이어 감) |
| `reloading` | 재장전 행동 중 | |
| `firing` | 사격 행동 중 (조준 포함) | |
| `resting` | 휴식 행동 중 | 지구력이 제대로 회복 |
| `moving` | 이번 틱에 움직임 | 지구력 소모, 발견되기 쉬움 |
| `watching` | 그 밖 (할 일 없이 깨어 둘레를 살핌) | 경계 구역을 제대로 훑는다 |

### 부상 `Wound` ([`body/wound.ts`](../../packages/sim/src/body/wound.ts))
체력 숫자는 없다. 맞을 때마다 부상 하나를 굴려 `wounds` 에 쌓는다: `{ part, severity, bleed (mL/초), tick, fatal? }`. `fatal` = 총탄 가슴·복부 치명상이 즉사 굴림에 걸림 (`isDead`). 머리 치명상은 `fatal` 없이도 늘 즉사.
- 부위 `part`: `head`, `torso`, `abdomen`, `leftArm`, `rightArm`, `leftLeg`, `rightLeg`. 급소(`WOUND.vital`) = 머리·가슴·복부.
- 정도 `severity`: `graze` 찰과 / `light` 경상 / `severe` 중상 / `critical` 치명. 확률표(`WOUND.bullet`, `WOUND.fragment`)에서 부위별로 굴린다.
  - **총탄이 급소에 맞으면 찰과·경상이 없다** → 언제나 중상 이상이라 바로 무력화된다. 머리 치명상(0.9)은 즉사하고, 가슴·복부는 처치가 없으면 출혈로 수 분 안에 죽는다.
  - 파편(폭발)은 급소도 가볍게 다칠 수 있다.
  - 탄 위력(`ammo.damage`, 소총탄 50 기준)이 크면 확률표를 무거운 쪽으로 민다: 균등 난수 u 를 u^(50/위력) 로 바꿔 표에 넣는다.
- 부위 기능 = 그 부위의 가장 심한 부상: 찰과 → 멀쩡, 경상 → 저하, 중상·치명 → 못 씀 (`partLevel`).
- 출혈 속도와 혈액 문턱은 [../calc/rates.md](../calc/rates.md) "혈액".

| 부위 | 저하 (경상) | 못 씀 (중상·치명) |
|---|---|---|
| 팔 (`armUse`) | 산포 ×1.8, 조준 시간 ×1.4, 재장전 ×1.8 | 한 팔: 산포 ×4, 조준 ×2, 재장전 ×3 (한 손으로 받침). 두 팔: 사격·재장전 불가 |
| 다리 (`legUse`) | 속도 ×0.5, 약진 불가 | 한쪽이라도: 자세와 상관없이 포복 속도 |
| 급소 | (총탄은 없음) | 무력화 |

- 피를 30% 넘게 잃으면 약해진다 (`isWeak`): 속도 ×0.6, 산포 ×1.5, 조준 시간 ×1.3, 약진 불가.
- 맞으면 스트레스가 오르고, 부상 정도에 따른 확률로 바로 패닉(쇼크)에 빠진다. 곁의 전우가 쓰러지면 그 전우들의 스트레스도 오른다 ([../calc/rates.md](../calc/rates.md)).
- 부상 무력화(`incapacitated`)와 심리적 무력화(`panicked`)는 서로 다른 상태다. 앞은 몸이 꺾인 것이고 뒤는 의지가 꺾인 것이다. 무력화가 우선한다.

### 스트레스 `stress` 와 심리 단계 `stressLevel`
근탄·피탄·폭발·전우 피격이 올리고, 조용해지면 형편(엄폐·전우·출혈)에 따라 흔들리며 준다. 양과 확률은 [../calc/rates.md](../calc/rates.md) "스트레스". 상태를 정한 뒤 줄어든다.
교범의 화력 심리 효과 순서(위협 → 혼란·위축 → 제압 → 무력화)를 따른다.

| 단계 | 스트레스 | 교범 | 효과 |
|---|---|---|---|
| `calm` 평상 | < 20 | | |
| `alert` 위협 인지 | ≥ 20 | 위협 지각·경각 | 서서 멈춰 있으면 앉는다. 발견 ×1.2. 판단·반격 정상 |
| `shaken` 혼란·위축 | ≥ 45 | 혼란·위축 (제압 직전) | 명령을 `orderDelay`(2초, + 반응 시간) 뒤에 따른다 (OODA 지연). 발견 ×0.6. 반격 산포 ×1.8·조준 시간 ×1.6 ([../calc/fire.md](../calc/fire.md)) |
| `suppressed` 제압 | ≥ 70 | 제압 | 엎드림, 이동 불가, 터널 비전 (발견 ×0.3) |
| `broken` 패닉 | 100 에 닿으면 반드시, 제압 단계에서는 초당 확률로 (근탄만으로는 90 까지만 올라 100 에 닿지 않는다, #23). 피격 쇼크로도 빠진다. `rally`(30) 아래에서 초당 확률로 풀림 | 무력화 (심리) | 명령 거부·관측 불가. 꺾이는 순간 웅크림·도주·항복 중 하나를 고른다 ([action.md](action.md) `panic`) |


#### 분대 교전 목표 분포 (#23)
서로 위치를 알고 상대 분대 중심을 60초 제압하는 교전 (`npm run headless -- 1 --n 30 --sec 60 --mutual [--full]`, bd1 지도 시드 1~30) 에서 병사 끝 상태가 한쪽으로 몰리지 않는 것을 목표로 한다. 근탄이 쌓이면 스트레스가 바로 100 에 닿아 제압 단계를 건너뛰고 패닉으로 갔기 때문에 (한쪽이 반드시 무너지는 쏠림), 근탄 상한 `nearMissCap` 90 을 두어 제압 단계에서 `breakPerSec` 확률로만 패닉하게 했다.
- 목표 (사용자 결정으로 미리 정하지 않음, 민감도로 원인을 찾은 뒤 잡은 값): 어느 편도 전원 패닉이 아니고 (30판 중 0판), 끝 상태가 교전·제압·패닉으로 섞이며, 패닉 비율이 한쪽에 몰리지 않는 것. 정확한 비율은 근거 자료가 없어 정하지 않았다 (추정).
- 전후: 전 `--mutual --full` 청 교전 66% · 제압 0% · 패닉 32%, 적 교전 38% · 제압 0% · 패닉 60% → 후 청 68% · 14% · 17%, 적 30% · 23% · 43%.
- 원인: `breakPerSec` 0.2 도, 피격 쇼크·폭발·전우 쓰러짐을 끈 것도 결과가 거의 안 변했다 (스트레스가 100 에 닿아 제압 단계를 건너뜀). 근탄 15 → 8 도 패닉 비율이 거의 같았다.
- 남은 쏠림: 평지 드릴 `supp-squads` 에서는 먼저 눌린 쪽이 계속 눌려 한 편이 몽땅 패닉하는 판이 시드 40개 중 13개 있다 (지형·엄폐가 없을 때). bd1 지도에서는 0/30.

### 이동 속도 `speedOf(s, gait)` (m/s, 지형 계수 전)
`걸음 기준 속도 × 하중 계수 × 지구력 계수 × 다리 계수 × 실혈 계수`
- 걸음 `gait` ([action.md](action.md)): `walk` 걷기 = 자세별 속도 (서기 1.4 (보통 걸음 ≈ 5 km/h), 앉아 0.8, 포복 0.25). `rush` 약진 = `RUSH_SPEED` 3.5 (서서 뛴다). 다리를 다쳤거나 약해졌으면 약진하지 못해 선 걸음으로 간다.
- 하중 계수는 하중 ÷ 몸무게 0.15 까지 1, 넘으면 줄어든다 (국군 소총수 ×0.91, 기관총 사수 ×0.84). 지구력 계수는 50 아래에서 0 일 때 0.5 까지.
- 식·한 틱 이동 거리·직책별 계산 예는 [../calc/movement.md](../calc/movement.md).

### 지구력 `stamina`
- 움직이면 줄고, **휴식** 행동(`rest` 명령, 또는 할 일 없이 평온하면 저절로) 중에 제대로 회복한다 (그냥 멈춰 조준·사격·감시하면 그 1/4 빠르기). 막 쓴 몫(숨참)은 1~2분에 돌아오지만, 오래 쌓인 피로는 느려 완전히 지친 뒤 다 돌아오려면 50분쯤 걸린다. 휴식은 평온(`calm`)할 때만 시작하고, 위협을 느끼면 그친다 (`canRest`). 걸음은 몇 시간을 버티고 포복은 몇 분, 약진은 몇 십 초면 지친다. 양은 [../calc/rates.md](../calc/rates.md) "지구력".

### 자세 `posture`
- 몸 높이 = `size.h × POSTURE_HEIGHT` (서기 1, 앉아 0.6, 엎드려 0.2). 시야의 눈높이·피탄 높이가 이 값을 쓴다 (엎드리면 덜 보이고 덜 본다).
- 바꾸는 명령: `{ kind: "posture", ids, posture }`. 제압·패닉되면 저절로 엎드리고, 위협을 느끼면 서서 멈춘 병사는 앉는다. 약진하는 동안은 서고, 도착하면 엎드린다. 무력화(쓰러짐)는 바로 엎드리고, 나머지는 모두 시간이 든다 (#51).
- 자세 바꾸기는 바로 되지 않는다: `setPosture` 가 `shift` 를 세우고, 바꾸는 시간이 지난 틱에 `posture` 가 확정된다. 시간은 짐 없는 남자 기준 서기→엎드림 1.0초, 엎드림→서기 1.1초 × 하중·지구력·다리·실혈 계수 ([../calc/movement.md](../calc/movement.md) "자세 바꾸기"). 도중에는 사격(조준 포함)하지 못하고 포복 속도로만 움직이며, 몸은 보이고 맞을 수 있다(높이는 선형 보간). 제압당한 병사는 엎드리라는 명령만 받는다.
- 엎드린 몸은 바라보는 방향으로 길게 눕는다 (발 → 머리 = `facing`). 피탄 판정이 이 방향을 쓴다 ([../calc/fire.md](../calc/fire.md) "맞은 부위").

### 경계 (시선) `look` — [`perception/scan.ts`](../../packages/sim/src/perception/scan.ts)
- 몸 방향(`facing`)과 눈 방향(`look`)이 따로다. 매 틱 행동 다음, 탐지 전에 `updateScan` 이 정한다 (튜닝 `SCAN`). 난수는 시선 전용 `World.lookRng` 만 써서 사격·피해 난수 흐름을 흔들지 않는다.
- 볼 곳(`lookAim`)을 고르면 눈은 고개를 돌리듯 따라간다: 매 틱 남은 각의 `SCAN.ease`(50%), 최고 `SCAN.turnMax`(300°/초).
- 고개는 몸 정면 ± `SCAN.neck`(90°) 안에서만 돈다. 위협 쪽(아는 적·돌아보기)이 그 밖이면 `bodyAim` 을 잡아 멈춰 있는 병사는 고개가 한계에서 `SCAN.bodyLead`(15°) 안쪽까지 먼저 돈 뒤 몸을 돌린다 (`SCAN.bodyTurn` 서기·앉기 240°/초, 엎드려 45°/초). 걷는 중이면 몸은 진행 방향에 묶여 고개만 한계까지 돌린다. 평소 구역 훑기로는 몸을 돌리지 않는다 (맨 뒤의 후방은 고개 한계 + 주변 시야로 본다).
- 경계 구역: 같은 진영·같은 분대 안 id 순서로 맨 앞 = 정면, 가운데 = 좌·우전방(±`SCAN.flank` 45°) 번갈아, 맨 뒤 = 후방 (`sectorOf`). 맨 뒤도 눈을 옮길 때 `SCAN.rearShare`(40%)만 뒤를 보고 나머지는 앞을 본다.
- 구역 중심 ± `SCAN.sector`(50°) 안을 `SCAN.dwell`(1.5초 ± 60%)마다 이웃한 곳(± `SCAN.step` 35°)으로 훑는다 (이동 중·감시 중 모두, 쉬는 중은 보는 시간 × `SCAN.restDwellCoef` 2).
- 아는 적이 있으면 눈을 옮길 때마다 `SCAN.threat`(85%) 확률로 가장 가까운 아는 적 쪽(± 15°)을 본다.
- 직사 탄(총탄·로켓)이 스쳐 위협을 받으면 반응 시간 `SCAN.reaction`(0.3~1초) 뒤, 총소리로 어림한 쏜 쪽(표준편차 `SCAN.heardError` 25° 어긋남)을 `SCAN.fireDwell`(3초) 본다. 곡사(유탄 등)는 쏜 곳을 모르고 폭발로만 느끼므로 쏜 쪽은 돌아보지 않는다.
- 스치지 않고 듣기만 한 적 총성·폭발음(#35)도, 돌아볼 예정이 없으면 소리 크기(1 − 거리/들리는 거리)만큼의 확률로 반응 시간 뒤 가장 큰 소리 쪽(총성은 총구, 폭발음은 폭발점)을 `SCAN.fireDwell` 본다. 어긋남은 `heardError` × (1 + `SCAN.hearFarErrorCoef` 2 × (1 − 크기)) 로 멀수록 크다. 아군 소리는 돌아보지 않는다.
- 쏘는 중(사격·이동사격)이면 눈은 겨누는 쪽(= `facing`)에 붙어 있다.
- 분대원이 혼자면 나눌 조원이 없어 정면 구역(몸 정면 ± `SCAN.sector`)을 맡아 훑는다.
- 상태별: 이동·감시·휴식·재장전 중 모두 같은 규칙으로 (휴식만 느리게) 고개를 훑는다 (혼자여도). 사격 중엔 겨누는 쪽에 고정, 무력화되면 멈춘다. 제압·패닉도 지금은 똑같이 훑는다.
- 걷는 분대 후방 병사가 몸째 뒤돌기·후진하는 것은 아직 없다 (백로그, 교범 확인 예정).
- 고개·몸 돌리는 속도와 볼 곳 고르기 난수는 [../calc/vision.md](../calc/vision.md) "경계 시선", [../calc/random/rolls.md](../calc/random/rolls.md) "경계 시선".
- 밸런스: 접적 시나리오(bd1, 적이 정면) 100판 첫 발견 평균이 정면만 볼 때와 비슷하다 (아군 5.85→5.82초, 적 2.46→2.53초). 대신 옆·뒤 적을 찾는다.

## 몸 크기 `BodySize`

| 필드 | 뜻 | 기본값 (`BODY`, [`body/soldier.ts`](../../packages/sim/src/body/soldier.ts)) |
|---|---|---|
| `w` | 가로 (어깨 폭) | 0.5 m |
| `d` | 세로 (가슴 두께) | 0.3 m |
| `h` | 높이 (선 자세 키) | 1.75 m |
| `mass` | 몸무게 | 70 kg |

- 지금 쓰는 곳: 시야 — 눈높이 = 자세별 몸 높이 × `VISION.eyeRatio(0.93)`, 겨냥 높이 = 자세별 몸 높이 × `VISION.aimRatio(0.7)` ([../calc/vision.md](../calc/vision.md)). 사격 — 총구 높이 `h × 0.85`, 피탄 폭 `w`(선·앉음) / 엎드리면 `h`(옆)·0.7m(정면), 맞은 부위 높이 ([../calc/fire.md](../calc/fire.md)). 하중 비율 — `mass`.

## 휴대 장비 `LoadoutItem`

| 필드 | 뜻 |
|---|---|
| `item` | 장비 id ([equipment.md](equipment.md)) |
| `qty` | 수량. 화기는 정 수, 탄약은 발 수 |

- 예: 국군 유탄수 `[{rok-kit,1}, {k2,1}, {k201,1}, {556-k100,210}, {40-k200,12}]` (`rok-kit` 은 편제 공통 장구).
- `weaponsOf(loadout, catalog)` 로 화기만 뽑는다. `checkLoadout` 은 없는 장비·탄약·0 이하 수량을 오류로 돌려준다.

### 휴대 한도
- 화기 칸: 주화기(`primary`) 1정, 보조(`secondary`) 1정 (`WEAPON_SLOTS`, [`content/equipment.ts`](../../packages/sim/src/content/equipment.ts)). 탄약·장구는 칸 없이 무게로만 제한.
- 무게: 공통 장구 + 직책 장비 합이 몸무게 × `LOAD.maxRatio`(0.7, 49kg) 를 넘으면 오류 (`checkCarry`). 편제는 교범 접근하중 상한 × `LOAD.limitRatio`(0.45, 31.5kg) 안이어야 한다 (콘텐츠 테스트).
- `checkOrg` 가 구성원마다 둘 다 검사한다. 지금 가장 무거운 구성원도 45% 안.

## 아직 없는 것
응급처치(지혈대·압박, 리더 로직과 함께), 방호구(방탄모·방탄복이 부상을 줄이는 것), 사기(분대 단위로 둘 예정), 빈 탄창 무게, 적에게 보이는 상태(쓰러짐 등).
상태 필드를 늘리면 `stateHash`([`core/replay.ts`](../../packages/sim/src/core/replay.ts))에도 섞어야 결정성 테스트가 검사한다.

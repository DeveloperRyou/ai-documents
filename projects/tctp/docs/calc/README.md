# 수치 계산 — 시뮬이 숫자를 어떻게 셈하는가

객체가 **무엇을 가지는지**는 [`../objects/`](../objects/README.md), 그 값들이 **어떻게 섞여 결과가 되는지**는 여기에 둔다.
식은 코드(`packages/sim/src`)를 그대로 옮긴 것이고, 상수 이름을 함께 적는다. 상수 값이 바뀌면 이 문서의 표·계산 예도 고친다.
그래프(`img/*.svg`)는 튜닝 상수로 그린다: 상수를 바꾸면 `npm run charts` 로 다시 그린다 ([`tools/src/calc-charts.ts`](../../packages/tools/src/calc-charts.ts)). 식을 바꾸면 그 스크립트의 같은 식도 고친다.

| 문서 | 무엇을 셈하나 | 코드 (상수) |
|---|---|---|
| [movement.md](movement.md) | 이동 속도, 한 틱에 가는 거리, 약진 | [`body/soldier.ts`](../../packages/sim/src/body/soldier.ts) (`BASE_SPEED`, `RUSH_SPEED`, `LOAD`, `STAMINA`), [`command/action.ts`](../../packages/sim/src/command/action.ts) (`MOVE`) |
| [fire.md](fire.md) | 조준 시간, 산포, 탄도선·명중 부위, 지물 차단, 곡사·폭발, 근탄 | [`combat/fire.ts`](../../packages/sim/src/combat/fire.ts) (`FIRE`), [`command/action.ts`](../../packages/sim/src/command/action.ts), [`command/command.ts`](../../packages/sim/src/command/command.ts) (`FIRE_ORDER`), [`body/wound.ts`](../../packages/sim/src/body/wound.ts) (`WOUND`) |
| [vision.md](vision.md) | 시선 투과율, 시야각, 발견 확률, 계속 보기, 경계 시선 | [`perception/vision.ts`](../../packages/sim/src/perception/vision.ts) (`VISION`), [`perception/scan.ts`](../../packages/sim/src/perception/scan.ts) (`SCAN`), [`terrain/terrain.ts`](../../packages/sim/src/terrain/terrain.ts) (`RIM`) |
| [rates.md](rates.md) | 늘고 주는 몸 수치: 스트레스·지구력·혈액 (`RATES`) | [`body/rates.ts`](../../packages/sim/src/body/rates.ts), [`body/wound.ts`](../../packages/sim/src/body/wound.ts) |
| [random/](random/README.md) | **랜덤 수치**: 난수 생성기, 분포, 난수를 쓰는 곳 전부와 순서 | [`core/rng.ts`](../../packages/sim/src/core/rng.ts), [`core/vary.ts`](../../packages/sim/src/core/vary.ts) (`VARY`) |

## 공통 규칙

- **단위**: 거리 m, 시간은 상수에 초로 적고 시뮬은 정수 틱(1틱 = `DT` 0.25초)으로 센다. 초 → 틱은 `secToTicks(sec) = max(1, round(sec × 4))`.
- **SI 단위 상수, 틱 변환은 계산 안에서만**: 튜닝 상수는 실제 단위(m, 초, kg, 초당 값·초당 확률)로 적고, 틱 값으로 바꾸는 일은 그 값을 쓰는 식 안에서만 한다. 상수 자체에 틱 값을 담지 않는다 (예: `secToTicks(1)` 을 상수로 두지 않는다). 그래야 `DT` 를 바꿔도 상수가 그대로다.
  - 시간 길이 → `secToTicks(초)`.
  - 초당 양(속도·회복·출혈) → 한 틱에 `값 × DT`.
  - 초당 확률 → 한 틱 확률 `perSecChance(p) = 1 − (1 − p)^DT` ([`core/time.ts`](../../packages/sim/src/core/time.ts)). 위험률 변환이라 틱 길이와 상관없이 1초 동안 일어날 확률이 p 그대로다. `p × DT` 는 쓰지 않는다 (p 가 크면 1초 확률이 달라진다: p = 0.36 이면 `0.09` 를 네 번 굴려 1초에 0.31).
- **고정 주기 없음**: 모든 시스템(이동·사격·몸·경계 시선·탐지)이 매 틱 돈다. 여러 틱마다 한 번 도는 시스템을 두지 않는다 (틱 위상에 따라 결과가 갈리지 않게).
- **각도**: 시뮬 안은 화면 라디안 (0 = 동, 시계방향, y 남쪽). 시나리오 방위각(도, 0 = 북)은 `bearingToFacing(deg) = (deg − 90) × π/180`. 튜닝 상수는 도로 적는다.
- **산포**: 화기 `dispersion` 은 mrad 표준편차. 거리 d 에서 어긋남(m) ≈ `σ(rad) × d`.
- **기준 × 계수 (이름 규칙)**: 결과는 대부분 "기준 값 × 계수 × 계수 …" 이다. 식이 출발하는 값은 **기준 …**(코드 `base…`, 예: 기준 조준 시간 `baseAimTime`, 기준 속도 `BASE_SPEED`), 거기에 곱하는 값은 **… 계수**(코드 `…Coef` 또는 계수 표의 항 이름, 예: 조준 계수 `FIRE_ORDER.*.aimCoef`, 하중 계수)라 부른다. 계수 1 = 영향 없음. "배율"·"기본값"·"비율" 같은 다른 말은 쓰지 않는다. 표마다 기준과 계수를 나눠 적고, 같은 이름의 계수가 두 식에 나오면 앞에 무엇을 셈하는지 붙여 가른다 (조준 계수 vs 조준 산포 계수).
- **문턱 vs 양**: 단계가 넘어가는 문턱(`STRESS`, `WOUND`, `STAMINA`)과 늘고 주는 양(`RATES`)은 따로 둔다.

## 한 틱 순서 (`step`, [`core/world.ts`](../../packages/sim/src/core/world.ts))

순서가 바뀌면 같은 시드에서도 결과가 달라진다 (난수를 꺼내는 순서가 바뀌므로, [random/README.md](random/README.md)).

1. 이번 틱 명령 적용 (`applyCommand`: 반응 시간 굴림) → 때가 된 미뤄 둔 명령 (`applyDueOrders`)
2. `tick++`, `shots` 비움
3. 행동 (`updateActions`, 병사 id 순): 이동·사격·재장전. 사격은 그 자리에서 탄착·부상·근탄까지 판정
4. 듣기 (`updateHearing`, 병사 id 순): 이번 틱 탄의 총성·폭발음 → 스트레스 (#35)
5. 몸 (`updateBody`, 병사 id 순): 출혈 → 휴식 그침 → 지구력 → 상태 → 전우 피격 → 자세 → 스트레스
6. 경계 시선 (`updateScan`, 병사 id 순, 시선 전용 난수)
7. 탐지 (`updateVision`, 매 틱): 진영별 아는 적 갱신

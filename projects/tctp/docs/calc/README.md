# 수치 계산 — 시뮬이 숫자를 어떻게 셈하는가

객체가 **무엇을 가지는지**는 [`../objects/`](../objects/README.md), 그 값들이 **어떻게 섞여 결과가 되는지**는 여기에 둔다.
식은 코드(`packages/sim/src`)를 그대로 옮긴 것이고, 상수 이름을 함께 적는다. 상수 값이 바뀌면 이 문서의 표·계산 예도 고친다.

| 문서 | 무엇을 셈하나 | 코드 (상수) |
|---|---|---|
| [movement.md](movement.md) | 이동 속도, 한 틱에 가는 거리, 약진 | `soldier.ts` (`BASE_SPEED`, `RUSH_SPEED`, `LOAD`, `STAMINA`), `action.ts` (`MOVE`) |
| [fire.md](fire.md) | 조준 시간, 산포, 탄도선·명중 부위, 지물 차단, 곡사·폭발, 근탄 | `fire.ts` (`FIRE`), `action.ts`, `command.ts` (`FIRE_ORDER`), `wound.ts` (`WOUND`) |
| [vision.md](vision.md) | 시선 투과율, 시야각, 발견 확률, 계속 보기, 경계 시선 | `vision.ts` (`VISION`), `scan.ts` (`SCAN`), `terrain.ts` (`RIM`) |
| [rates.md](rates.md) | 늘고 주는 몸 수치: 스트레스·지구력·혈액 (`RATES`) | `rates.ts`, `wound.ts` |
| [random/](random/README.md) | **랜덤 수치**: 난수 생성기, 분포, 난수를 쓰는 곳 전부와 순서 | `rng.ts`, `vary.ts` (`VARY`) |

## 공통 규칙

- **단위**: 거리 m, 시간은 상수에 초로 적고 시뮬은 정수 틱(1틱 = `DT` 0.25초)으로 센다. 초 → 틱은 `secToTicks(sec) = max(1, round(sec × 4))`.
  초당 값은 한 틱에 `값 × DT` 만큼 적용한다. 초당 확률도 한 틱에 `p × DT` 로 굴린다 (작은 확률에서 `1 − (1 − p)^DT` 와 거의 같다).
- **각도**: 시뮬 안은 화면 라디안 (0 = 동, 시계방향, y 남쪽). 시나리오 방위각(도, 0 = 북)은 `bearingToFacing(deg) = (deg − 90) × π/180`. 튜닝 상수는 도로 적는다.
- **산포**: 화기 `dispersion` 은 mrad 표준편차. 거리 d 에서 어긋남(m) ≈ `σ(rad) × d`.
- **배율 곱**: 결과는 대부분 "기본값 × 배율 × 배율 …" 이다. 배율 1 = 영향 없음. 표마다 기본값과 배율을 나눠 적는다.
- **문턱 vs 양**: 단계가 넘어가는 문턱(`STRESS`, `WOUND`, `STAMINA`)과 늘고 주는 양(`RATES`)은 따로 둔다.

## 한 틱 순서 (`step`, `world.ts`)

순서가 바뀌면 같은 시드에서도 결과가 달라진다 (난수를 꺼내는 순서가 바뀌므로, [random/README.md](random/README.md)).

1. 이번 틱 명령 적용 (`applyCommand`: 반응 시간 굴림) → 때가 된 미뤄 둔 명령 (`applyDueOrders`)
2. `tick++`, `shots` 비움
3. 행동 (`updateActions`, 병사 id 순): 이동·사격·재장전. 사격은 그 자리에서 탄착·부상·근탄까지 판정
4. 몸 (`updateBody`, 병사 id 순): 출혈 → 휴식 그침 → 지구력 → 상태 → 전우 피격 → 자세 → 스트레스
5. 경계 시선 (`updateScan`, 병사 id 순, 시선 전용 난수)
6. 탐지 (`updateVision`, 4틱 = 1초마다): 진영별 아는 적 갱신

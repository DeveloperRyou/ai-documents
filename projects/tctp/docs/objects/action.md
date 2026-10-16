# 행동 `Action`

병사가 지금 하는 일. 코드: [`packages/sim/src/command/action.ts`](../../packages/sim/src/command/action.ts). 병사마다 하나(`Soldier.action`, 없으면 감시)를 가진다.

## 구조 (명령 → 임무 → 행동 → 장비)

```
Command (플레이어·AI 입력, commandLog 에 기록, 리플레이 대상)
   └▶ Order (분대·조 임무)          ── 리더 로직이 조원 행동으로 쪼갬   [구현됨: command/leader.ts]
         └▶ Action (병사 개인 행동)  ── 매 틱 종류별 처리 함수가 한 걸음 진행
               └▶ 장비 트리거 (화기 → Shot [구현됨], 수류탄 → Projectile, 삽 → 개인호)
```

- 행동은 **무엇을 할지**만 정한다 (어디로 갈지, 어디를 겨눌지, 얼마나 조준할지, 몇 발 쏠지). **결과**(속도·명중·피해)는 몸 상태와 장비가 정한다.
  예) 조준사격과 제압사격의 명중률 차이는 행동에 붙은 보정치가 아니라, 조준점·조준 시간·발 수가 달라서 화기 산포 계산에서 나온다.
- 행동은 순수 데이터다 (클래스 아님). 그래서 `stateHash`·`Snapshot`·리플레이에 그대로 들어간다. 처리 규칙은 종류별 함수 표(`ACTIONS`)에 둔다.
- 지금은 명령이 행동을 바로 준다 (`move` 명령 → `move` 행동). 플레이어는 분대·조에 임무(`order`)를 줄 수도 있고, 리더 로직([`command/leader.ts`](../../packages/sim/src/command/leader.ts))이 조원에게 개인 명령을 나눠 준다. 리더 로직은 시뮬 안에서 결정적으로 돌아 기록하지 않는다 (`commandLog` 에는 임무·교전 규칙 명령만 남고, 조원 행동과 교전 규칙이 고른 사격은 리플레이가 다시 만든다).
- 자세는 행동이 아니라 몸 상태다 (`posture` 명령이 바로 바꾼다. 이동 중에도 유지). 자세 바꾸는 데 시간이 걸리게 하려면 그때 짧은 행동으로 만든다.

## 종류

| 종류 | 필드 | 처리 (`ACTIONS`) | 끝 |
|---|---|---|---|
| `move` | `x`, `y` (목표, m), `via` (남은 경유점 목록, 차례로 지남), `route` (경로 탐색이 명령 때 구한 중간 경유점, 차례로 지남), `pace` (걸음 계수), `gait` (`walk` 걷기 / `rush` 약진), `fire` (이동사격: 사격 행동 또는 null) | `route[0]`, 없으면 `via[0]`, 없으면 목표 쪽으로 `speedOf(gait) × 선 칸 move 계수 × pace × 틱 흔들림 × DT` 만큼 직선 이동, 방향을 목표로. 다음 위치가 통행 불가면 그 자리 (길은 명령 때 `planRoute` 가 막힌 칸을 돌아 구해 두므로 목표에 닿을 길이 없을 때뿐). **약진**: 서서 뛰고 (3.5 m/s × 하중·지구력, 지구력 소모 큼) 도착하면 엎드린다. 다리를 다쳤거나 약해졌으면 걷는다. **이동사격** (걷기 + `fire`): 걸음 × `MOVE.fireSpeed`(0.5), 같은 틱에 `fire` 를 한 걸음 진행 (산포 × 2). 속도 식은 [../calc/movement.md](../calc/movement.md). 표적을 놓치거나 탄창이 비면 사격만 그친다 (걸으며 재장전하지 않음) | `route`·경유점은 `MOVE.arrive` 안에 닿으면 빼고 멈추지 않고 다음으로 꺾는다 (약진도 경유점에서는 엎드리지 않음). 경유점이 다 빠진 뒤 목표 `MOVE.arrive`(0.5m) 안, 또는 목표 5m 안에서 먼저 멈춘 병사에 닿음 (`blockedNear`). 다른 병사와 겹치면 `separate` 가 떼어 놓는다 ([../calc/movement.md](../calc/movement.md)) |
| `fire` | `slot`, `at`(조준점: 아는 적 `{soldier, id}` / 지점 `{point, x, y}`), `aim`(초, 화기 기준 조준 시간 × 명령의 조준 계수), `burst`(발), `judge`(제압: 영역을 아는 접촉으로 정함), `part`·`parts`(같은 명령의 몫 번호·몫 수), `risk`(명령의 `risk`: 아군이 사선에 있어도 쏨), 진행 `line`(사선 상태 `clear`·`reposition`·`hold`)·`step`(비켜 설 자리), `sweep`(이번 점사 영역 흩뿌림 반경 m)· `aimed`·`need`·`left`·`shot`·`ox`·`oy` | 조준점을 향해 `aim` × 조준 시간 계수(심리 `FIRE.stressAim` × 팔 × 실혈, ± `VARY.aim`) 초 조준 → 점사 `burst` (2발 이상이면 ± 1) 발 (한 틱에 `max(1, round(rof × DT / 60))` 발) → 다시 조준. 점사마다 영역(`judge` 면 아는 접촉에서 정함, fire.md §2a) 안의 한 점 + 겨눔 어긋남(`VARY.hold`)을 겨눈다. 탄창이 비면 재장전 행동으로 바꾸고 끝나면 이어 쏜다 | 겨눈 적이 진영에 안 보이거나 **사수 본인 눈에 안 보임**(`canAimAt`: 표적 쪽으로 돌아섰을 때 시선 투과 < `VISION.track`), 죽음, 탄이 다 떨어짐, 두 팔을 다 못 씀 |
| `reload` | `slot`, `until`(틱), `then`(이어 갈 사격) | `until` 에 장전 수만큼 (모자라면 남은 만큼) 채우고 `then` 으로 | `then` 이 없으면 채운 뒤 |
| `rest` | `wake` (교전을 알아채 일어날 틱, 모르면 null) | 아무것도 하지 않는다. 이 행동 중에 지구력이 제대로 회복 (멈춰만 있으면 `RATES.stamina.idleCoef` 배 빠르기, [../calc/rates.md](../calc/rates.md) "지구력"). 명령으로도, 할 일 없이 평온하면 저절로도 든다 (`startRest`: 서 있으면 앉음, [soldier.md](soldier.md) "기본 상태 전환"). 느슨하게 둘러본다 (보는 시간 × 2, 발견 × 0.5) | 평온(`calm`)이 깨지면 바로 (`updateBody`), 교전(`combatFloor > 0`)이 생기면 `wake` 틱 (0 ~ `VARY.reaction` 뒤) |
| `panic` | `mode` (`cower` 웅크림 / `surrender` 항복 / `flee` 도주), `x`, `y` (도주 목표, m) | 명령으로 줄 수 없다. 병사가 패닉(`broken`)에 빠진 틱에 [`body/panic.ts`](../../packages/sim/src/body/panic.ts) `choosePanic` 이 한 번 고른다 (아는 적 `World.contacts` 중 가장 가까운 것 기준): 선 자리 엄폐(`cover`) ≥ `PANIC.coverStay`(0.3) 이거나 아는 적이 없으면 웅크림; 적이 `PANIC.surrenderRange`(15m) 안이면 확률 `surrenderChance`(40%)로 항복; 아니고 `PANIC.fleeRange`(100m) 안이면 확률 `fleeChance`(60%)로 도주, 아니면 웅크림. 웅크림은 엎드려 제자리, 항복은 서서 제자리, 도주는 가장 가까운 아는 적 반대쪽 `PANIC.fleeDist`(40m) 지점으로 약진 속도로 직선 이동 (서서 뜀, 이동 행동과 같은 통행·하중·지구력). 도주 목표에 닿거나 길이 막히면 웅크린다 | 패닉이 풀리면(회복) `updateBody` 가 행동을 비우고 다시 명령을 듣는다 |
| `collect` | `from` (줄 쪽 병사 id), `item` (가져올 장비 id, null = 지닌 것 전부), `until` (줍기를 끝낼 틱, 곁에 닿기 전엔 null) | 쓰러진(무력화·사망) 병사 `from` 곁(`COLLECT.reach` 1.5m)까지 직선으로 걸어가 (속도·통행·하중·지구력은 이동 행동과 같다), 닿은 틱에 줍는 시간을 정하고, 그 시간이 지나면 [`collect.ts`](../../packages/sim/src/command/collect.ts) `transfer` 로 옮긴다. 가져오는 목록은 `planTake`: `item` 이 없으면 줄 쪽이 지닌 것 전부 (이미 칸이 찬 화기는 빼고), 화기 id 면 그 화기 (칸이 차 있으면 내 화기와 맞바꿔 옛 화기는 줄 쪽에 남음) 와 그 탄약 전부, 그 밖의 id 면 그 장비 전부. 무게가 `LOAD.maxRatio`(0.7) × 몸무게를 넘는 줄은 건너뛴다. 옮기면 양쪽 `load`·`loaded` 를 다시 센다: 새로 든 화기는 한 탄창 장전, 탄이 떨어져 있던 화기가 탄을 받으면 이어서 재장전 행동에 든다. 걷는 동안 줄 쪽이 치워졌거나 가져올 게 사라져도 그만둔다 | 옮기고 나서 (재장전이 이어지면 그 행동으로), 또는 가져올 게 없어졌을 때 |

줍는 시간 = (`COLLECT.baseTime` 3초 + 가져오는 무게 1kg 당 `COLLECT.perKg` 1초) × (1 ± `COLLECT.vary` 20%). 줄 쪽은 지금 쓰러진 병사뿐이고, 보급소는 같은 `planTake`·`transfer` 에 출처만 더해 붙인다 (미구현, 후속). 비화기 장비(장구 등)도 같은 방식으로 줍는다; 무전기처럼 줍는 것만으로 할 수 있는 일이 늘어나는 장비는 통신(#45)이 생길 때 붙인다.

**스스로 줍기** (`autoCollect`, 매 `COLLECT.auto.every`(4)틱, 병사마다 id 로 어긋남, 병사가 아는 것만 쓴다): 행동이 없거나 쉬는 중이고, 받을 명령이 없고, 심리가 평상·위협 인지이고, 마지막 위협 뒤 `auto.quiet`(10초)가 지났고, 곁 `auto.range`(15m)에 쓰러진 같은 편 전우가 있을 때, 가까운 전우부터 (a) 내 주화기 탄이 떨어졌고 그가 같은 탄을 지녔으면 그 탄을, (b) 내게 지원화기(탄창 ≥ `auto.supportMagazine` 100)가 없고 그가 임자 없는 지원화기와 그 탄을 지녔으면 그 화기를 줍는다. 다른 병사가 이미 그를 줍는 중이면 건드리지 않는다. 걸어가는 명령·사격·재장전 중이거나 총알을 맞는 중이면 하지 않는다. 난수는 줍는 시간 흔들림(`World.rng`)만 쓴다. 외부 판단 모델 쓸지는 #75.

조준사격·제압사격은 같은 `fire` 행동이다 (명령이 `FIRE_ORDER` 로 조준 시간·발 수·반경만 달리 넣는다, [world.md](world.md)).
조준사격(적 한 명)은 사수 본인이 그 적을 볼 때만 된다 — 다른 아군만 보는 적은 명령 때 거부(행동을 바꾸지 않음)되고, 쏘는 중에 가려지면 그친다 (이동사격은 사격만 그친다). 못 보는 적의 알려진 자리는 제압사격(지점)으로 쏜다.
다음 단계에서 늘어날 것: 수류탄 투척, 개인호 구축, 응급처치

## 흔들림 ([`core/vary.ts`](../../packages/sim/src/core/vary.ts), `VARY`)
같은 명령을 받아도 병사마다, 매번 조금씩 다르게 움직이고 쏘게 하는 사건별 잡음 (반응 시간·서는 자리·걸음·조준 시간·점사 발 수·겨눔 어긋남·재장전). 병사에 붙는 능력치가 아니다 (능력치는 두지 않는다). 난수는 시드 RNG 라 결정성은 그대로.
값과 굴리는 순서는 [../calc/random/rolls.md](../calc/random/rolls.md).

## 사격 판정 ([`combat/fire.ts`](../../packages/sim/src/combat/fire.ts), `pullTrigger`)
탄 하나하나를 날리지 않고, 쏜 틱에 탄도선을 따라 바로 판정한다. 결과는 `World.shots` (화면 효과용).
- 직사: 총구 → 조준점 방향에 산포를 더한 직선. 처음 걸린 사람(아군 포함)·지물·땅이 탄착점. 탄도선 곁 사람은 근탄으로 눌린다.
- 곡사: 조준점 둘레에 떨어진다 (지물을 넘어감). 폭발탄은 탄착점 둘레에 파편 부상·제압.
- 맞으면 부상 하나를 굴린다 ([soldier.md](soldier.md) "부상"), 스트레스와 확률적 쇼크(패닉), 기록에 정도·부위 또는 전사.
- 산포 식·피탄 폭·맞은 부위·지물 차단·폭발 확률과 계산 예는 [../calc/fire.md](../calc/fire.md).
- 방호구(방탄모·방탄복)·관통력·총성으로 위치 노출은 아직 없다.

## 진행 (`updateActions`, 매 틱)
- 병사 id 순서로 처리 → 결정적. 처리 함수가 `"done"` 을 돌려주면 행동을 비운다.
- 제압·패닉·무력화된 병사는 행동이 멈춘다 (`canMove`). 패닉·무력화·사망은 `updateBody` 가 행동을 버린다. 제압은 행동을 남겨 두어 풀리면 이어 간다.
- 이번 틱에 움직인 병사 id 를 돌려주고, `updateBody` 가 그것으로 `status = moving`·지구력 소모를 정한다.

## 명령과의 관계
| 명령 | 행동 |
|---|---|
| `move` | `{ kind: "move", x, y, via, route, pace, gait, fire }` 로 바꿈 (`route` = `planRoute`, [../calc/movement.md](../calc/movement.md) "경로 탐색") (진행 중 행동을 덮음). 명령의 `via`(경유점)가 `MOVE.maxVia`(8)개를 넘으면 명령을 거부한다. 경유점에도 목표와 같은 자리 어긋남을 더해 분대 모양이 경로 내내 유지된다. 목표는 명령 지점 + 명령 `ids` 순서로 받은 자리(`slotOffset`, 육각 고리 2m 간격) + `VARY.dest` 흔들림, `pace` = 1 ± `VARY.pace`. `gait` = 명령의 걸음 (기본 walk), `fire` = 명령의 `fire` 로 만든 사격 행동 (걷기일 때만) |
| `stop` | 행동 비움 |
| `posture` | 행동은 그대로, 자세만 바꿈 |
| `conceal` / `cover` | 위협 지점 `(x, y)` 을 알려 주면 `findShelter`([`command/shelter.ts`](../../packages/sim/src/command/shelter.ts))가 선 자리 둘레 `SHELTER.radius`(15m) 안에서 은폐(칸의 은폐 값) / 엄폐(칸의 엄폐 값)가 가장 좋은 칸을 골라, 약진 이동 행동(`gait: rush`, 도착하면 엎드림)을 준다. 선 칸보다 `SHELTER.minGain`(0.2) 이상 나은 칸이 없으면 이동 없이 그 자리에 엎드린다. 별도 "숨음" 상태는 없다 — 보호는 지형과 자세에서만 나온다. 점수·간격은 [../calc/movement.md](../calc/movement.md) "은폐·엄폐 찾기" |
| `collect` | `{ kind: "collect", from, item, until: null }`. `from` 이 쓰러져 있지 않거나, 자기 자신이거나, 가져올 게 없으면 거부 |

## 임무 `Order`와 교전 규칙 `Roe` (리더 로직)
명령 `{ kind: "order", side, unit, order }`: `unit` = 분대 이름 또는 조 이름. `World.units[unitKey(side, unit)]` 에 마지막 임무 종류와 교전 규칙을 둔다 (`stateHash` 에 들어감). 임무는 조원에게 개인 명령(`applyIndividual`)으로 나뉘므로 반응 시간·혼란 지연·"나중 명령이 이김"이 개인 명령과 똑같다.

| 임무 | 조원에게 나눠 주는 명령 |
|---|---|
| `move` (`x`,`y`,`via`,`gait`) | 이동 (경유점이 `MOVE.maxVia` 를 넘으면 임무 거부) |
| `withdraw` (`x`,`y`) | 약진 이동 |
| `assault` (`x`,`y`) | 걸어서 이동 + 목표 지점 이동사격 (화기 없는 조원은 그냥 걸음) |
| `suppress` (`x`,`y`) | 주화기를 든 조원만 지점 제압사격 (몫을 나눠 맡음). 든 조원이 없으면 거부 |
| `hold` | 정지 (행동 비움) |

없는 부대 이름이면 거부한다. 거부는 `World.log` 에 "거부: …" 로 남는다.

교전 규칙 명령 `{ kind: "roe", side, unit, roe }` (병사에게는 조에 준 규칙 > 분대에 준 규칙 > 기본 `hold`; 분대에 주면 조별 규칙을 덮음). `updateLeaders` 가 매 `ROE.every`(4)틱, 병사 id 로 어긋나게 행동이 없거나 쉬는 병사(받을 명령이 없을 때)에게 사격을 준다:
- `hold`: 임무·개인 명령으로 시키지 않는 한 쏘지 않음 (기본값이라 기존 동작 그대로).
- `return`: 같은 분대원 누군가 최근 `ROE.returnWindow`(10초) 안에 위협(피탄·근탄)을 받았을 때만, 아래 `free` 처럼 쏨.
- `free`: 주화기를 쏠 수 있는 병사가 사수 본인 눈에 보이고 사거리 안인 아는 적(`World.contacts`) 중 가장 가까운 것을 조준사격.

**지휘 권한**: `World.control = { side, echelon }` (시나리오의 `player`·`echelon`, 없으면 제한 없음). `echelon` 이 분대면 플레이어 진영 병사에게 개인 명령도 줄 수 있고(임무와 섞어도 나중 명령이 이김), 분대보다 높으면 개인 명령이 거부된다. 개인 명령에 `by: "debug"` 를 붙이면 항상 받는다.

혼란·위축된 병사는 명령을 늦게 받는다 (`Soldier.order`, [soldier.md](soldier.md)).

## 화면용
`SoldierView.dest` = 이동 행동의 목표 (`destOf`), `body.action` = 행동 종류 ([world.md](world.md)).

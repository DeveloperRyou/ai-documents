# #38 보급 행동 (탄·장비 건네기, 바닥/보급소에서 줍기)

조사일 2026-10-16. 코드는 바꾸지 않았다. 규칙: [research.md](../../.claude/rules/research.md).

## 이슈가 묻는 것

1. 전우끼리 탄·장비를 건네는 데 드는 시간 (양쪽 모두 묶임, 닿는 거리, 끊기는 조건).
2. 보급소/보급 더미(캐시)에서 스스로 줍는 시간·절차.
3. 옮긴 무게가 하중·속도에 주는 영향, 호환 탄만.
4. 교범이 분대 안 탄 재분배를 어떻게 다루는가.

## 현재 코드 (이미 있는 것)

- `COLLECT` ([`command/collect.ts`](../../packages/sim/src/command/collect.ts)): `reach` 1.5 m, `baseTime` 3 s + `perKg` 1 s/kg (줍는 무게 기준), `vary` ±20%, 모두 코드 주석 "추정". 출처는 쓰러진 병사뿐 (#8). `planTake`/`transfer` 가 호환 탄·화기 칸·하중 상한(`LOAD.maxRatio` 0.7)을 이미 처리한다.
- 하중: `LOAD.freeRatio` 0.15, `speedPerRatio` 0.6, `minSpeed` 0.4, `staminaPerRatio` 2, `limitRatio` 0.45 ([movement.md](../calc/movement.md)). 옮긴 뒤 `load` 를 다시 세므로 "무게에 따른 속도 변화"는 #8 에서 해결돼 있다.
- 탄 질량 (`content/equipment.json`): 5.56 K100 0.012 kg/발, 7.62x39 0.016 kg/발. 탄창은 개수가 아니라 발 수로 센다.
- 없는 것: 병사→병사 건네기(양쪽 행동), 보급소 개념(위치·내용물), 보급소를 알아보는 정보 안개.

## 조사 결과

### 1. 교범은 분대 안 탄 재분배를 절차만 말하고 시간·숫자는 없다 — 확인 (정성)

출처: FM 3-21.8 *The Infantry Rifle Platoon and Squad*, HQ Dept. of the Army, 28 March 2007. PDF `usu.edu/military-science/files/tools-for-cadets/the-infantry-rifle-platoon-and-squad.pdf` 를 받아 본문 grep (PDF 쪽 번호 = 파일 안 `=== page N ===`).

| 내용 | 위치 |
|---|---|
| 분대장 임무에 "Cross-leveling supplies and equipment throughout the squad" (6-3) | 6장 6-1~6-2, PDF 193~194쪽 |
| 부사수(AG)는 "Obtain ammunition from other Soldiers who are carrying machine gun ammunition", "Provide a supply of ammunition to the gun", 사격 중 탄 수를 분대장에 보고 (1-97) | PDF 32쪽 |
| 기관총 사수가 탄을 져야 하면 부사수가 사격을 멈추지 않고 꺼내도록 등에 진다 | 부록 A 표, PDF 385쪽 |
| 재편성(reorganization): "Redistribute ammunition" (7-169), "Redistributing ammunition and supplies" (8-33) | PDF 244쪽, 270쪽 |
| 방어 통합·재편성에서 분대·조장이 LACE(액체·탄·사상자·장비) 보고, 소대장이 합쳐 중대에 올림 (8-31) | PDF 269쪽 |
| 탄이 기본 휴대량을 넘을 걸 예상하면 캐시를 판다: 위치는 보조·후속 진지, "should be dug in", 경계는 능동·수동, 건드린 흔적 확인 (8-64) | PDF 279쪽 |
| 전투 휴대량 vs 기본 휴대량: 탄의 기본 휴대량은 상급 지휘관·SOP 가 정한다 (6-33) | PDF 198쪽 |
| 정기/긴급/사전비축 보급 3분류 (6-35) | PDF 198쪽 |

- 성립 조건: 미 보병 소대·분대 교리. 한국군에 그대로 맞는다는 근거는 아님.
- 교범에 없는 것: 탄창·벨트를 건네는 데 걸리는 초, 건네는 거리, 보급소에서 집는 데 드는 초.

### 2. 건네기·줍기 시간 — 못 찾음

- 교범 본문 어디에도 초 단위 수치가 없다 (위 grep 으로 확인). 웹 검색에서도 탄 건네기 시간 연구는 나오지 않았다.
- 현재 `COLLECT` 의 3 s + 1 s/kg 도 근거 없는 추정이다. 이슈 수락 기준은 시간에 수치 근거를 요구하지 않고 "N 개 이동, 양쪽 묶임, 끊기는 조건"만 요구한다.
- 등급: `추정`. 대안으로는 자세 바꾸기(#51)·재장전 시간과의 일관성(탄창 교체 3 s, 이미 `K2.reload`)으로 고른다고 적을 수 있다: 탄창 한 개 건넴 ≈ 탄창 갈기와 같은 몸놀림이라는 가정.

### 3. 하중 한도 — 2차

- FM 21-18 *Foot Marches* (1990, ATP 3-21.18 (2017) 이 대체) 의 전투 휴대량 48 lb (약 21.8 kg), 접근행군 72 lb (약 32.7 kg), 비상 접근행군 120 lb. 검색 요약 기준의 재인용이고 원문 PDF 는 못 열었다 (ATP 3-21.18 사본 uspatriottactical.com 은 받기 실패). 평균 160 lb 병사의 30% / 45% 로 환산된 값이라는 해설(MIL-STD-1472F)도 같은 검색 요약에서 봄 → 코드의 `limitRatio` 0.45 와 같은 출발점.
- 이미 코드 값이므로 이 이슈에서 새로 정할 필요 없음.

### 4. 탄 질량 — 2차 (약함)

- 5.56x45 한 발 약 12 g (단일 블로그), M249 200발 상자 6.6~7.2 lb (링크 포함, 같은 블로그). 현재 0.012 kg 과 일치. 30발 탄창 빈 무게는 못 찾음 → 현재는 탄창 몸체 질량을 0 으로 둔 셈 (7.62x39 0.016 kg 은 이번에 검증 안 함).
- 한 발 단위 운반이라 `mass` 가 이미 맞는 모델이다. 탄창 몸체/벨트 링크 질량(발당 + 약 몇 g)을 더할지는 결정 사항.

### 5. 호환 탄

- `equipment.json` 의 `ammo` 필드 일치로 이미 판정한다 (K2/K15 둘 다 `556-k100`: 국군 소총수 탄이 기관총에 호환, AK/RPD 는 `762x39`). 한국군 K15 가 K2 탄창과 호환되는지는 이번에 확인하지 못했다 (나무위키 단서만, 권위 자료 아님) → `추정`.

## 접근 실패·다음에 볼 곳

- ATP 3-21.8 (2016/2022/2024) 최신판: tamucc.edu 링크 404, armypubs 직접 접근 불가, Wayback (`ARN40007-ATP_3-21.8-000-WEB-1.pdf`, `ARN44065...001-WEB-3.pdf`, 2022 `ARN13842...001-WEB-4.pdf`) 받기 실패. 다음에 `pdf-text` 로 Wayback 다른 스냅숏을 시도.
- FM 3-21.8 마린 사본 (marines.mil) Access Denied (이번엔 usu.edu 사본 사용).
- ATP 3-21.18 (*Foot Marches*) 원문 하중표.
- 한국군 교범(분대 탄약 분배, 탄입대 규격), K15 탄창 호환, 탄창 빈 질량.
- 건네기·줍기 시간: 시간·동작 연구(예: 사격장 탄 보급 속도)나 훈련 교범 TC 3-22.9 류에 있는지 확인.

## 반영

(비움 — 반영 시 커밋을 적는다)

## 제안 (코드 수정 아님)

현재 코드와 이 조사의 차이: 교범은 **무엇을 하는가**(탄 재분배, 캐시, 보고)만 근거를 주고, 시간·거리 숫자는 근거가 없다. 따라서 새 수치는 모두 `추정` 으로 두고 이름과 문서에 그렇게 밝힌다.

1. **줍기 시간 상수를 공유**: `COLLECT.baseTime/perKg/reach/vary` 를 쓰러진 전우·보급소·건네기 세 경로가 같이 쓰게 한다 (이미 `planTake`/`transfer` 공용). 건네기의 시간식 = 줍기와 같은 `baseTime + perKg × 무게`. 새 상수를 만들면 `GIVE.baseTime` 처럼 이름 붙이되 값은 `COLLECT` 와 같게 두고 "추정" 표시.
2. **보급소(`cache`)를 `collect.ts` 의 출처로 추가**: 위치·내용물(`item→qty`)을 가진 월드 객체. 시나리오 JSON 으로 둔다. 8-64 에 맞춰 "쓰러진 전우 줍기와 같은 `planTake`" 를 쓰고, 정보 안개상 그 진영이 아는 보급소만 snapshot 에 낸다 (`World.contacts` 방식과 같은 거름). 경계(건드린 흔적)는 범위 밖으로 둔다.
3. **건네기 행동(`give`)**: 양쪽 병사에 행동을 건다 (주는 쪽 `give{to,item,qty,until}`, 받는 쪽 `receive{from,until}`). 끊김 = 이동 명령·무력화·`reach` 밖·명령 취소 중 어느 하나. 끊기면 시간 비례 부분 이동은 하지 않고(교범에 근거가 없다) "전부 or 0" 이 가장 단순하고, 수락 기준의 "partially or not at all" 은 질량 단위로 쪼갠 단계 이동(1틱마다 발 수 비례)으로도 만족된다 → 결정 필요.
4. **하중·속도**: 새 식 필요 없음. `transfer` 뒤 `load` 재계산으로 `LOAD` 식이 그대로 적용된다 (수락 기준 4 충족).
5. **탄 질량**: 탄창/벨트 링크 질량을 더할지 결정. 근거는 2차(웹 한 곳) 수준이라 현재 `mass` 유지를 권한다.
6. **드릴**: 이슈가 요구한 5개 — 건네기, 맞건네기, 끊긴 건네기, 보급소 줍기, 시체 줍기(#8 드릴 있음, 재사용) — 를 `drills.ts` 에 추가. 화면 표시: 병사 상세에 탄 수 (이미 있는지 확인 필요).
7. 문서: `docs/objects/action.md` 표에 `give`/`receive`, `docs/calc/movement.md` 에 건네기 시간 줄 (출처 줄이 이 파일을 가리키게).

## 권장 라벨

시간 수치가 `추정` 으로 남지만 교범이 절차를 뒷받침하고 구현 경로(#8 의 `planTake`)가 이미 있다. 건네기 중간 끊김의 부분 이동 여부 한 가지만 사용자 결정이 필요하다 → `needs-decision`.

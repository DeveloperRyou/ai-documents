# #55 패닉 결과(도주·웅크림·항복) 근거

조사일 2026-10-16. 이슈: [#55](https://github.com/DeveloperRyou/tctp/issues/55). 앞선 조사 [54-55-morale-panic.md](54-55-morale-panic.md) 의 후속.

## 현재 상태 (코드)

이슈 수락 기준은 이미 코드에 들어 있다 (커밋 618a835). [`body/panic.ts`](../../packages/sim/src/body/panic.ts) `PANIC` 상수 전부 **추정**이다.

| 상수 | 값 | 뜻 |
|---|---|---|
| `coverStay` | 0.3 | 선 자리 엄폐 이상이면 웅크림 |
| `surrenderRange` / `surrenderChance` | 15 m / 0.4 | 아는 적이 15 m 안이면 40 % 항복 |
| `fleeRange` / `fleeChance` | 100 m / 0.6 | 아는 적이 100 m 안이면 60 % 도주, 아니면 웅크림 |
| `fleeDist` | 40 m | 가장 가까운 아는 적 반대쪽 40 m 직선 |
| `rallyPerSec` / `STRESS.rally` | 0.25 / 30 | 회복 (docs/calc/rates.md, 추정) |

`docs/calc/` 에는 `PANIC` 표가 없다 (docs/objects/action.md 에만 있음). 드릴 6개: panic-flee, -flee-rally, -surrender, -cower-cover, -cower-far, -cower-unknown.

## 확인

| 항목 | 값·내용 | 조건 | 출처 |
|---|---|---|---|
| 패닉 증상의 정성 규정 | "Panics, runs under fire" 와 "Freezes under fire or is totally immobile" 가 서로 다른 전투 스트레스 경고 행동으로 나열됨. "panic run" = 자제력 없이 이리저리 뛰는 것, 일어서서 사격전 중 위험에 자신을 노출함, 위치를 잃고 마비된 듯 보이기도 함. 패닉은 일찍 못 막으면 다른 사람에게 번진다 | 정성 서술, 수치 없음 | FM 90-44/6-22.5 (= MCRP 6-11C, NTTP 1-15M) *Combat Stress*, 2000-06-23, 문서 쪽 14·15 (PDF 14·24쪽). [archive.org PDF](https://archive.org/download/MManuals/Fm90-44UsmcCombatStressMcrp611c.pdf) |
| 항복 | 이 교범은 항복을 다루지 않음 (grep `surrender` 0건) | - | 같은 문서 |
| 전선 근처 치료 시 복귀율 | 전선 가까이서 치료하면 약 75 % 가 완전 복귀. 부대 근처 전투 스트레스 시설에서 65~85 % 가 1~3일 안, 15~20 % 가 더 1~2주 안에 복귀, 5~10 % 만 후송. 후방 치료는 거의 복귀 못함 | 단위는 일·주. 초 단위 즉시 회복(rally)과 직접 비교 불가 | 같은 문서 PDF 60쪽·63쪽 |

해석: 패닉에 "웅크림(마비)"과 "달아남(panic run)"이 모두 있다는 구조(`cower`/`flee`)는 교범과 맞는다. 둘의 비율·도주 거리·항복 문턱은 숫자가 없다.

## 2차

| 항목 | 내용 | 출처 |
|---|---|---|
| 반응 분류 | 얼어붙기, 도주·투쟁, 탈출 불가 시 포기(체념) 같은 즉각 생존 반응 | [MGH 전투 스트레스 반응 팁](https://mghcme.org/app/uploads/2023/05/COMBAT-STRESS-REACTIONS-Tips-for-Providers.pdf) 검색 요약만 봄, 원문 안 열음 |
| 항복은 전염되고 전투 단위로 연구됨 | 개별 전투 수준에서 항복이 전투 사이에 퍼진다 | Lehmann & Zhukov, "Until the Bitter End? The Diffusion of Surrender across Battles", *International Organization* (2019). 초록만 봄, 수치 못 읽음 |
| 항복 의례·위험 | 1차대전 캐나다군 사이 항복은 비공식 규칙과 몸짓이 있었고 항복 직전 포로 살해가 잦았다 | Tim Cook, "The Politics of Surrender", *Journal of Military History* 2006. 검색 요약만 봄 |
| 사격 비율 | 54-55 문서와 같음 (Marshall, 수치 근거로 쓰지 않음) | [54-55-morale-panic.md](54-55-morale-panic.md) |

## 추정

- 위 `PANIC` 상수 전부. 항복 15 m 는 "손이 닿고 총구가 마주 보는 거리", 도주 100 m 는 "소총 유효 교전 거리 안", 도주 40 m 는 "다음 엄폐까지 뛰는 거리" 로 고른 값이며 출처는 없다.
- 도주·웅크림·항복 비율: 정량 자료를 못 찾았다. 현재 40 %/60 % 는 플레이로 맞추는 값.

## 접근 실패·못 찾음 (gaps)

- 도주·웅크림·항복 비율을 상황별로 준 1차 자료 없음. FM 6-22.5 (2000판)는 열었으나 정성 서술뿐. 최신 ATP 6-22.5 는 안 열었다.
- 항복 거리·확률: Lehmann & Zhukov, John A. Lynn II *Leaving the Fight* (Cambridge 2014) 본문 못 열음 (출판사 소개만 봄).
- Dupuy 의 항복·포로 비율 검색에서 아무것도 안 나옴.
- 한국군 교범의 패닉·항복 처리 미조사 (namuwiki 스킬 단서도 안 씀: 권위 자료가 아니고 수치가 없을 가능성이 큼).

## 다음에 볼 곳

- ATP 6-22.5 (Army) 최신판, Grossman *On Combat* (도주 대 얼어붙기 생리), Marshall 대신 Engen *Canadians Under Fire* 와 Keegan *Face of Battle* 의 도주 서술, Lynn *Leaving the Fight*, S. Rachman *Fear and Courage*.
- 일반 법칙: 제네바 협약 포로 대우는 항복 AI 규칙(포로 처리)이 생길 때.

## 반영

(비움)

## 제안 (코드·문서 수정은 하지 않음)

1. 수락 기준 세 항목 모두 이미 구현됐다. 남은 일은 근거뿐이다. 이슈를 닫고 `PANIC` 수치는 "추정, 튜닝 대상"으로 유지하는 것이 정직한 결정이다. 정량 근거가 없으니 `design:needs-research` 를 풀고 `needs-decision` 정도로 두거나, 그대로 닫기를 권한다.
2. 반영안 (수치 변화 없음): `docs/calc/rates.md` 에 `PANIC` 상수 표를 더하고 모든 줄에 "추정" 과 이 파일 링크를 단다. 지금은 docs/objects/action.md 에만 있다. 이 변경은 동작이 안 바뀌므로 e2e 해당 없음.
3. 교범과 일치시킬 것: "얼어붙음(마비)"과 "달아남"을 별개로 둔 구조는 FM 90-44 와 같다. 추가한다면 (a) 도주 도중 일어서 있음(노출)은 이미 반영, (b) 패닉 전염(교범: 일찍 못 막으면 번짐)은 미반영 — 곁 전우 패닉 시 스트레스 가산을 별 이슈로 검토할 만하다.
4. 회복 시간: 교범의 회복은 일 단위이고 현재 `rallyPerSec` 0.25 (평균 4초)는 훨씬 빠르다. 게임 플레이 단위(분 단위 교전)를 위한 설계 값으로 두고, 추정임을 docs 에 명시한다.

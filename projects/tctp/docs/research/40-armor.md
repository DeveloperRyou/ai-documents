# #40 방탄 장구 (방탄모·방탄복이 막아 주게)

조사일 2026-10-16. 코드는 바꾸지 않음.

## 지금 코드

- `content/equipment.json` `rok-kit`: gear 15 kg (방탄모 1.4 + 방탄복·판 ≈ 9, 추정). `gear` 는 하중에만 쓰임 (`content/equipment.ts` 61행).
- 피탄 부위는 `combat/fire.ts` `partAt` (선·앉음) / `pronePartAt` (엎드림) 이 높이·옆 위치로 정함 → `wound()` → `rollWound` (`body/wound.ts`) 가 `WOUND[kind][partClass]` 표와 `(refPower/power)` 지수로 심각도를 굴림. 방호 단계 없음.
- 탄약 `penetration` 은 mm 강판 상당(5.56 K100 10, 7.62×39 8, 7.62×54R 12). 방호 등급과 같은 단위가 아니라 그대로 못 비교한다.
- 파편은 `kind: "fragment"` 로 굴림 (위력은 거리로 줄인 값).
- 방호구 내구도, 부위별 덮음, KPA 장구 필드는 없음.

## 확인 (원문을 열어 봄)

| 항목 | 값 | 조건 | 출처 |
|---|---|---|---|
| NIJ Type III 시험탄 | 7.62 mm NATO FMJ 9.6 g, 847 m/s → 운동에너지 ½mv² ≈ 3,440 J (계산) | 경질 판 시험 | NIJ Standard-0101.06 (2008.7), Table 4 (PDF 60쪽, 문서 46쪽) [PDF](https://www.ojp.gov/pdffiles1/nij/223054.pdf) |
| NIJ Type IV 시험탄 | .30 M2 AP 10.8 g, 878 m/s → ≈ 4,160 J (계산) | 〃 | 같은 표 |
| 후면변형(BFS) 한도 | 44 mm. 조건: 모든 변형 ≤ 44 mm, 또는 80 % 이상이 44 mm 이하라는 95 % 신뢰 (부록 D) | 점토 후면재 | 같은 문서 Table 4, 부록 D |
| 한국군 다목적방탄복 | 연질 방탄복(판 미장착)은 권총탄 방호 목적으로 발전. 시험 = 17 grain FSP V50 + NIJ 0101.06 Level IIIA 권총탄(.357 SIG 125 gr, .44 Magnum 240 gr) 관통·후면변형. 소총탄은 판 몫 | 시험 규격 KDS 8470-4003 계열 | 박호연·구승환, 「방탄복 경량화를 위한 운영방안에 관한 연구」, 한국산학기술학회논문지 22(10), 2021, 277-285쪽 (2.2~2.4절) [PDF](https://www.kais99.org/jkais/journal/Vol22No10/vol22no10p32.pdf) |
| 한국군 방탄복 구성 | 국내는 PASGT형 → 다기능 → 다목적 방탄복. 판 삽입은 전·후면(필수) + 좌·우측면(선택)으로 구분하는 제안 (1단계 판 없음 / 2~3단계 전후면 판 / 4단계 사면 판) | 제안이지 현행 규정 아님 | 같은 논문 4쪽 결론부 |
| 한국군 방탄헬멧 | 신형 방탄헬멧(BH-2000 계열) 2004년부터 보급, 규격 KDS 8470-4001. 17 grain FSP V50 이상(수치는 논문에서 가림 `OOO.O`)을 상온·저온(−32 ℃)·침수 3조건에서 요구 | | 구승환·박호연·김영철, 「방탄헬멧의 고장인자 분석에 관한 연구」, 한국산학기술학회논문지 22(10), 2021, 357-363쪽 (2.2절) [PDF](https://www.kais99.org/jkais/journal/Vol22No10/vol22no10p40.pdf) |
| 미군 ACH 시험탄별 V50 | 2 gr RCC 1280.2 · 4 gr 1059.2 · 16 gr 754.4 · 64 gr 533.4 · 17 gr FSP 670.6 m/s | 미군 ACH 기준 (한국 헬멧 값 아님) | 같은 논문 Table 1 (359쪽) |
| 전상 부위 분포 | 사지 54 %, 복부 11 %, 얼굴 10 %, 머리 8 %, 눈 6 %, 흉부 6 %, 목 3 %, 귀 3 % (상처 6,609개, 1,566명, 2001.10~2005.1) | 미군 OIF/OEF, JTTR | Owens 외, *J Trauma* 64:295-299, 2008 — 초록 [UTMB](https://researchexperts.utmb.edu/en/publications/combat-wounds-in-operation-iraqi-freedom-and-operation-enduring-f/) (본문 표는 못 봄) |
| 전상 기전 | 폭발 78 %, 총상 18 % | 같은 연구 | 같은 초록 |

### 이 값으로 알 수 있는 것

- 총탄 대 판: Type III 시험탄(≈ 3.4 kJ)은 7.62 NATO 보통탄이다. 5.56×45·7.62×39 보통탄이 이보다 약하다는 것은 **추정**(탄 제원은 이번에 안 열어 봄) → 소총 보통탄은 판이 막는 것이 정상 경로, 철심탄·AP 는 예외라는 구도. 탄종별 정지 한계는 시험 보고서가 필요하다.
- 연질 방탄복(판 없음)은 권총탄·파편용이다. 소총탄에는 사실상 방호 없음으로 둬도 근거(위 논문 2.4절)와 어긋나지 않는다.
- 파편: 폭발이 상처의 78 %. 파편 방호가 방탄모·연질 방탄복의 본업이다.

## 2차 (원문은 아직 못 열음)

| 항목 | 값 | 출처 |
|---|---|---|
| SAPI 판 크기·무게 | 앞뒤: XS 184×292 mm 1.27 kg · S 222×298 1.59 · M 241×318 1.82 · L 260×337 2.09 · XL 280×356 2.40. ESAPI 는 같은 크기에 M 2.50 · L 2.85 kg. 옆판(SSAPI) 6×8 in ≈ 1 kg, ESBI 152×152~178×203 mm 0.75~1.15 kg | [Wikipedia SAPI](https://en.wikipedia.org/wiki/Small_Arms_Protective_Insert) (인용: BAE·GlobalSecurity — 원문 못 봄) |
| ESAPI/SAPI 방호 | .30-06 M2 AP 를 막는 NIJ IV 급. 판 뒤에 연질 층을 전제하는 경우 있음 | 같은 문서 |
| 한국군 신형 헬멧 기준 | 파편모의탄(1.1 g = 17 gr FSP) V50 선진국 기준 670 m/s 이상, 구형은 610 m/s 이상 | [서울신문 2022-06-05](https://m.seoul.co.kr/news/2022/06/05/20220605500017) (기사 요약, 본문 수치 직접 대조 못 함) |
| PASGT 헬멧 | 17 gr 파편 V50 ≈ 627 m/s (620~650) | 제조사 안내 [Safariland](https://safariland.com/collections/hard-armor/products/pasgt-ballistic-helmet-pasgt) |
| 이라크 해병 수술 부대 | 파편상 48 %(2003 침공) → 61 %(2004.3~2005.2), 총상 43 % → 33 % | Brethauer 외, *Arch Surg* — [Plastic Surgery Practice 기사](https://plasticsurgerypractice.com/treatment-solutions/innovations/research/report-quantifies-iraq-war-casualties-from-surgeons-pov/) |

## 추정 (출처 없이 고른 값)

- 판이 덮는 면적: 판이 가슴 한복판(≈ 24×32 cm)만 덮고 몸통 폭은 ≈ 35~40 cm, 복부는 판 아래라 안 덮임 → 코드의 `torso` 맞음에 "판 있음", `abdomen` 맞음은 연질만. 몸통 폭 수치는 임의 어림이라 `추정`.
- 방탄모 덮음: `head` 맞음의 일부(얼굴·목은 안 덮음, Owens 에서 얼굴 10 %·눈 6 % 가 머리 8 %와 별개로 집계되니 `head` 전체를 덮는 것으로 두면 과대).
- 판 내구도: 한 판이 견디는 발수. NIJ 는 판당 시험 발수만 정함(여러 발 연속 맞춤은 겹치지 않는 자리 기준). 실제 한계는 못 찾음 → 내구도 감소 곡선은 설계 값으로 정해야 함.

## 못 찾음 / 접근 실패

- KPA 방탄복·방탄모 유무와 성능: 공개 1차 자료 없음 (이슈에서 "KPA는 방탄 없음"으로 전제 — 근거 못 찾음).
- 한국군 방탄판(방탄복 판)의 실제 방호 등급·무게, 방탄모 정확한 무게: 논문에서 수치 가려짐. KDS 8470-4001·4003 원문은 국방기술품질원 규격이라 접근 못 함.
- 파편 정지 확률 곡선(V0·V50 곡선), 소총탄 vs 판 확률(판 시험은 6발 무관통 합격 기준만 있음).
- NIJ 0101.06 부록의 Type III/IV 발수·평가 절차 일부 (BL 시험)는 표만 봄.
- Owens 2008 본문 표(부위 겹침), Brethauer 원문, MIL-STD-662F 원문.
- koreascience JAKO201832073078368 PDF 받기 실패.

## 다음에 볼 곳

- KDS 8470-4001(방탄헬멧)·8470-4003(다목적방탄복) 국방규격, 국방기술품질원 표준 목록.
- MIL-STD-662F (V50), ARL 헬멧·IOTV 시험 보고서(DTIC), M193/M855/7.62×39 시험 속도·에너지.
- 판 연속 피탄(multi-hit) 시험 보고서.

## 반영

없음. (코드 미변경)

## 반영안 제안 (코드·docs/calc 는 아직 안 고침)

수락 기준 5개에 맞춰, **모델은 "방호 단계 vs 탄 위력" 과 "부위 덮음"** 두 축으로 나눈다.

1. 방호 표현: `gear` 외에 `armor` 종류(또는 gear 필드 `protection`)를 둔다. 부위별 항목 `{head | torso | abdomen: {fragment: 정지계수, rifle: 정지계수}}`. 단위가 mm 강판인 `ammo.penetration` 과 별도로 방호 수치를 두고, 탄에는 `armorClass`(권총/소총/철심)를 둔다 — 탄 제원이 확인된 뒤에.
2. 덮음: `fire.ts` 의 `partAt` 에서 `torso` 맞음에 한해 앞·뒤 판 구역(|off| ≤ `plateHalfWidth`)을 가르고, 옆·복부는 연질만. 상수 후보 `plateHalfWidth`, `helmetCoverage` — 값은 `추정`, 근거 없음을 표시해서 넣는다.
3. 판정: 덮인 부위 맞음 → 정지 확률 `stopP(탄종, 방호, 내구도)`. 정지면 심각도를 `graze`(둔상 + 스트레스 `RATES.stress.hit`)로 내리고, 실패하면 지금 `rollWound`. 수락 기준이 "파편은 소총탄보다 훨씬 자주 막힘"이므로, 방탄모·연질은 파편 정지 확률 ≫ 소총탄 정지 확률로 나누고, 판은 소총탄 정지 확률을 높게 둔다 (구체 값은 설계 판단·추정이고, 위 확인값은 방향만 뒷받침).
4. 내구도: 판·모 `durability`(발수 기준), 피탄마다 감소, 정지 확률 = `base × durability/max`. 곡선 근거 없음(추정).
5. KPA: 장비에 `armor` 가 없으면 지금 그대로. 같은 드릴에서 ROK/KPA 치명상 비율 차이를 확인 항목으로.
6. 하중: `rok-kit` 의 방탄모 1.4 + 방탄복·판 ≈ 9 kg 내역을 `armor` 로 분리 (무게 합 유지 → 이름만 바꾸는 단계로 나눠 `stateHash` 확인).
7. 사용자 결정 필요: ① KPA 를 전부 무방탄으로 둘지 ② 판 정지 확률·내구도 곡선(출처 없음) ③ 복부를 연질로 둘지 ④ 문서·상수 이름은 `…Coef` 규칙.

수치 근거가 `추정`인 것이 많아, 정지 확률 곡선과 한국군 판 규격 확인 전에는 `design:needs-research` 를 유지하고, 위 7번을 결정하면 `needs-decision` 으로 옮길 수 있다.

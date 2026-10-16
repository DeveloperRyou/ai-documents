# #33 발견: 임계와 탐색 시간 분포

조사일 2026-10-16. 결정(2026-10-15): 임계 모델 채택. 이 파일은 (a) 보이나/안 보이나 임계와 (b) 보일 때 걸리는 시간 분포의 함수 꼴을 고르기 위한 근거다.

## 찾은 것

| 항목 | 내용 | 등급 | 출처 |
|---|---|---|---|
| 탐색 시간 분포 | 관측자·표적이 정지해 있으면 발견 시각은 지수 분포. 센서마다 P∞(시간 제한 없을 때 결국 찾을 확률)와 τ(평균 발견 시간) 두 값으로 기술 | 2차(초록) | Friedman, ["Fundamental search relationships…"](https://www.researchgate.net/publication/258808203) ; Friedman·Mark, ["What probability distribution describes search?"](https://www.spiedigitallibrary.org/journals/OE/volume-58/issue-09/093103/What-probability-distribution-describes-search/10.1117/1.OE.58.9.093103.full), *Opt. Eng.* 58(9) 2019 |
| 흔히 쓰는 꼴 | P(t) = P∞ · (1 − e^(−t/τ)) | 2차(일반 서술, 원문 대조 전) | 위 문헌 계열 |
| τ 와 P∞ | τ 는 시나리오마다 P∞ 에서 경험적으로 정한다(밝을수록·쉬울수록 짧다) | 2차(초록) | Friedman 2019 초록. 흔히 인용되는 τ = 3.4/P∞ 는 이번에 확인 못 함 |
| 분포 예외 | 관측자 여럿·정지 표적은 하이퍼지수, 겨우 보이는 표적은 레일리 분포가 더 맞음 | 2차(초록) | Friedman·Mark 2019 |
| 임계(P∞) | Johnson 기준: 표적에 걸치는 분해 가능 주기 수로 탐지 확률. N50 = 시간 제한 없이 반을 탐지하는 주기 수. NVThermIP·TTP 가 이를 이어받음 | 2차 | [History and Evolution of the Johnson Criteria](https://www.osti.gov/servlets/purl/1222446) (OSTI) ; [TTP metric, DTIC ADA422493](https://apps.dtic.mil/sti/tr/pdf/ADA422493.pdf) |
| 시간 제한 탐색 | NVESD time-limited search 모델: P∞ 를 NVThermIP 에서 받아 시간에 따른 확률로 | 2차(초록) | [NVESD time-limited search model](https://www.researchgate.net/publication/253070372) (SPIE 5076, 2003) |

## TCTP 에 옮기면 (제안, 미반영)

- P∞ 를 "임계": 조건(거리·자세·은폐 투과·움직임)으로 P∞ 를 계산하고, P∞ 가 아주 작으면 0 으로 둔다 → 오래 봐도 못 찾는다.
- 지금의 매 초 굴림 대신, 조건이 바뀔 때 P∞ 로 "결국 찾을지"를 한 번 굴리고, 찾는다면 τ 를 평균으로 하는 지수 분포에서 발견 시각을 뽑는다. 조건이 바뀌면 다시 굴린다.
- 이슈 본문의 사용자 기준(개활지 400m 움직이는 표적 1~3초, 은폐된 표적 5초~수십 초 또는 영영)은 τ·P∞ 목표값으로 쓸 수 있다. 이 값들은 출처가 사용자 메모라 `추정`.

## 다음에 볼 곳

- Friedman·Mark 2019 본문(Open Access): τ–P∞ 관계식과 평균 시간식. 받은 PDF 는 텍스트 추출 도구가 없어 못 읽음.
- Johnson 기준의 사람 표적 N50 값(서 있는 사람·엎드린 사람 탐지 주기 수)

## 반영

없음.

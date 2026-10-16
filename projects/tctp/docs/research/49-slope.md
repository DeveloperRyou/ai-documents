# #49 경사: 이동 속도와 체력

조사일 2026-10-16. 지금: 경사를 보지 않는다.

## 찾은 것

| 항목 | 식·값 | 등급 | 출처 |
|---|---|---|---|
| Tobler 보행 함수 | W = 6·e^(−3.5·\|S + 0.05\|) km/h, S = dh/dx (오르막 +). 평지 약 5 km/h, 최고 6 km/h(약 −2.86° 내리막). 길 밖은 ×3/5 | 2차(위키) | [Wikipedia](https://en.wikipedia.org/wiki/Tobler%27s_hiking_function) ← Tobler 1993, NCGIA Tech. Report 93-1 (Imhof 1950 자료) |
| Tobler 한계 | 완만한 내리막에서 뾰족한 최고점이 비현실적일 수 있음. GPS 궤적 연구는 평지에서 더 느리고 경사에서 더 빠름 | 2차 | 위 위키 ; [Improved prediction of hiking speeds, arXiv 2303.16065](https://arxiv.org/pdf/2303.16065) |
| Pandolf 식 (체력) | M = 1.5W + 2.0(W+L)(L/W)² + η(W+L)(1.5V² + 0.35·V·G) [W] — W 체중 kg, L 짐 kg, V m/s, G 경사 %, η 지형 계수 | 2차(위키) | [Wikipedia](https://en.wikipedia.org/wiki/Pandolf_equation) ← Pandolf 외 1977 |
| 지형 계수 η | 포장 1.0, 흙길 1.1, 덤불 1.2, 짙은 덤불 1.5, 늪 1.8, 모래 2.1 | 2차(위키) | 같은 곳 |
| 내리막 | Pandolf 는 내리막을 못 다룸 → Santee 외 보정이 복잡 지형에서 오차가 가장 작음 | 2차(초록) | [Mil Med 183(9-10) e357](https://academic.oup.com/milmed/article/183/9-10/e357/5025891) ; 내리막 보정 원문 Pimental·Pandolf 1979, *Ergonomics* 22(8) |
| 군 행군 속도 | 평지 주간 4 km/h, 야간 3.2 km/h, 야지 주간 2.5–2.6, 야간 1.6 km/h | 2차(블로그) | [mtntactical](https://mtntactical.com/?p=93959) ← FM 21-18 (1990) |

## 판단

- 속도는 Tobler 꼴, 체력 소모는 Pandolf 의 경사 항(0.35·V·G)을 쓰는 안이 가장 단순하다. 둘 다 원문 미확인이라 지금은 `2차`.
- Tobler 는 등산객 자료라 군장 무게를 반영하지 않는다. 짐 효과는 이미 있는 부하 계수와 곱한다(제안).
- "아주 가파르면 못 지나감" 한계값의 출처는 아직 없다.

## 다음에 볼 곳

- ATP 3-21.18 (2022) 행군 속도·경사 표 ([irp.fas.org](https://irp.fas.org/doddir/army/atp3-21-18.pdf) 받기 실패)
- Santee 외 2003 내리막 보정식 계수

## 반영

없음.

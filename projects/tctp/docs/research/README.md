# 조사 근거

수치·식·편제·교범 절차를 바꾸기 전에 모은 출처. 규칙은 [`.claude/rules/research.md`](../../.claude/rules/research.md).

등급: `확인`(1차 원문을 직접 봄) · `2차`(재인용, 원문 미확인) · `추정`(출처 없음, 이유 적음).

| 파일 | 이슈 | 주제 | 상태 |
|---|---|---|---|
| [16-formation.md](16-formation.md) | #16 | 대형 이동 간격 | 조 쐐기 10 m 확인, 분대 종대 간격은 교범에 수치 없음 |
| [45-59-comms.md](45-59-comms.md) | #45 #59 | 음성·수신호·무전 | 수단 분류만 확인, 거리·지연 수치 없음 |
| [60-dig.md](60-dig.md) | #60 #69 | 땅 파기 시간 | 못 찾음 (FM 5-103 에 없음) |
| [23-suppression.md](23-suppression.md) | #23 | 구경별 제압 반경, 제압 유지 사격률 | 1972 DARPA 보고서 확인(선형 감소·화기별 점수), 반경 m 값은 2차 |
| [30-dispersion.md](30-dispersion.md) | #30 | 소총·MG 분산 | 기록사격 합격선(23/40)·MG 사격률 확인, 분산 mrad·탄착 지대 치수는 못 찾음 |
| [31-explosives.md](31-explosives.md) | #31 #37 | 수류탄·40 mm 폭발 | M67 5/15 m·4~5초·35 m 확인, 40 mm 사상 반경은 교범 안에서도 5 m/130 m 충돌 |
| [32-bleeding.md](32-bleeding.md) | #32 | 출혈·사망 시간 (#43·#81 통합) | 문턱은 ATLS 표 확인, 출혈·즉사 값은 추정 (반영함) |
| [33-detection.md](33-detection.md) | #33 | 발견 임계·탐색 시간 분포 | 식 꼴 확인(Friedman 2019), 맨눈 τ·P∞ 상수 미확보 |
| [39-61-aid.md](39-61-aid.md) | #39 #61 | 응급처치·후송 | 지혈대·지혈 거즈 3분 확인, 시간·끌기 속도 못 찾음 |
| [41-penetration.md](41-penetration.md) | #41 | 탄 관통 | FM 3-06.11 표 7-2·7-3 확인 (5.56 소요탄·7.62 관통 인치) |
| [43-vital-hit.md](43-vital-hit.md) | #43 | (#32 로 통합) | 내용은 32-bleeding.md "통합: #43" 절 |
| [49-slope.md](49-slope.md) | #49 | 경사 속도·체력 | 교범 확인(7% 문턱·오르내림 모두 느림), 곡선은 2차 |
| [51-posture.md](51-posture.md) | #51 | 자세 바꾸는 시간 | 2차 근사치만 |
| [53-hydration.md](53-hydration.md) | #53 | 수분·열 | TB MED 507 작업별 물 섭취·작업/휴식 (전재본), 저하율 곡선 없음 |
| [67-org-bd1.md](67-org-bd1.md) | #67 | 국군 8인 분대·BD1 원문 | BD1 확인(2016 단계·2024 이름), 국군 편제 2차 |
| [73-74-indirect-buildings.md](73-74-indirect-buildings.md) | #72 #73 #74 | 간접사격·건물 | 박격포 안전 구역·층고 13피트·벽 구멍 확인, 치명 반경 못 찾음 |
| [40-armor.md](40-armor.md) | #40 | 방탄 장구 | 2차만 (표준 원문 못 열음) |
| [46-47-light-optics.md](46-47-light-optics.md) | #46 #47 | 조도·광학 | 조도·PSO-1 2차, 인식 거리 못 찾음 |
| [54-55-morale-panic.md](54-55-morale-panic.md) | #54 #55 | 사기·패닉 | 못 찾음 (Marshall 수치는 부정확 판정) |
| [66-bd3-ambush.md](66-bd3-ambush.md) | #66 | BD3 매복 대응 절차 | 2007 판 단계 확인, 2016/2024 번호 충돌 |
| [70-trees.md](70-trees.md) | #70 | 나무 밀도 | 줄기 밀도 2차, 굵은 줄기 분포 없음 |
| [unresearched.md](unresearched.md) | #18 #21 #22 #42 #68 #69 #75 | 미조사·종속 | 이유 표 |

## 원문 받기

`pdf-text` 스킬(`.claude/skills/pdf-text/run.sh <url>`)을 쓴다. curl, headless Chromium, Wayback 순으로 시도한다. `apps.dtic.mil` 은 2026-10-16 기준 "Under Maintenance" 상태라 Wayback 으로 받았다.

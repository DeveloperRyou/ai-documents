# 조사 근거

수치·식·편제·교범 절차를 바꾸기 전에 모은 출처. 규칙은 [`.claude/rules/research.md`](../../.claude/rules/research.md).

등급: `확인`(1차 원문을 직접 봄) · `2차`(재인용, 원문 미확인) · `추정`(출처 없음, 이유 적음).

| 파일 | 이슈 | 주제 | 상태 |
|---|---|---|---|
| [23-suppression.md](23-suppression.md) | #23 | 구경별 제압 반경, 제압 유지 사격률 | 1972 DARPA 보고서 확인(선형 감소·화기별 점수), 반경 m 값은 2차 |
| [33-detection.md](33-detection.md) | #33 | 발견 임계·탐색 시간 분포 | 식 꼴 확인(Friedman 2019), 맨눈 τ·P∞ 상수 미확보 |
| [43-vital-hit.md](43-vital-hit.md) | #43 | 몸통 피격 즉시/지연 무력화 | 부위·장기별 치명 확인(WDMET), 시간 분포 미확보 |
| [49-slope.md](49-slope.md) | #49 | 경사 속도·체력 | 교범 확인(7% 문턱·오르내림 모두 느림), 곡선은 2차 |
| [51-posture.md](51-posture.md) | #51 | 자세 바꾸는 시간 | 2차 근사치만 |
| [67-org-bd1.md](67-org-bd1.md) | #67 | 국군 8인 분대·BD1 원문 | BD1 확인(2016 단계·2024 이름), 국군 편제 2차 |

## 원문 받기

`pdf-text` 스킬(`.claude/skills/pdf-text/run.sh <url>`)을 쓴다. curl, headless Chromium, Wayback 순으로 시도한다. `apps.dtic.mil` 은 2026-10-16 기준 "Under Maintenance" 상태라 Wayback 으로 받았다.

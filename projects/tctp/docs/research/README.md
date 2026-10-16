# 조사 근거

수치·식·편제·교범 절차를 바꾸기 전에 모은 출처. 규칙은 [`.claude/rules/research.md`](../../.claude/rules/research.md).

등급: `확인`(1차 원문을 직접 봄) · `2차`(재인용, 원문 미확인) · `추정`(출처 없음, 이유 적음).

| 파일 | 이슈 | 주제 | 상태 |
|---|---|---|---|
| [23-suppression.md](23-suppression.md) | #23 | 구경별 제압 반경, 제압 유지 사격률 | 2차만, 1차 미확보 |
| [33-detection.md](33-detection.md) | #33 | 발견 임계·탐색 시간 분포 | 식 꼴 2차, 상수 미확보 |
| [43-vital-hit.md](43-vital-hit.md) | #43 | 몸통 피격 즉시/지연 무력화 | 2차, 시간 분포 미확보 |
| [49-slope.md](49-slope.md) | #49 | 경사 속도·체력 | 식 2차(Tobler·Pandolf) |
| [51-posture.md](51-posture.md) | #51 | 자세 바꾸는 시간 | 2차 근사치만 |
| [67-org-bd1.md](67-org-bd1.md) | #67 | 국군 8인 분대·BD1 원문 | 2차, 원문 미확보 |

## 공통 접근 문제

- `apps.dtic.mil` PDF 는 WebFetch 403, curl 은 봇 확인 HTML 을 돌려준다. 브라우저(playwright)로 받거나 사용자에게 파일을 받아야 한다.
- 이 환경에 `pdftotext`·`pypdf` 가 없다. PDF 본문을 읽으려면 도구 설치가 먼저다.

# 수치·식 수정 (TCTP)

튜닝 상수, 계산 식, 화기·편제 수치, 그 이름을 바꿀 때 지키는 절차.

- **이름**: 식이 출발하는 값은 "기준 …"(코드 `base…`, 예: `baseAimTime`, `BASE_SPEED`), 거기에 곱하는 값은 "… 계수"(코드 `…Coef`, 예: `FIRE_ORDER.*.aimCoef`)라 부른다. 문서·주석·그래프 라벨·확인장 문구 모두 같다. "배율"·"기본값"·"비율"로 부르지 않는다. 같은 이름이 두 식에 나오면 셈하는 것을 붙여 가른다 (조준 계수 vs 조준 산포 계수). 규칙 원문은 [`docs/calc/README.md`](../../docs/calc/README.md).
- **같이 고칠 곳**: 상수 값·식을 바꾸면 한 커밋에서
  - `docs/calc/<문서>.md` 의 식 블록, 계수 표, 상수 표, 계산 예
  - 식을 바꿨으면 [`packages/tools/src/calc-charts.ts`](../../packages/tools/src/calc-charts.ts) 의 같은 식, 그리고 `npm run charts`
  - 난수 굴림을 더하거나 순서를 바꿨으면 `docs/calc/random/rolls.md`
  - 필드 이름을 바꿨으면 `docs/objects/`, `content/*.json` 의 `note` 설명, 테스트 도우미(`drills/test-util.ts`)의 가짜 장비
- **이름만 바꿀 때**: 동작이 같아야 한다. `npm run check` 의 드릴·리플레이 `stateHash` 가 그대로인지 보고, 바뀌면 이름 바꾸기가 아니다 — 원인을 찾는다. 이때는 e2e 해당 없음.
- **값·식을 바꿀 때**: [e2e.md](e2e.md) 대로 드릴을 더하고, 밸런스에 닿으면 `npm run headless` 로 전후를 비교해 보고한다.
- 바꾼 상수 이름이 남았는지 `grep -rn "<옛 이름>" packages content docs` 로 확인한다 (`poc/` 는 제외).

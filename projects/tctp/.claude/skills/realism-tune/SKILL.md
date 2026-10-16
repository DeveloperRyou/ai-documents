---
name: realism-tune
description: Make a TCTP sim number or formula more realistic -- suppression radius/stress, bleeding-to-death time, aim dispersion, reload/aim time, grenade/explosive effect, movement speed, detection time, weapon/org specs (K2, K201, K15, 분대 편제). Use when the user says "현실화", "실제 규격에 맞게", "교범 참고", "웹에서 확인해서 반영", "나무위키 확인 후 갱신", "수치가 이상해", "너무 커/작아", or picks a `type:realism` issue. Drives research with sources → constant/formula change → docs/calc + charts → drill → headless before/after report.
---

# realism-tune — 출처를 붙여 수치 현실화하기

TCTP의 수치는 근거가 있어야 한다. 사용자는 "어디서 나온 숫자인가"를 묻고, 모르면 "추정"이라고 적어 두기를 원한다. 상수를 고치는 일 자체보다, 조사 → 기록 → 반영 → 확인 순서를 지키는 것이 이 스킬의 핵심이다. 이름·문서 갱신 규칙은 `.claude/rules/calc.md`가 정하고, 이 스킬은 그 규칙을 지키는 절차다.

## 1. 지금 값을 안다

- 해당 상수·식을 찾는다: `grep -rn "<상수 이름>" packages/sim/src docs/calc`. 식 설명은 `docs/calc/<movement|fire|rates|vision>.md`, 난수 굴림은 `docs/calc/random/rolls.md`에 있다.
- 지금 결과를 숫자로 본다. 관련 드릴을 `sim-probe`로 덤프하면 "지금 12초에 죽음", "400m에서 1m 어긋남" 같은 비교 기준이 생긴다.
- **바꾸기 전에** 밸런스 기준선을 남긴다. 같은 작업 폴더를 다른 세션이 쓰므로 `git stash`로 되돌려 비교하지 말고, 먼저 돌려서 저장해 둔다.
  ```bash
  npm run headless -- 1 --n 10 --sec 120 > /tmp/headless-before.txt
  ```

## 2. 조사한다 — 확인된 것만 쓴다

- 출처 우선순위: 교범·군 문서(FM/ATP, DTIC, 국군 교범) > 논문·연구 보고서 > 제조사 규격 > 나무위키·블로그. 나무위키는 실마리로만 쓰고(`namuwiki` 스킬), 화기·편제 수치는 다른 출처로 한 번 더 확인한다.
- 숫자마다 **확인됨 / 추정** 중 하나로 가른다. 출처가 범위만 주면 범위 안에서 고르고 "범위 중 어디를 왜 골랐는지"를 적는다. 확인 못 한 것은 지어내지 않는다. 추정이라고 적거나, 사용자에게 묻거나, `design:needs-research`로 남긴다.
- 한국군 장비·편제(K2·K201·K15, 분대 인원)는 최근 개편이 있었다. 날짜가 있는 출처를 쓴다.

## 3. 반영한다 (calc.md 규칙)

- 상수는 이름 붙은 상수로 둔다. 초·m·kg 단위로 적고 계산할 때 `secToTicks`/`perSecChance`로 틱 단위로 바꾼다. 출발값은 `base…`(기준 …), 곱하는 값은 `…Coef`(… 계수)로 부른다. "배율"·"기본값"은 쓰지 않는다.
- 같은 커밋에서 함께 고친다:
  - `docs/calc/<문서>.md`: 식 블록, 계수·상수 표, 계산 예, 그리고 **출처 줄**(`- 출처: … (확인) / … 는 추정`)
  - 식을 바꿨으면 `packages/tools/src/calc-charts.ts`의 같은 식을 고치고 `npm run charts`
  - 난수 굴림을 더하거나 순서를 바꿨으면 `docs/calc/random/rolls.md`
  - 화기·탄약 수치는 `content/equipment.json`(`note` 설명 포함), 테스트 가짜 장비는 `drills/test-util.ts`
- 옛 이름이 남았는지 본다: `grep -rn "<옛 이름>" packages content docs`

## 4. 확인한다

- 바뀐 동작은 드릴로 보인다(`add-drill` 스킬). 현실 기준이 있으면 그 기준을 확인 항목으로 만든다. 예: "치명상은 2~5분 안에 사망", "5.56mm 2m 안 빗나감은 제압". 기존 드릴 기준이 깨지면, 새 현실 기준에 맞는지 보고 기준 쪽을 고친다. 이때는 이유를 보고에 쓴다.
- 밸런스를 비교한다:
  ```bash
  npm run headless -- 1 --n 10 --sec 120 > /tmp/headless-after.txt
  diff /tmp/headless-before.txt /tmp/headless-after.txt
  ```
- `npm run check`, 그리고 `run-tctp`로 확인장을 화면에서 본다.

## 5. 보고

결과 한 줄(옛 값 → 새 값, 출처 하나), 추정으로 남긴 것, headless 전후에서 달라진 것(첫 발견 시각, 사상자 등), `확인장 확인: <id> — 무엇을 봤는지`. 자세한 출처와 계산은 `docs/calc`에 있으니 보고에 다시 쓰지 않는다.

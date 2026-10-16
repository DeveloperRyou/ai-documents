---
name: add-drill
description: Add or change an e2e drill in TCTP's 행동 확인장 (packages/sim/src/drills/drills.ts) -- whenever a sim behavior is added/changed/fixed, an issue is resolved, or the user says "e2e로 확인 가능하게", "드릴 추가", "테스트로 보여줘", "확인장에서 보이게", "거리별로 e2e 만들어", "매복 테스트 해줘". Covers picking the group, laying out units/map/script, writing checks with the right `when`, the normal-path + exception pair, running it, and verifying it on screen.
---

# add-drill — 확인장 드릴 더하기

이 프로젝트의 e2e는 드릴이다(`.claude/rules/e2e.md`). 드릴 하나는 작은 지도, 병사 배치, 명령 기록, 확인 항목으로 이루어진다. `npm run check`가 모든 드릴을 끝까지 돌려 확인 항목이 전부 ✓인지 보고, 사용자는 `?debug=drills&drill=<id>`에서 틱 단위로 재생해 눈으로 본다. 그래서 드릴은 테스트이면서 사용자에게 보여 주는 설명이기도 하다. 제목·설명·항목 이름은 사용자가 읽고 바로 이해할 쉬운 한국어로 쓴다.

## 순서

1. **무엇을 증명할지 한 문장으로 정한다.** 고친 동작마다 정상 경로 드릴 하나, 예외(그치는 조건, 거부되는 조건, 한계)마다 드릴 하나씩 만든다. 예를 들어 `aimed-own-sight`(본인 시선 있으면 쏨)와 `unknown-target`(모르는 적은 거부)이 한 쌍이다. 거리처럼 값이 연속이면 거리별로 드릴을 나눈다(`supp-close`·`supp-hold`·`supp-far`).
2. **비슷한 드릴을 찾아 복사한다.** `grep -n 'group: "<묶음>"' packages/sim/src/drills/drills.ts`로 같은 묶음을 보고, 가장 가까운 드릴을 바로 뒤에 복사해 고친다. 파일 위쪽의 도우미(`field`·`ridge`·`cliff`·`rect`·`seg`, 장비 `K2`·`K15`·`K201`, 배치 `SQUAD9`·`COLUMN`·`HOLD`, 판정 `S`·`near`·`known`·`seen`·`ownSight`·`peak` 등)를 먼저 쓰고, 없을 때만 새로 만든다.
3. **필드를 채운다** (`Drill` 인터페이스가 정답이다):
   - `id`: 케밥 이름. 묶음 접두어를 붙인다(`vis-`, `trench-`, `scan-`, `spacing-`…).
   - `group`: `DRILL_GROUPS` 중 하나. 맞는 묶음이 없을 때만 새 묶음을 `DRILL_GROUPS`에 더한다(확인장 사이드바 순서가 바뀐다).
   - `title`·`desc`: desc에는 **기대 결과**를 쓴다. "~하면 ~한다. ~하지 않는다." 형식이고, 수치 기준이 있으면 수치도 쓴다.
   - `seed`·`sec`: 결과가 뚜렷해질 만큼만 길게 잡는다. 확률이 걸리면 기준을 넉넉하게 잡고, 시드 몇 개로 깨지지 않는지 본다(아래 확인 단계).
   - `units`: id는 배열 순서다. 좌표는 미터이고 x는 동쪽, y는 남쪽이다. `facing`은 라디안, 0 = 동쪽.
   - `known: true`는 발견을 기다리지 않을 때만 쓴다(사격·제압 드릴). 시야·발견 드릴에서는 쓰지 않는다.
   - `script`: `{ tick, cmd }`. 시각은 `secToTicks(초)`로 쓴다.
4. **확인 항목(`checks`)의 `when`을 고른다**:
   - `"ever"`: 한 번이라도 참이면 통과. "~하게 된다".
   - `"always"`: 내내 참이어야 통과. "~하지 않는다"(겹치지 않음, 쏘지 않음).
   - `"end"`: 끝났을 때 참. 최종 상태.
   - 숫자: 그 초에 참. 시점이 중요한 것("10초 안에 발견"은 숫자보다 `ever`+짧은 `sec`가 나을 때가 많다).
   - 판정에 쓰는 값을 `value: (w) => "…"`로 꼭 붙인다. 확인장이 참/거짓 옆에 그 값을 보여 줘서, 사용자가 "왜 통과했는지"를 숫자로 본다.
5. **돌린다.** 드릴 테스트 이름은 `title`이다.
   ```bash
   npx vitest run packages/tools/src/drills.test.ts -t "<title>"
   ```
   실패하면 `sim-probe` 스킬로 해당 시각의 값을 덤프해 원인을 본다. 기준을 결과에 맞춰 느슨하게 고치는 것은 마지막 수단이다. 그렇게 할 때는 이유를 보고에 쓴다.
6. **시드 흔들림을 본다.** 확률이 낀 드릴은 시드 몇 개로 돌려 본다.
   ```bash
   for s in 1 2 3 7 11; do node --preserve-symlinks --preserve-symlinks-main --import tsx .claude/skills/sim-probe/probe.ts <id> --seed $s | tail -n +2 | grep -c "✗"; done
   ```
   시드에 따라 실패하면 배치를 더 뚜렷하게 바꾸거나(거리, 자세) `sec`를 늘린다.
7. **화면에서 본다**(e2e 규칙). `run-tctp` 스킬을 쓴다.
   ```bash
   .claude/skills/run-tctp/run.sh drill <id> --end
   ```
   출력된 확인 항목이 새 드릴의 것인지 본다. 없는 id면 조용히 `move`가 열린다. 바뀐 동작이 지도나 병사 상세에 안 보이면, 확인장 표시(`packages/client/src/drills.ts`)를 같은 작업에서 더한다. 이 경우는 요청 외 UI 변경 금지의 예외다.
8. `npm run check` 후, 최종 보고에 `확인장 확인: <id> — 무엇을 봤는지` 한 줄을 넣는다.

## 하지 말 것

- 드릴에서 `Math.random()`이나 시각 함수를 쓰지 않는다. 결정성이 깨진다.
- 실제 시나리오 지도를 쓰지 않는다. 드릴은 `field()` 같은 작은 평지에 필요한 지형만 얹는다. 그래야 무엇을 보는 드릴인지 분명하다.
- 확인 항목 하나에 조건 여러 개를 `&&`로 묶지 않는다. 실패했을 때 어느 것이 틀렸는지 안 보인다. 항목을 나눈다.

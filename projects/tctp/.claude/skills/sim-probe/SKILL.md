---
name: sim-probe
description: Answer "why" questions about TCTP sim numbers by running the drill and dumping the actual values -- e.g. "투과가 왜 0.58이야?", "50m 서 있는 적을 왜 못 봐?", "시드 7 12초에 시야가 왜 확 바뀌어?", "발견 확률이 얼마야?", "스트레스가 왜 안 내려가?". Use whenever the user asks about a soldier's state, visibility, detection chance, or a drill's outcome at a specific seed/time, before reading code to guess. Also use to check a hypothesis while debugging a drill failure.
---

# sim-probe — 드릴을 돌려 숫자로 답하기

TCTP에 대한 "왜 이렇게 나와?" 질문은 대부분 특정 드릴·시드·시각의 값 문제다. 코드를 읽고 추측하기 전에 그 순간 값을 먼저 덤프하라. 실제로 어떤 요인이 0이거나 작은지 보이면, 그 요인 하나만 코드에서 찾아 읽으면 된다. 질문 하나에 파일 열 개를 읽는 일이 줄어든다.

## 실행 (레포 루트에서)

```bash
P="node --preserve-symlinks --preserve-symlinks-main --import tsx .claude/skills/sim-probe/probe.ts"
$P vis-posture --at 5,10 --pair 0:1 --log      # 5·10초에 전원 상태 + 0이 1을 보는 시야·발견 요인 + 그 사이 로그
$P scan-rear --seed 7 --at 11.5,12,12.25 --ids 0   # 시드 7에서 12초 앞뒤로 병사 0만
$P supp-close --every 2 --ids 1 --json         # 2초마다, JSON
```

- `<drill>`: 드릴 id. 없는 id를 주면 있는 id 목록을 출력한다.
- `--at` 초 목록 / `--every S` / `--seed N` / `--ids` / `--pair 관측자:대상`(여러 번 가능) / `--log` / `--json`.
- 마지막에 드릴 판정(✓/✗)을 끝까지 돌린 결과로 출력한다.

출력 읽기:
- 병사 줄: `id | side | xy | posture | status | action | stress | stressLevel | stamina | winded | blood | facing | look | wounds | loaded`. 각도는 도 단위이고 0 = 동쪽이다.
- `--pair` 줄: `visibility`(시선 투과) 뒤에 `detectFactors`의 모든 요인(`range fov vis conceal moving still observer observe …`)과 `chance`(이 틱의 발견 확률)가 온다. 끝의 `known`은 보임/놓침/모름이다. **chance가 0이면 곱해지는 요인 중 0인 것을 찾는다.** 원인은 거기에 있다.

## 쓰는 법

1. 사용자가 말한 드릴·시드·시각을 그대로 쓴다. 드릴 이름만 알면 `grep -n 'title: "<제목 일부>"' -B3 packages/sim/src/drills/drills.ts`로 id를 찾는다.
2. 갑자기 변한 순간을 묻는다면 그 시각 앞뒤로 0.25초(1틱) 간격의 `--at`을 준다.
3. 덤프에서 이상한 값을 고른 뒤에, 그 값을 만드는 코드와 `docs/calc/<문서>.md`의 식만 읽는다.
4. 답은 "숫자 → 그 숫자를 만든 식·상수 → 현실적으로 맞는지" 순서로 쓴다. 설계 결함으로 보이면 고칠지 백로그로 남길지 사용자에게 묻는다.

드릴이 아닌 상황(새 배치, 다른 거리)을 보고 싶으면 비슷한 드릴을 복사해 고친 임시 드릴을 만들지 말고, 사용자에게 그 상황을 드릴로 더할지 물어본다. 더하게 되면 `add-drill` 스킬을 따른다. 시나리오 단위(지도 전체) 통계는 `npm run headless`가 맡는다.

## 함정

- **`--preserve-symlinks --preserve-symlinks-main`가 꼭 필요하다.** `.claude/`가 ai-documents 레포로 가는 심볼릭 링크라서, 빼면 Node가 실제 경로 기준으로 모듈을 찾다가 `Cannot find module '@tctp/sim'`으로 실패한다.
- 시각은 틱으로 올림된다(1틱 = 0.25초). `--at 12.1`은 12.25초를 본다.
- 같은 작업 폴더에서 다른 세션이 sim을 고치는 중이면 덤프가 그 변경을 포함한다. 결과가 이상하면 `git status`부터 본다.

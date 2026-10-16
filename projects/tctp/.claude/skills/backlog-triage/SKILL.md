---
name: backlog-triage
description: Triage TCTP's GitHub backlog -- "백로그 확인", "남은 백로그", "할만한거", "간단한거 판단", "바로 진행 가능한거", "조사·결정 필요한 이슈 있어?", "이슈 분석해서 라벨 달아줘", "로컬 커밋으로 해결한건 닫아줘", or picking issues to hand to parallel agents. Groups open issues by the repo's own label scheme (design/priority/size/type/area), flags missing labels, issues closed in commits but still open, and blocked issues whose blockers are done, then recommends what to do next. Prefer this over the generic issue-status skill inside the tctp repo.
---

# backlog-triage — TCTP 백로그 정리·고르기

이 레포의 이슈에는 정해진 라벨 체계가 있다. 백로그 질문은 이 라벨로 답하는 것이 가장 빠르고, 사용자도 같은 말로 생각한다. 라벨 뜻은 `gh label list`의 설명이 정답이다.

| 축 | 값 | 판단 기준 |
|---|---|---|
| `design:` | `ready` · `needs-decision` · `needs-research` · `blocked` | 수락 기준이 충분해서 바로 착수 가능 / 사용자 결정이 남음 / 출처·수치 조사가 먼저 / 선행 이슈가 먼저 |
| `priority:` | `high` · `medium` · `low` | 분대 제품에 지금 필요 / 분대 현실성 다음 순서 / 소대 이후·확장 |
| `size:` | `S` · `M` · `L` · `XL` | 반나절~하루 / 며칠 / 1~2주 / 쪼갤 규모 |
| `type:` | `feature` · `realism` · `bug` · `refactor` · `docs` · `perf` | |
| `area:` | `combat` · `body` · `perception` · `movement` · `command` · `client` · `terrain` · `render` · `content` | 겹쳐도 됨 |

## 먼저 돌린다 (레포 루트)

```bash
python3 .claude/skills/backlog-triage/triage.py              # 전체: design → priority → size 순
python3 .claude/skills/backlog-triage/triage.py --ready      # 바로 착수 가능만
python3 .claude/skills/backlog-triage/triage.py --area perception
```

끝의 "손볼 것"에는 세 가지가 나온다: 라벨이 빠진 이슈, 커밋 메시지에 `closes #N`이 있는데 아직 열린 이슈, `blocked`인데 본문이 가리키는 이슈가 모두 닫힌 이슈(`ready` 후보).

## 요청별로

- **"할만한거 / 간단한거 / 바로 진행 가능한거"**: `--ready`에서 `size:S`·`M`을 priority 순으로 3~5개 추천한다. 병렬 에이전트에 나눠 줄 거라면, 고친 파일 영역(`area:`)이 겹치지 않는 묶음으로 짜고 겹치는 것은 따로 표시한다. 같은 작업 폴더를 여러 에이전트가 쓰기 때문에, 같은 파일을 동시에 고치면 서로의 hunk가 섞인다.
- **"조사·결정 필요한 거"**: `needs-research`는 무엇을 찾아야 하는지 한 줄씩 쓴다. 조사해서 반영하라고 하면, 웹·교범으로 **확실히 확인된 것만** 반영하고 확인 못 한 것은 남겨 둔다(`realism-tune` 스킬의 출처 규칙). `needs-decision`은 선택지를 짧게 나열하고 추천 하나를 붙여 사용자에게 묻는다. 결정되면 이슈 본문에 결정을 적고 `design:ready`로 바꾼다.
- **"분석해서 라벨 달아줘"**: 본문을 읽고 다섯 축을 모두 채운다. 확신이 없는 축(특히 `priority`)은 추천만 하고 사용자에게 확인받는다. 라벨을 바꿀 때는 `gh issue edit <n> --add-label … --remove-label …`을 쓴다.
- **"로컬 커밋으로 해결한건 닫아줘"**: "손볼 것"의 closes 항목을 이슈마다 커밋 내용과 대조한다. 그 커밋이 수락 기준을 다 채웠을 때만 `gh issue close <n> --comment "<커밋 해시>로 해결"`로 닫는다. 일부만 했으면 닫지 말고 남은 것을 코멘트로 적는다.
- **새 이슈 올리기**: `backlog-issue` 스킬을 쓰고, 위 다섯 축 라벨을 함께 단다.

## 보고

결과 한 줄 → 추천(번호·제목·왜) → 사용자가 정할 것 순서로 짧게 쓴다. 표 전체를 그대로 붙이지 않는다. 사용자는 GitHub에서 볼 수 있다.

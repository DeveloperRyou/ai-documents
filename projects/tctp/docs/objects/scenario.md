# 시나리오 `Scenario` · 캠페인

코드: `packages/sim/src/scenario.ts` (시나리오), `packages/client/src/content.ts` (캠페인 타입).
데이터: `content/scenarios/<id>.json`, `content/campaign.json`, `content/names.json`.

## 시나리오 `Scenario`

| 필드 | 뜻 |
|---|---|
| `id`, `title`, `subtitle` | 식별자, 제목, 부제 (교범 이름 등) |
| `echelon` | 플레이어가 지휘하는 제대 |
| `map` | 지도 id (`content/maps/<id>.json`) |
| `seed` | 기본 시드 (`?seed=` 로 덮어씀). 이름 생성에도 쓴다 |
| `player` | 플레이어 진영 |
| `camera` | 시작 화면 중심 `{x, y}` (m) |
| `briefing` | `Briefing` |
| `forces` | `ForceSpec[]` — 세울 부대들 |

`Briefing`: `situation` 상황, `mission` 임무, `drill` 훈련 절차(단계 문자열 배열), `source` 근거.

### 부대 배치 `ForceSpec`
| 필드 | 뜻 |
|---|---|
| `side` | 진영 |
| `org` | 편제 id ([org.md](org.md)) |
| `name` | 부대명 → 병사의 `squad` |
| `x`, `y` | 대형 중심 (m) |
| `bearing` | 바라보는 방위각 (도, 0 = 북, 시계방향) |
| `formation` | `"column"` 앞뒤 일렬 (맨 앞이 편제 첫 사람) / `"line"` 좌우 일렬 |
| `spacing` | 사람 간격 (m) |

`buildSoldiers(scenario, db)` 가 부대마다 편제 순서대로 병사를 만들고 대형 자리에 놓는다. `checkScenario` 는 편제·장비 참조 오류를 돌려준다.
`ContentDb` = `{ equipment: EquipmentCatalog, orgs: id → OrgTemplate, names: NamePool }`, `contentDb(...)` 로 묶는다.
`NamePool` = `{ surnames, given }` — 성 + 이름 조합 (실존 인물과 무관).

### 현재 시나리오
`bd1-react-to-contact` — 배틀 드릴 1 접적 시 행동 (ATP 3-21.8). 라스도르프, 국군 소총분대 `1분대` 종대(방위 25°, 5m 간격) vs 북한군 보병분대 `적 분대` 횡대(방위 205°, 4m 간격), 거리 약 220m.

## 캠페인 `campaign.json`

```
Campaign { programs: Program[] }
Program  { id, title, subtitle, locked?, courses: Course[] }     TACTICAL · COMMAND · STAFF
Course   { echelon, title, desc, locked?, scenarios: id[] }      분대 과정 → 소대 과정 …
```

- 과정은 분대에서 시작해 제대가 커지는 사다리. `locked` 는 메뉴에서 잠김 표시 (수료·승급 조건은 아직 없음).
- 지금 열린 것: TACTICAL → 분대 과정 → `bd1-react-to-contact`.

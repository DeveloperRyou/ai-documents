# 객체 — 현재 게임이 정의하는 것

코드(`packages/sim/src`)와 데이터(`content/`)에 있는 객체를 정리한다. 코드가 바뀌면 같이 고친다.
설계 의도는 [`../DESIGN.md`](../DESIGN.md), 모듈 구조는 [`../ARCHITECTURE.md`](../ARCHITECTURE.md).

| 문서 | 객체 | 코드 | 데이터 |
|---|---|---|---|
| [soldier.md](soldier.md) | 병사 `Soldier`, 몸 크기 `BodySize`, 휴대 장비 `LoadoutItem` | `types.ts`, `soldier.ts` (`BODY`) | 편제에서 생성 |
| [action.md](action.md) | 행동 `Action` (명령 → 임무 → 행동 → 장비 구조) | `action.ts` | — |
| [equipment.md](equipment.md) | 화기 `Weapon`, 탄약 `Ammo`, 장구 `Gear` | `equipment.ts` | `content/equipment.json` |
| [org.md](org.md) | 편제 `OrgTemplate` → 조 `OrgTeam` → 직책 `OrgMember` | `org.ts` | `content/orgs/*.json` |
| [scenario.md](scenario.md) | 시나리오 `Scenario`, 부대 배치 `ForceSpec`, 브리핑, 캠페인 | `scenario.ts`, `client/content.ts` | `content/scenarios/*.json`, `content/campaign.json`, `content/names.json` |
| [terrain.md](terrain.md) | 지형 격자 `Terrain`, 칸 성질 `TerrainProps` | `terrain.ts` | 지도(`content/maps`)에서 생성 |
| [world.md](world.md) | 월드 `World`, 아는 적 `Contact`, 명령 `Command`, 화면용 `Snapshot` | `types.ts`, `command.ts`, `snapshot.ts`, `vision.ts` | — |

## 관계

```
campaign.json ─ 과정 → 제대 과정 → 시나리오 id
                                      │
Scenario ─ forces[] ─ ForceSpec ─ org id ─▶ OrgTemplate ─ teams[] ─ members[] ─ loadout[] ─ item id ─▶ Weapon ─ ammo id ─▶ Ammo
   │                                                                                              (EquipmentCatalog)
   └─ buildSoldiers(scenario, ContentDb) ─▶ Soldier[] ─▶ createWorld(map, seed, soldiers) ─▶ World
                                                                                              ├─ terrain: Terrain (지도에서 구움)
                                                                                              ├─ contacts: 진영별 Contact[]
                                                                                              └─ snapshot(world, viewer) ─▶ Snapshot (렌더러가 읽음)
```

- 데이터 객체(장비·편제·시나리오)는 JSON 이고 id 로 서로 가리킨다. 병사는 장비를 id + 수량으로만 들고, 성능은 카탈로그에서 찾는다.
- 상태가 바뀌는 객체는 `World` 안의 `Soldier`(행동 `Action` 포함)·`Contact` 뿐이고, `step` 안에서만 바뀐다.
- 사격 판정은 아직 없다 (스트레스·부위 피해를 주는 쪽). 들어갈 자리는 [action.md](action.md) "장비 트리거"와 [`../DESIGN.md`](../DESIGN.md) "시뮬 모델".

# 객체 — 현재 게임이 정의하는 것

코드(`packages/sim/src`)와 데이터(`content/`)에 있는 객체를 정리한다. 코드가 바뀌면 같이 고친다.
설계 의도는 [`../DESIGN.md`](../DESIGN.md), 모듈 구조는 [`../ARCHITECTURE.md`](../ARCHITECTURE.md).
값들이 섞여 결과가 되는 식(속도·산포·발견 확률·스트레스 증감·난수)은 [`../calc/`](../calc/README.md).

| 문서 | 객체 | 코드 | 데이터 |
|---|---|---|---|
| [soldier.md](soldier.md) | 병사 `Soldier`, 부상 `Wound`, 몸 크기 `BodySize`, 휴대 장비 `LoadoutItem` | [`core/types.ts`](../../packages/sim/src/core/types.ts), [`body/soldier.ts`](../../packages/sim/src/body/soldier.ts) (`BODY`), [`body/wound.ts`](../../packages/sim/src/body/wound.ts) | 편제에서 생성 |
| [action.md](action.md) | 행동 `Action` (명령 → 임무 → 행동 → 장비 구조) | [`command/action.ts`](../../packages/sim/src/command/action.ts) | — |
| [equipment.md](equipment.md) | 화기 `Weapon`, 탄약 `Ammo`, 장구 `Gear` | [`content/equipment.ts`](../../packages/sim/src/content/equipment.ts) | [`content/equipment.json`](../../content/equipment.json) |
| [comms.md](comms.md) | 통신: 수단(목소리·워키토키·배낭 무전기)·통신 그래프·보고 전파 | [`perception/comms.ts`](../../packages/sim/src/perception/comms.ts) | [`content/equipment.json`](../../content/equipment.json) (무전기) |
| [org.md](org.md) | 편제 `OrgTemplate` → 조 `OrgTeam` → 직책 `OrgMember` | [`content/org.ts`](../../packages/sim/src/content/org.ts) | [`content/orgs/*.json`](../../content/orgs) |
| [scenario.md](scenario.md) | 시나리오 `Scenario`, 부대 배치 `ForceSpec`, 브리핑, 캠페인 | [`content/scenario.ts`](../../packages/sim/src/content/scenario.ts), `client/content.ts` | [`content/scenarios/*.json`](../../content/scenarios), [`content/campaign.json`](../../content/campaign.json), [`content/names.json`](../../content/names.json) |
| [terrain.md](terrain.md) | 지형 격자 `Terrain`, 칸 성질 `TerrainProps` | [`terrain/terrain.ts`](../../packages/sim/src/terrain/terrain.ts) | 지도(`content/maps`)에서 생성 |
| [world.md](world.md) | 월드 `World`, 아는 적 `Contact`, 명령 `Command`, 화면용 `Snapshot` | [`core/types.ts`](../../packages/sim/src/core/types.ts), [`command/command.ts`](../../packages/sim/src/command/command.ts), [`view/snapshot.ts`](../../packages/sim/src/view/snapshot.ts), [`perception/vision.ts`](../../packages/sim/src/perception/vision.ts) | — |

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
- 사격 판정은 [../calc/fire.md](../calc/fire.md), 부상은 [soldier.md](soldier.md) "부상", 늘고 주는 수치(`RATES`)는 [../calc/rates.md](../calc/rates.md), 흔들림·난수는 [../calc/random/](../calc/random/README.md).

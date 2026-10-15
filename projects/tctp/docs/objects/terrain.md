# 지형 격자 `Terrain` · 칸 성질 `TerrainProps`

코드: `packages/sim/src/terrain.ts`. 데이터는 따로 없고 지도(`MapData`)에서 굽는다.
`terrainOf(map)` 가 지도 객체마다 한 번 만들어 캐시한다 (라스도르프 1199 × 1001 칸에 약 60ms). 판 중에 바뀌지 않는다.

## `Terrain`
| 필드 | 뜻 |
|---|---|
| `w`, `h` | 칸 수 (칸 = `TERRAIN_CELL` = 1m) |
| `kind` | 칸마다 지물 종류 번호 (`Uint8Array`) |
| `elev` | 고도 격자 `ElevationGrid { cell, w, h, z: Float32Array(m) } \| null` |

읽기: `kindAt(t, x, y)` 종류, `propsAt(t, x, y)` 성질, `elevAt(t, x, y)` 고도(쌍선형, 격자 없으면 0).

## 굽는 규칙
- 칸마다 종류 하나. 겹치면 나중에 굽는 것이 이긴다.
- 면: 칸 중심이 다각형 안이면 칠함. 순서 residential → farmland → grass → orchard → scrub → wood → water → building.
- 선: 칸 중심이 선분에서 반폭 이내면 칠함 (최소 폭 1m). 순서 stream → river → ditch → path → track → road → fence → hedge → wall.
- 고도: 지도의 base64 Int16LE(0.1m)를 직접 디코드 (`decodeBase64`, `decodeElevation`).

## 칸 성질 `TerrainProps` (표 `TERRAIN`, 대략값)

| 종류 | 높이 m | 시야 감쇠 /m | 은폐 | 엄폐 | 이동 배율 |
|---|---|---|---|---|---|
| open (빈 땅) | 0 | 0 | 0 | 0 | 1 |
| residential (주거지) | 2 | 0.03 | 0.5 | 0.1 | 1 |
| farmland (농경지·밭) | 0.6 | 0.004 | 0.15 | 0 | 0.85 |
| grass (풀밭) | 0.3 | 0.002 | 0.05 | 0 | 1 |
| orchard (과수원) | 4 | 0.03 | 0.3 | 0.1 | 0.9 |
| scrub (덤불·관목) | 2 | 0.06 | 0.5 | 0.1 | 0.6 |
| wood (숲) | 15 | 0.08 | 0.6 | 0.3 | 0.7 |
| water (물: 호수·연못) | 0 | 0 | 0 | 0 | 0 (불가) |
| building (건물) | 6 | 10 (차단) | 0.9 | 0.9 | 0 (불가) |
| road / track / path (도로 / 비포장 농로 / 오솔길) | 0 | 0 | 0 | 0 | 1.1 / 1.05 / 1 |
| stream (개울) | 0 | 0 | 0.2 | 0.3 | 0.3 |
| river (강) | 0 | 0 | 0 | 0 | 0 (불가) |
| ditch (도랑·배수로) | 0 | 0 | 0.3 | 0.5 | 0.5 |
| fence (울타리) | 1.2 | 0.05 | 0.05 | 0 | 0.3 |
| hedge (생울타리) | 2 | 0.5 | 0.7 | 0.1 | 0.2 |
| wall (담장·돌담) | 1.5 | 10 (차단) | 0.6 | 0.8 | 0.2 |

| 성질 | 쓰는 곳 |
|---|---|
| `height`, `density` | 시선: 시선이 지면+`height` 아래를 지나면 1m 마다 `density` 누적, 투과율 = exp(−합) |
| `concealment` | 탐지: 표적이 선 칸의 은폐만큼 발견 확률 감소 (움직이면 절반) |
| `cover` | 아직 안 씀 — 사격·제압 판정용 |
| `move` | 이동: 걷기 속도 × 선 칸의 배율. 다음 칸이 0 이면 그 자리에 선다 (경로 탐색 없음) |

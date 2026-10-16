---
name: pdf-text
description: Download a source PDF (DTIC report, Army manual, paper) and extract its text so it can be grepped -- use when researching a number or doctrine for `docs/research/` and a web search only gave a secondary summary, when WebFetch returns 403 / binary PDF / "Under Maintenance", or when the user says "원문 찾아봐", "PDF 읽어줘", "교범 원문 확인". Falls back to headless Chromium and the Wayback Machine.
---

# pdf-text — 원문 PDF 받아 텍스트로 읽기

검색 요약은 `2차`일 뿐이다. 숫자를 `확인`으로 올리려면 원문을 직접 열어야 한다([research 규칙](../../rules/research.md)). WebFetch 는 큰 PDF 를 못 읽고 DTIC 에서는 403 이 나기도 한다. 이 스킬은 PDF 를 받아 페이지 표시가 붙은 텍스트로 바꾼다. 그다음 `grep`으로 필요한 곳만 읽는다.

```bash
.claude/skills/pdf-text/run.sh <url|file.pdf> [out-dir]
# -> <out-dir>/<이름>.pdf 와 <이름>.txt (페이지마다 '=== page N ==='), 마지막 줄에 txt 경로
```

- `out-dir` 는 세션 scratchpad 에 둔다(기본 `$TMPDIR/pdf-text`). 원문 PDF 는 레포에 넣지 않는다. 근거 파일에는 URL·서지·쪽수만 적는다.
- 받는 순서는 curl → headless Chromium(`run-tctp` 의 playwright 캐시 `~/.cache/tctp-run`) → Wayback 이다. Wayback 은 PDF 로 저장된 스냅숏 중 최신 것부터 시도한다.
- `pypdf` 는 `~/.cache/pdf-text/venv` 에 처음 한 번만 설치한다.

## 읽는 법 (본문을 통째로 Read 하지 않는다)

```bash
grep -n -iE "miss distance|suppress" <txt> | head -40   # 어디에 있는지 먼저 찾는다
sed -n '1300,1330p' <txt>                               # 그 근처만 읽는다
grep -n "=== page" <txt> | awk -F: '$1<1330' | tail -1  # 몇 쪽인지 (근거에 쪽수를 적는다)
```

- 처음에는 초록, 결론 장(`CONCLUSIONS`), 표 제목(`TABLE`)부터 grep 한다.
- 스캔본은 OCR 글자가 깨져 있을 수 있다. 숫자를 옮길 때는 앞뒤 문맥으로 한 번 더 확인한다.

## 원문 찾기 요령

- DTIC 보고서: `https://apps.dtic.mil/sti/tr/pdf/<AD번호>.pdf`. 사이트가 점검 중이면 Wayback 에서 받는다.
- 미 육군 교범: 최신판 파일 이름(ARN)은 Wayback 색인에서 찾는다.
  `curl -s "https://web.archive.org/cdx/search/cdx?url=armypubs.army.mil/epubs/DR_pubs/DR_a/&matchType=prefix&filter=original:.*ATP_3-21\.8-.*pdf&filter=mimetype:application/pdf&collapse=urlkey&fl=timestamp,original"`
- 2024년 이후 ATP 3-21.8 처럼 드릴 단계를 본문에서 빼고 ATN·CAR(로그인 필요)로 넘긴 교범은, 단계가 실린 이전 판을 함께 받아 판 차이를 적는다.

## 끝나면

`docs/research/<이슈>-<주제>.md` 항목을 `확인`으로 올린다. 이때 출처에 쪽수나 표 번호를 붙인다. 받지 못한 원문은 "다음에 볼 곳"에 남긴다.

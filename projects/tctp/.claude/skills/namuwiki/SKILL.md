---
name: namuwiki
description: Use when the user asks to look something up on 나무위키 (namu.wiki) -- e.g. pastes `site:namu.wiki <키워드>`, says "나무위키 검색", "나무위키에서 찾아줘", or `/namuwiki <키워드>`. Searches only namu.wiki and returns a short Korean summary with source links. Not for authoritative military data (편제·장비 수치) -- treat results as leads to verify.
---

# 나무위키 검색

Argument = 검색어 (예: `분대`, `K2 소총`). A leading `site:namu.wiki` is
stripped; if no keyword is given, ask for one.

## Steps

1. Load `WebSearch` via ToolSearch (`select:WebSearch`) if it isn't loaded.
2. One search, `mode: "standard"`, `allowed_domains: ["namu.wiki"]`,
   query = the keyword (add a disambiguating word such as `군대` only when
   the keyword is ambiguous and the context makes the meaning clear).
   Use `"extended"` only if the standard result is thin or off-target.
3. Don't WebFetch namu.wiki pages unless the user asks for the full
   article -- the search result is usually enough, and fetches are often
   blocked or bulky.

## Answer (Korean)

- 3~6 bullets: 정의 → 핵심 수치/구성 → 비교·변형. Bold the bullet label.
- Results often mix old revisions (`?uuid=`, `?rev=`); say so in one
  line when details differ between them, and prefer the main page.
- One line of caveat when the result would feed project data
  (`content/orgs/`, `equipment.json`): 나무위키는 교범이 아니므로 근거로
  쓰려면 공식 출처로 재확인.
- End with `Sources:` -- markdown links, main article first, at most 3.
- Don't edit project files from the result unless the user asks.

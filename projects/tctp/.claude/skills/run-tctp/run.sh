#!/usr/bin/env bash
# TCTP 를 띄워 브라우저로 조작한다. 레포 루트에서: .claude/skills/run-tctp/run.sh <drill|game|menu> ...
# - playwright 는 프로젝트 의존성이 아니라 ~/.cache/tctp-run 에 한 번 설치해 둔다
# - dev 서버(5175)가 없으면 띄우고 로그는 /tmp/tctp-dev.log
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd -P)
repo=$(git -C "$(pwd)" rev-parse --show-toplevel)
cache=${TCTP_RUN_CACHE:-$HOME/.cache/tctp-run}
pw=1.62.1

if [ ! -d "$cache/node_modules/playwright" ]; then
  mkdir -p "$cache"
  npm i --silent --no-save --prefix "$cache" "playwright@$pw" >&2
  NODE_PATH=$cache/node_modules node -e "require('playwright').chromium.launch().then(b=>b.close())" 2>/dev/null \
    || "$cache/node_modules/.bin/playwright" install chromium >&2
fi

if ! curl -sf http://localhost:5175 >/dev/null; then
  (cd "$repo" && nohup npm run dev >/tmp/tctp-dev.log 2>&1 &)
  timeout 60 bash -c 'until curl -sf http://localhost:5175 >/dev/null; do sleep 0.5; done'
fi

NODE_PATH=$cache/node_modules exec node "$here/driver.cjs" "$@"

#!/usr/bin/env bash
# PDF 원문 받아서 텍스트로 뽑기.
#   run.sh <url|file.pdf> [out-dir]   -> <out-dir>/<name>.pdf, <name>.txt (페이지마다 '=== page N ===')
# 받기 순서: curl -> headless Chromium(run-tctp 의 playwright 캐시) -> Wayback 최신 스냅숏.
# pypdf 는 ~/.cache/pdf-text/venv 에 한 번 설치한다 (프로젝트 의존성 아님).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
src=$1; out=${2:-${TMPDIR:-/tmp}/pdf-text}; mkdir -p "$out"
venv=${PDF_TEXT_VENV:-$HOME/.cache/pdf-text/venv}
if [ ! -x "$venv/bin/python" ] || ! "$venv/bin/python" -c "import pypdf" 2>/dev/null; then
  python3 -m venv "$venv" >&2 && "$venv/bin/pip" install -q pypdf >&2
fi
ispdf() { [ -s "$1" ] && head -c 5 "$1" | grep -q '%PDF'; }
if [ -f "$src" ]; then pdf=$src; name=$(basename "${src%.*}")
else
  name=$(basename "${src%%\?*}"); name=${name%.pdf}; pdf=$out/$name.pdf
  ua='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
  curl -sL -A "$ua" --max-time 90 -o "$pdf" "$src" || true
  if ! ispdf "$pdf"; then
    pw=$HOME/.cache/tctp-run/node_modules
    [ -d "$pw/playwright" ] && NODE_PATH=$pw timeout 120 node "$here/pwget.cjs" "$src" "$pdf" >&2 || true
  fi
  if ! ispdf "$pdf"; then
    echo "직접 받기 실패 -> Wayback 시도" >&2
    # 최신 스냅숏이 HTML(점검·차단 페이지)일 수 있어, PDF 로 저장된 마지막 스냅숏을 고른다
    # 새 것부터 차례로, 받다 끊긴 스냅숏은 건너뛴다
    for ts in $(curl -s --max-time 60 "https://web.archive.org/cdx/search/cdx?url=$src&filter=statuscode:200&filter=mimetype:application/pdf&fl=timestamp" | sort -r | head -5); do
      curl -sL -A "$ua" --max-time 300 -o "$pdf" "https://web.archive.org/web/${ts}id_/$src" || true
      ispdf "$pdf" && break
    done
  fi
  ispdf "$pdf" || { echo "PDF 를 못 받음: $src (첫 줄: $(head -c 120 "$pdf" | tr -d '\n'))" >&2; exit 1; }
fi
"$venv/bin/python" -I "$here/extract.py" "$pdf" "$out/$name.txt"
echo "$out/$name.txt"

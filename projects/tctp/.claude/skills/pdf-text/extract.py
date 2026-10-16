"""PDF -> text, one '=== page N ===' header per page (pypdf)."""
import sys
from pypdf import PdfReader

src, out = sys.argv[1], sys.argv[2]
r = PdfReader(src)
with open(out, "w") as f:
    for i, p in enumerate(r.pages, 1):
        f.write(f"\n=== page {i} ===\n{p.extract_text() or ''}")
print(f"{len(r.pages)} pages -> {out}", file=sys.stderr)

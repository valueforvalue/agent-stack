"""Splice the generated appendix into core/pragmatic-principles.md.

Replaces any existing §6 (Tip index) / §7 (Summary) / §8
(additional references) block with the freshly-generated
content. Idempotent — re-running on a doc that has not
been externally edited to §6-§8 yields the same result.

Pattern: locate the marker `\n---\n\n## §6 — Tip index`,
truncate the doc at that point, then write the marker +
fresh §6/§7/§8 content. If the marker is not found, append
fresh §6/§7/§8 (first-run behavior).
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
APPENDIX_FINAL = REPO / ".scratch" / "appendix-final.md"
APPENDIX_STRIPPED = REPO / ".scratch" / "appendix-stripped.md"
DOC = REPO / "core" / "pragmatic-principles.md"

if not APPENDIX_FINAL.exists():
    print(
        f"error: {APPENDIX_FINAL} not found; "
        "run scripts/build_tip_index.py first.",
        file=sys.stderr,
    )
    sys.exit(1)

# build_tip_index.py writes the appendix with a single leading
# blank line; strip it so the spliced section reads cleanly.
appendix = APPENDIX_FINAL.read_text(encoding="utf-8").lstrip().rstrip()
APPENDIX_STRIPPED.write_text(appendix, encoding="utf-8")
doc = DOC.read_text(encoding="utf-8").rstrip()

# Locate the start of the existing §6 block. Truncate the
# doc there so the splice REPLACES rather than appends.
MARKER = "\n\n---\n\n## §6 — Tip index"
idx = doc.find(MARKER)
if idx != -1:
    doc = doc[:idx]

section = (
    "\n\n---\n\n"
    "## §6 — Tip index (the 100 tips, by number)\n\n"
    f"{appendix}\n\n"
    "---\n\n"
    "## §8 — References (see also §5)\n\n"
    "- The companion audit doc: "
    "[`docs/audit/pragmatic-programmer-audit-2026-07.md`]"
    "(../docs/audit/pragmatic-programmer-audit-2026-07.md) — "
    "the per-tip *evidence*.\n"
    "- The regenerator: "
    "[`scripts/build_tip_index.py`](../scripts/build_tip_index.py) — "
    "reads the audit doc, writes `.scratch/appendix-final.md`. "
    "Run after every state change; then run this script to splice.\n"
    "- DixieData's `docs/agents/pragmatic-principles.md` "
    "(commit `cca2183` for the original spine, commit `177c2dd` "
    "for the tip-index appendix) — the upstream this doc was "
    "ported from.\n"
)

new = doc + section
DOC.write_text(new, encoding="utf-8")
print(f"Wrote {DOC} ({new.count(chr(10)) + 1} lines, was {doc.count(chr(10)) + 1})")

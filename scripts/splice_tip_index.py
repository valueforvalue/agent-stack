"""Splice the generated appendix into core/pragmatic-principles.md as §6+§7+§8."""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
APPENDIX = REPO / ".scratch" / "appendix-stripped.md"
DOC = REPO / "core" / "pragmatic-principles.md"

appendix = APPENDIX.read_text(encoding="utf-8").rstrip()
doc = DOC.read_text(encoding="utf-8").rstrip()

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
    "Run after every state change.\n"
    "- DixieData's `docs/agents/pragmatic-principles.md` "
    "(commit `cca2183` for the original spine, commit `177c2dd` "
    "for the tip-index appendix) — the upstream this doc was "
    "ported from.\n"
)

new = doc + section
DOC.write_text(new, encoding="utf-8")
print(f"Wrote {DOC} ({new.count(chr(10)) + 1} lines, was {doc.count(chr(10)) + 1})")

"""Build the Tip index appendix for core/pragmatic-principles.md.

Reads the per-tip evidence rows from
docs/audit/pragmatic-programmer-audit-2026-07.md and the principle↔tip
mapping (defined in this file), then emits §6 (Tip index) and §7
(Summary) text to .scratch/appendix-final.md so it can be spliced
back into core/pragmatic-principles.md.

Mirrors DixieData's .scratch/build_tip_index.py but with
agent-stack-specific data (the per-tip evidence) and the
principle↔tip mapping lifted from DixieData's
docs/audit/pragmatic-programmer-principles-audit-2026-07.md §2.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
AUDIT_TIPS = REPO / "docs" / "audit" / "pragmatic-programmer-audit-2026-07.md"
OUT = REPO / ".scratch" / "appendix-final.md"

# Principle ↔ tip mapping. 48 of the 100 tips map to a §1.x
# principle in core/pragmatic-principles.md. The rest are
# "philosophy / technique" attitudes (Ch 1) or "technique"
# (Ch 3+) — they inform behavior but are not operationalized as
# a deep-module rule.
#
# Source: DixieData's
# docs/audit/pragmatic-programmer-principles-audit-2026-07.md §2.
# The mapping is the book's structure, not repo-specific, so it
# ports cleanly to agent-stack.
PRINCIPLE_OF_TIP = {}
_PRINCIPLE_MAP_RAW = {
    "§1.1 DRY":                          [11, 12, 15, 16],
    "§1.2 Orthogonality":                [17, 44, 47, 48, 49, 50, 51],
    "§1.3 Reversibility":                [14, 18, 19],
    "§1.4 Tracer Bullets":               [20, 42, 66],
    "§1.5 Design by Contract":           [36, 37, 38, 39],
    "§1.6 Dead Programs":                [32, 33, 34],
    "§1.7 Law of Demeter":               [44, 45, 46],  # #44 overlaps with §1.2
    "§1.8 Metaprogramming":              [78, 79, 80],
    "§1.9 Temporal Coupling":            [53, 54, 55, 56, 60],
    "§1.10 MVC":                         [42],  # #42 overlaps with §1.4
    "§1.11 Program Deliberately":        [60, 67],
    "§1.12 Algorithm Speed":             [61, 62],
    "§1.13 Refactoring":                 [63, 65],
    "§1.14 Code That's Easy to Test":    [67, 68, 69, 70, 72],
    "§1.15 Ubiquitous Automation":       [85, 89, 90, 91, 94, 95],
    "§1.16 It's All Writing":            [11, 12, 13],  # #11, #12 overlap with §1.1
    "§1.17 Great Expectations":          [96],
    "§1.18 Pragmatic Teams":             [],  # N/A
    "§1.19 WISDOM":                      [10, 12],  # #12 overlaps with §1.1, §1.16
}
for principle, tips in _PRINCIPLE_MAP_RAW.items():
    for tip in tips:
        PRINCIPLE_OF_TIP[tip] = principle

# Tips with no §1.x mapping — "philosophy / technique, not a
# principle" per agent-stack's spine.
ATTITUDE_TIPS = {
    1, 2, 3, 4, 5, 6, 7, 8, 9,
    21, 22, 23, 25, 26,
    28, 29, 31,
    35,
    40, 41, 43,
    52,  # duplicate of #49
    57, 58, 59,
    64, 71, 73,
    74, 75, 76, 77,
    81, 82, 83, 84,
    86, 87, 88,
    92, 93,
    97, 98, 99, 100,
}

# Tips that are concrete N/A for agent-stack (multi-team,
# hiring, hosting incidents, scheduler iteration, etc.). State
# is ➖ for these.
NA_TIPS = {24, 27, 30, 35, 57, 76, 83, 84, 86, 99}


def parse_audit(path: Path):
    """Parse the per-tip evidence rows.

    Each row looks like:
        | 67 | Care About Your Craft | ✅ | `AGENTS.md` "Bias toward action" + ... |

    Returned: {tip_num: (title, state, evidence_str)}
    """
    tips = {}
    # The [TIP_INDEX_PLACEHOLDER] marker stands in for the table
    # body. After parsing the rows below the placeholder, we emit
    # them in numeric order.
    in_table = False
    with path.open(encoding="utf-8") as f:
        for line in f:
            if "[TIP_INDEX_PLACEHOLDER]" in line:
                in_table = True
                continue
            if not in_table:
                continue
            m = re.match(
                r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*"
                r"(✅|⚠️|❌|➖)\s*\|\s*([^|]+?)\s*\|\s*$",
                line.rstrip(),
            )
            if m:
                num = int(m.group(1))
                title = m.group(2).strip()
                state = m.group(3)
                evidence = m.group(4).strip()
                tips[num] = (title, state, evidence)
    return tips


def main():
    # Force UTF-8 stdout so the emoji in the roll-up line
    # prints correctly on Windows consoles (cp1252 -> UnicodeEncodeError).
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    if not AUDIT_TIPS.exists():
        print(f"Audit file not found: {AUDIT_TIPS}", file=sys.stderr)
        sys.exit(1)

    tips = parse_audit(AUDIT_TIPS)
    if len(tips) < 96:
        print(
            f"Expected ~100 tips in {AUDIT_TIPS}, got {len(tips)}.",
            file=sys.stderr,
        )
        sys.exit(1)

    header = """

This index is the **operational counterpart** to the principle
spine in §1. Each tip is a concrete behavior; the principle
is the *why* behind the behavior. The principle spine is what
an agent reads when designing a new feature; this index is what
an agent reads when checking whether a specific commit or
behavior is in compliance.

**State legend:**
- ✅ **Enforced** — a `core/laws.md` Law, a `core/*.md` rule, an
  `addenda/*` rule, an `issues/*.md` template, a `scripts/*`
  automation, or a `templates/*.md.tmpl` pins the tip.
- ⚠️ **Partial** — the spirit is satisfied but no written
  rule, OR the rule exists but no regression net enforces it.
  Cited.
- ❌ **Gap** — the tip is not addressed and would be
  high-leverage to add. Candidate follow-up.
- ➖ **N/A** — applies to contexts agent-stack does not
  inhabit (multi-team management, hiring, hosting incidents,
  scheduling iteration, etc.).

**Principle column** maps the tip to the §1.x section in this
doc that explains the *why*. Tips with a "philosophy /
technique" note are *attitudes* (Ch 1 of the book) or
*techniques* (Ch 3+), not principles per se — they inform
behavior but are not operationalized as a deep-module rule.

**One-line evidence** is truncated to ~110 chars. The full
evidence per tip lives in the source audit at
`docs/audit/pragmatic-programmer-audit-2026-07.md` (the
100-tip map retained as a primary audit artifact).

"""

    footer = """

## §7 — Summary: the 100 tips in numbers

| State | Count | What it means |
|---|---|---|
| ✅ Enforced | {yes} | The repo is in compliance. The principle spine in §1 names the operational form. |
| ⚠️ Partial | {partial} | The spirit is satisfied but no written rule, or no regression net. A future commit could regress without the agent noticing. |
| ❌ Gap | {gap} | Not addressed. Each gap is a candidate follow-up. |
| ➖ N/A | {na} | Doesn't apply (multi-team management, hiring, hosting incidents, scheduling iteration). |

The 100-tip audit is a **check**, not a refactor. The
principle spine (§1) is the primary lens for future work; the
tip index (§6, this section) is the primary lens for checking
specific commits against the canonical book.

When a new tip is added to a future edition of the book,
append a row to this index. When a tip's state changes (a new
commit pushes a ⚠️ to ✅ or a ✅ to ⚠️), update the State
column. The index is the **summary**; the audit doc
(`docs/audit/pragmatic-programmer-audit-2026-07.md`) is the
per-tip *evidence*.
"""

    lines = ["| # | Tip | State | Principle | One-line evidence |"]
    lines.append("|---|---|---|---|---|")
    for n in sorted(tips.keys()):
        title, state, evidence = tips[n]
        if n in PRINCIPLE_OF_TIP:
            principle = PRINCIPLE_OF_TIP[n]
        elif n in ATTITUDE_TIPS or n in NA_TIPS:
            principle = "— (philosophy / technique, not a principle)"
        else:
            principle = "—"
        ev = evidence.replace("|", "\\|")
        if len(ev) > 110:
            ev = ev[:107] + "..."
        lines.append(f"| {n} | {title} | {state} | {principle} | {ev} |")

    # Roll-up state counts for §7 — drives the table cells, not
    # a separate "computed at audit time" line.
    counts = {"✅": 0, "⚠️": 0, "❌": 0, "➖": 0}
    for _, state, _ in tips.values():
        counts[state] = counts.get(state, 0) + 1

    footer_filled = footer.format(
        yes=counts["✅"],
        partial=counts["⚠️"],
        gap=counts["❌"],
        na=counts["➖"],
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        header + "\n".join(lines) + footer_filled,
        encoding="utf-8",
    )
    print(
        f"Wrote {OUT} ({len(tips)} tips, "
        f"{counts['✅']} ✅ / {counts['⚠️']} ⚠️ / "
        f"{counts['❌']} ❌ / {counts['➖']} ➖)"
    )


if __name__ == "__main__":
    main()

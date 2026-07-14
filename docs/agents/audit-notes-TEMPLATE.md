# Manual UI Audit Notes — <DATE>

> **How to use this file.** Walk each surface in order. For
> every finding, fill in the matching block. Use ONE block
> per finding — do not bundle multiple bugs into one. Delete
> the `[placeholder]` lines as you go. If a surface has no
> findings, leave the section empty.
>
> See
> [`docs/agents/manual-audit-playbook.md`](manual-audit-playbook.md)
> for the full protocol. See
> [`../core/bug-patterns.md`](../core/bug-patterns.md) for the
> stack-agnostic pattern catalog. Run the adopting repo's
> audit runner (e.g. `audit/run-interactive.mjs`) to walk the
> surfaces — this file is for capturing what the script
> can't.

## Meta

- **Date**: <YYYY-MM-DD>
- **Walker**: <your name>
- **Build**: `<integration-branch>` @ `<commit SHA>` (run
  `git rev-parse HEAD`)
- **Server**: `<web-binary>` at `http://127.0.0.1:<port>`
- **Scratch dir**: `<.scratch path>` (seeded with N records)
- **Script result**: <paste the final "X pass, Y fail, Z
  manual" line from the script>

---

## Surface: <name> (N auto + M manual)

> <one-line surface description>
> **Manual prompt**: <what to verify by hand>

### Findings

<!-- FILL IN BELOW. DELETE THIS COMMENT. -->

---

## Summary

| Severity | Count | Issues |
|---|---|---|
| Blocker | 0 | — |
| Concern | 0 | — |
| Suggestion | 0 | — |
| Feature | 0 | — |
| Correction | 0 | — |

**Total findings**: 0

### Issues to file

<!-- Copy each [BUG] / [FEATURE] / [CORRECTION] block into a
     separate issue via `gh issue create --body-file`. Update
     the table above as you file them. -->

### Patterns to add to the bug catalog

<!-- If you noticed a pattern that recurs across multiple
     findings, add it to the §"Bug class → first place to look"
     table in the adopting repo's bug catalog and to the grep
     cookbook (or `core/bug-patterns.md`). -->

### Cross-round observations

<!-- Anything that doesn't fit a single finding. E.g. "the
     audit process is slow on X" or "the manual prompts could
     be more specific on Y". -->

# Threat Models (CWE / OWASP / OWASP-LLM)

> **Externalized from [`../core/bug-patterns.md`](../core/bug-patterns.md).**
> The pattern → MITRE CWE / OWASP Top 10 / OWASP LLM mapping
> (13-row table + 6 source citations) lives here, kept
> load-light on the core bug catalog.
>
> **When to load:** on demand, when an adopter needs to map
> a fix contract to a CWE / OWASP control (regulated
> environments: SOC2, HIPAA, PCI), or when auditing a
> pattern against the canonical AI-amplified bug categories
> (Tambon et al. 2024, DAPLab 2026, CodeRabbit 2025).
> **Not** loaded at session start.
>
> Inline mappings (CWE / OWASP refs embedded in the
> meta-pattern descriptions in `core/bug-patterns.md`) stay
> there — they map directly to the per-pattern fix
> contract.

---

## Authoritative cross-references

Where an agent-stack pattern overlaps with a known
classification scheme, the cross-reference is recorded
inline. Adopters working in regulated environments (SOC2,
HIPAA, PCI) can map their required controls to these
sources.

- **[MITRE CWE Top 25 (2025)](https://cwe.mitre.org/top25/)** —
  industry-weakness enumeration. CWE-79 (XSS) still leads.
- **[OWASP Top 10:2025](https://owasp.org/Top10/2025/0x00_2025-Introduction/)** —
  web application risk categories. A10 "Mishandling of
  Exceptional Conditions" is new in 2025 and aligns with
  the *invoker wiring gap / silent early return* pattern
  below.
- **[OWASP Top 10 for LLM Applications (2025)](https://owasp.org/www-project-top-10-for-large-language-model-applications/)** —
  agent-specific risks. Excessive Agency, Improper Output
  Handling, Prompt Injection are the ones a coding agent
  can self-introduce.
- **[Tambon et al. (2024)](https://arxiv.org/abs/2403.08937)** —
  canonical empirical taxonomy of bugs in LLM-generated
  code: 333 bugs across 10 categories, LLM bugs 50% more
  logic-heavy than human bugs, 2.25× slower to fix. Source
  for many of the AI-amplified categories below.
- **[DAPLab 9 Critical Failure Patterns (Jan 2026)](https://daplab.cs.columbia.edu/general/2026/01/08/9-critical-failure-patterns-of-coding-agents.html)** —
  field reports from 5 leading agents (Claude, Cline,
  Cursor, v0, Replit) across 15+ vibe-coded apps.
  Source for *intent mismatch*, *hallucinated APIs*,
  *re-implementing stdlib*, *repeated code*.
- **[CodeRabbit AI vs Human report (Dec 2025)](https://coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report)** —
  470 PRs, AI produces 1.7× more issues overall, 2× more
  concurrency/dependency issues, 2.74× more security issues.

### Pattern → authority cross-reference

| Agent-stack pattern | CWE | OWASP 2025 | OWASP LLM |
|---|---|---|---|
| Invoker wiring gap (silent early return) | CWE-754, CWE-1188 | A10:2025 (Mishandling of Exceptional Conditions) | LLM05 (Improper Output Handling) |
| Drift between layers | CWE-704 (Incorrect Type Conversion) | A03:2025 (Supply Chain) | — |
| Response-shape mismatch | CWE-20 (Improper Input Validation) | A04:2025 (Cryptographic — by analogy, signature drift) | LLM05 |
| Authorization / intent gap | CWE-862 (Missing Authorization) | A01:2025 (Broken Access Control) | LLM06 (Excessive Agency) |
| Hardcoded paths / secrets | CWE-798 (Hardcoded Credentials), CWE-22 (Path Traversal) | A02:2025 (Cryptographic Failures), A05:2025 (Misconfiguration) | — |
| Concurrency / dependency correctness | CWE-362 (Race Condition), CWE-676 (Use of Risky API) | A08:2025 (Software/Data Integrity) | — |
| Nil-guard gap | CWE-476 (NULL Pointer Dereference) | A10:2025 | LLM05 |
| Hallucinated API / fake key | CWE-1188 (Insecure Default) | A06:2025 (Vulnerable Components) | LLM09 (Misinformation) |
| Silent error suppression (logging-only) | CWE-778 (Insufficient Logging), CWE-209 (Info Exposure via Error) | A09:2025 (Logging Failures), A10:2025 | — |
| Re-implementing stdlib / reinventing wheels | CWE-1076 (Insufficient Prefabricated Components) | A03:2025 (Supply Chain) | — |
| Repeated code (AI amplification) | CWE-1041 (Use of Redundant Code) | — | — |
| Date / timezone handling | CWE-682 (Incorrect Calculation) | — | — |
| UI re-entrant call | CWE-662 (Improper Synchronization) | A04:2025 | — |

If your fix contract maps to a CWE or OWASP category that
isn't listed here, open an issue. The table grows by
adoption.



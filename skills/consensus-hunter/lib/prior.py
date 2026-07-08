"""
History-derived priors for the consensus-hunter.

Three priors, each answering a different question about a (file, function)
coordinate:

  A) bug_density   -> P(this fn has been bug-prone historically).
                        Source: per-function commit-message scan for
                        fix/bug keywords. Best ground-truth via tagged
                        bug-fixes (Fixes: bpo-NNNN, Fixes: CVE-XXXX).

  B) churn         -> P(this fn has changed a lot recently).
                        Source: lines-changed over a recent window. The
                        Lehman §10 deep-module failure mode: high churn
                        + broad interface = complexity inflation.

  C) co_change     -> P(this fn inherits risk from co-changers).
                        Source: which other functions/files change in the
                        same commits. Bugs cluster in co-changed code.
                        The only prior that captures non-local risk.

All three priors are mapped onto [0,1] via a saturating transform:
    p = 1 - exp(-k / λ)
which gives a sigmoid shape that saturates near 1 for chronically-buggy
functions and stays near 0 for benign ones — matching the synthetic sweet
spot found in the calibration research.

The priors are designed to run against a git repo on disk (call site
provides the path). They are pure-stdlib; the only external dependency is
the `git` CLI for history queries.
"""

from __future__ import annotations

import math
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


# --- Git helpers -------------------------------------------------------------


def _git(repo: Path, *args: str, timeout: int = 60) -> str:
    """Run git with a timeout. Returns stdout (stripped). Raises on non-zero."""
    res = subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True, text=True, timeout=timeout,
        encoding="utf-8", errors="replace",
    )
    if res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {res.stderr.strip()}")
    return res.stdout.strip()


def list_python_functions(repo: Path, path_filter: str | None = None) -> list[tuple[str, str]]:
    """Discover (file_path, function_name) pairs via lightweight regex —
    sufficient for calibration work, avoids depending on tree-sitter or ast
    parsing for languages outside our v1 scope.

    v1 limits to Python. Add a parser-backed implementation when extending
    to non-Python (postgres was the next candidate; that needs a C AST).
    """
    py_files: list[Path] = []
    for p in repo.rglob("*.py"):
        # Skip virtualenvs, build dirs, .git, etc.
        s = str(p)
        if any(part.startswith(".") or part in {"venv", "site-packages",
                                                  "node_modules", "__pycache__"}
               for part in p.parts):
            continue
        if path_filter and path_filter not in s:
            continue
        py_files.append(p)

    fn_re = re.compile(r"^(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
    out: list[tuple[str, str]] = []
    for p in py_files:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = str(p.relative_to(repo))
        for line in text.splitlines():
            m = fn_re.match(line)
            if m:
                out.append((rel, m.group(1)))
    return out


# --- Prior A: bug density ----------------------------------------------------

BUG_KEYWORDS = re.compile(
    r"\b(fix(?:es|ed)?|bug|cve[- ]?\d|sec(?:urity)?|bpo[- ]?\d+"
    r"|vuln|patch)\b",
    re.IGNORECASE,
)


def bug_density_prior(
    repo: Path,
    coords: Iterable[tuple[str, str]],
    months: int = 24,
) -> dict[str, float]:
    """For each (file, fn), count fix/bug-keyword commit touches in
    the last `months` of history. Map to [0,1] via 1 - exp(-k/λ).

    Note: we use a coarse keyword signal here. A calibrated version would
    pull a tagged CVE/SECURITY commit list (e.g. from a CHANGELOG) and
    only count those — that's the v1.1 plan.
    """
    coord_set = set(coords)
    counts: Counter[str] = Counter()

    # Get log with patch info — `git log -p` is heavy; we get only files
    # touched then attribute blame to function via a separate map.
    log = _git(
        repo, "log", f"--since={months * 30} days ago",
        "--name-only", "--pretty=format:COMMIT:%H %s",
    )

    current_is_bug_commit = False
    current_files: list[str] = []
    for line in log.splitlines():
        if line.startswith("COMMIT:"):
            if current_is_bug_commit:
                for f in current_files:
                    # Attribute to function-level by also checking historical
                    # blame — this is the cheap version. A v1.1 would resolve
                    # to a specific function via `git log -L`.
                    counts[(f, "*")] += 1
            current_is_bug_commit = BUG_KEYWORDS.search(line) is not None
            current_files = []
        elif line.strip():
            current_files.append(line.strip())

    # Final commit
    if current_is_bug_commit:
        for f in current_files:
            counts[(f, "*")] += 1

    # λ = repo-wide mean per-file fix-touches in the window
    files_seen = {f for (f, _) in counts}
    if not files_seen:
        return {}
    lam = sum(counts.values()) / len(files_seen)

    # Per-coord bug-density. We don't have function-level blame yet; this
    # version maps any file touch with the keyword to "*" bucket, then
    # assigns that bucket's density to all functions in the file.
    by_file: dict[str, int] = {}
    for (f, _), k in counts.items():
        by_file[f] = by_file.get(f, 0) + k

    out: dict[str, float] = {}
    for f, fn in coord_set:
        k = by_file.get(f, 0)
        if lam == 0:
            lam = 1.0
        p = 1.0 - math.exp(-k / lam)
        out[f"{f}:{fn}"] = max(0.0, min(1.0, p))
    return out


# --- Prior B: churn ----------------------------------------------------------


def churn_prior(
    repo: Path,
    coords: Iterable[tuple[str, str]],
    months: int = 12,
) -> dict[str, float]:
    """For each (file, fn), count line-changes in the window. Saturated
    transform — chronic churners saturate fast; quiet files stay near 0."""
    coord_set = set(coords)
    counts: Counter[str] = Counter()

    log = _git(
        repo, "log", f"--since={months * 30} days ago",
        "--numstat", "--pretty=format:COMMIT:%H",
    )

    current_files: list[str] = []
    current_changes: list[tuple[int, int]] = []
    for line in log.splitlines():
        if line.startswith("COMMIT:"):
            for f, (a, d) in zip(current_files, current_changes):
                counts[f] += (a + d)
            current_files = []
            current_changes = []
        elif line.strip():
            parts = line.split("\t")
            if len(parts) == 3:
                try:
                    add = int(parts[0]) if parts[0] != "-" else 0
                    dele = int(parts[1]) if parts[1] != "-" else 0
                except ValueError:
                    continue
                current_files.append(parts[2])
                current_changes.append((add, dele))

    if current_files:
        for f, (a, d) in zip(current_files, current_changes):
            counts[f] += (a + d)

    if not counts:
        return {}
    lam = sum(counts.values()) / len(counts)

    out: dict[str, float] = {}
    for f, fn in coord_set:
        k = counts.get(f, 0)
        if lam == 0:
            lam = 1.0
        p = 1.0 - math.exp(-k / lam)
        out[f"{f}:{fn}"] = max(0.0, min(1.0, p))
    return out


# --- Prior C: co-change ------------------------------------------------------


def co_change_prior(
    repo: Path,
    coords: Iterable[tuple[str, str]],
    months: int = 12,
) -> dict[str, float]:
    """For each (file, fn), estimate risk inherited from co-changers in
    the same commit. Bugs cluster in co-changed code.

    Algorithm:
      1. Build a file -> {files_changed_with_it} map across the window.
      2. For each function's file, compute weighted mean of co-changers'
         bug-density-equivalent (churn here, as a proxy).
      3. Saturate.
    """
    coord_set = set(coords)
    co_change: dict[str, Counter] = defaultdict(Counter)

    log = _git(
        repo, "log", f"--since={months * 30} days ago",
        "--name-only", "--pretty=format:COMMIT:%H",
    )

    current_files: list[str] = []
    for line in log.splitlines():
        if line.startswith("COMMIT:"):
            for a in current_files:
                for b in current_files:
                    if a != b:
                        co_change[a][b] += 1
            current_files = []
        elif line.strip():
            current_files.append(line.strip())

    if current_files:
        for a in current_files:
            for b in current_files:
                if a != b:
                    co_change[a][b] += 1

    # Per-file raw churn as the risk proxy
    churn_log = _git(
        repo, "log", f"--since={months * 30} days ago",
        "--numstat", "--pretty=format:COMMIT:%H",
    )
    file_churn: Counter = Counter()
    cur: list[str] = []
    cur_changes: list[tuple[int, int]] = []
    for line in churn_log.splitlines():
        if line.startswith("COMMIT:"):
            for f, (a, d) in zip(cur, cur_changes):
                file_churn[f] += (a + d)
            cur = []
            cur_changes = []
        elif line.strip():
            parts = line.split("\t")
            if len(parts) == 3:
                try:
                    add = int(parts[0]) if parts[0] != "-" else 0
                    dele = int(parts[1]) if parts[1] != "-" else 0
                except ValueError:
                    continue
                cur.append(parts[2])
                cur_changes.append((add, dele))
    if cur:
        for f, (a, d) in zip(cur, cur_changes):
            file_churn[f] += (a + d)

    out: dict[str, float] = {}
    for f, fn in coord_set:
        co = co_change.get(f)
        if not co:
            out[f"{f}:{fn}"] = 0.0
            continue
        total_weight = sum(co.values())
        # risk = weighted mean of co-changer churn, normalized by the max
        max_churn = max(file_churn.values()) if file_churn else 1
        risk_sum = sum(
            (cnt / total_weight) * (file_churn.get(co_file, 0) / max_churn)
            for co_file, cnt in co.items()
        )
        p = max(0.0, min(1.0, risk_sum))
        out[f"{f}:{fn}"] = p
    return out


# --- Combined prior ----------------------------------------------------------


def combined_prior(
    repo: Path,
    coords: Iterable[tuple[str, str]],
    weights: tuple[float, float, float] = (0.4, 0.3, 0.3),
) -> dict[str, float]:
    """Run all three priors and fuse with `weights`. v1 default matches
    the design document — bug-density weighted highest, churn and
    co-change tied."""
    coords_list = list(coords)
    a = bug_density_prior(repo, coords_list)
    b = churn_prior(repo, coords_list)
    c = co_change_prior(repo, coords_list)
    wa, wb, wc = weights
    out: dict[str, float] = {}
    for coord in a:
        out[coord] = max(0.0, min(1.0, wa * a[coord] + wb * b.get(coord, 0) + wc * c.get(coord, 0)))
    return out

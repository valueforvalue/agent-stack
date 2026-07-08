# consensus-hunter — Operations Manual

Operational guide for using `consensus-hunter` once it's in your hands.
Pairs with [`SKILL.md`](SKILL.md) (which describes the skill in agent
invocation terms) and [`../../docs/run-on-your-codebase.md`](../../docs/run-on-your-codebase.md) (top-level adoption guide).

This file is the method writeup: how to run a real calibration, how to
interpret the numbers, and how to avoid the pitfalls learned in the
django and dixiedata calibration runs.

## 1. What a calibration run produces

`python scripts/run_real_agent_calibration.py` consumes:

- N agent JSON files in `.consensus-hunter/captured/agent_*.json`
- `.consensus-hunter/eval_coords.json` with the eval manifest
- (optional) `.consensus-hunter/calibration.json` from a prior run for `--calibrate-data` mode

It writes `.consensus-hunter/calibration.json` containing:

- `consensus.*` — logit-averaged headline metrics (Brier, Skill Score, precision@K, lift over base).
- `per_agent` — per-agent Brier / Skill Score / Platt Skill Score / derived weight.
- `agreement_band_distribution` — count of coords in each band (`unanimous`, `majority`, `contested`, `single`).
- `top_5_highest_consensus` / `top_5_lowest_consensus` — first-line-thing to inspect.

The **headline number that maps to operational value is `precision@K`**
(K = number of known bugs in your eval universe). That tells you
"of the top-K coords the skill ranked, what fraction are real bugs?"
A precision@K of 0.95 means an LLM or human reviewer pointed at the
top of the list finds a real bug ~19/20 attempts. That's the "skill
ranks well" claim and it's the number to defend.

`Skill Score` is the *secondary* number; it tells you whether the
absolute scores carry information across runs. Reads `Brier / base-rate-brier`,
so a value of +0.5 means "agent cuts the Brier score in half vs
constant prediction." A value of 0.0 means "agent is no better than
guessing the global base rate for every coord."

## 2. The time-aware replay protocol

Calibration only works if it's *time-aware* — agents must never see
the bugs they're scored against. The protocol:

1. **Pick a knowledge cutoff.** A git commit hash. Pick this BEFORE
   you look at the post-cutoff history. (Commit `ecaac9e42f497be04ddc72dfebb6e397ccca9517`
   in django was our reference. For dixiedata we used `d395f47140d27c38457b2819fbfa283a46352e25`.)

2. **Extract held-out labels from the post-cutoff history.** Either:
   - **Keyword-match:** walk post-cutoff commits for `fix`, `bug`,
     `cve`, `bpo`, `sec` keywords. Resolve the diff to (file, function)
     pairs. Fast, recall-biased.
   - **CVE-anchored (higher quality):** walk the CVEfixes dataset
     for the project. Cross-reference post-cutoff CVE-disclosure
     timestamps to specific commits and their functions. Slower,
     precision-biased. Currently the dixiedata run uses keywords;
     django too.

3. **Walk the agent inputs from BEFORE the cutoff.** `git show <cutoff_sha>:<path>`
   for each (file, function) candidate. The agent never sees post-cutoff
   history because the working tree *is* the pre-cutoff state.

4. **Run the agents → aggregator → calibration.**

5. **Compare predictions to held-out labels.** Skill Score and
   precision@K are reported on the full eval universe; per-agent
   Skill Scores are computed against the *global* base rate (default
   0.5 for unreported coords; see §3).

The "did you do it right?" check: if your eval universe is class-
balanced (50/50 buggy/clean), and your agents are reasonable, expect
consensus Skill Score in the +0.05 to +0.30 range on a single-model
configuration, and `precision@K` between 0.7 and 1.0.

## 3. The per-agent base-rate artifact (LESSON LEARNED)

`per_agent_calibration` had a bug where, if agents only emit findings
on a class-imbalanced subset (e.g. only on suspected-buggy coords),
the legacy code computed a base rate *from that subset*. Result:
with heavy imbalance, the base-rate brier collapses, the agent's
own Brier looks bad by comparison, and Skill Score diverges into
meaningless negatives (we observed -4.6 in the first dixiedata run,
despite precision@K = 0.95).

**Fix (in framework since commit `add4df4`):**

```python
per_agent_calibration(
    per_agent_pairs,
    global_labels=labels,                # FULL universe, in eval order
    coords_evaluated=coords_evaluated,    # matching coord order
)
```

Missing coords default to 0.5 (the abstention prediction). The
`global_labels` vector provides the true base rate; the `coords_evaluated`
vector provides the order.

**Symptom of the artifact:** consensus Skill Score is positive
AND `precision@K` is high, but per-agent Skill Scores are deeply
negative. If you see this, you have an old run. Re-run with the
fix or use a current framework checkout.

**Regression test:** `tests/test_calibrate_subset_artifact.py` —
four tests, including the artifact trigger pattern. If you
modify `per_agent_calibration`, run this suite.

## 4. Single-model 5-agent convergence — `agreement_band` is dead weight

In both django and dixiedata calibration runs, all 36–40 coords
landed in the `unanimous` band. The reason: all 5 agents ran on the
same parent model with prompt-only reasoning differentiation. They
converged on tight scores.

`agreement_band` exists to surface disagreement *as a signal*. With
single-model configurations it carries no signal because there's
no real disagreement.

**Options for v1.1:**

- **Multi-model diversity:** `--model-family claude-sonnet-4.5,gpt-5-mini,llama-3`
  configures each agent through a different LLM API. Restores
  meaningful disagreement.
- **Score-spread regen:** within a single model, sample twice
  with different seeds and average; introduces variance but not
  principled disagreement.
- **Drop `agreement_band` from the headline output** until multi-model
  is the default.

We recommend option 1. The cost is higher but it produces the
operationally-distinct signal that motivated the band in the first
place.

## 5. Coordinates: your eval universe must be `consistent`-shaped

`per_agent_calibration(..., coords_evaluated=coords_evaluated)` requires
`coords_evaluated` and `global_labels` to be **the same length AND
match the agent findings' coord keys**. Mismatches:

- Agent reports on a coord not in `coords_evaluated` → ignored (the
  coord is outside the eval universe; aggregator skips it).
- Agent doesn't report on a coord in `coords_evaluated` → defaulted
  to 0.5 (abstention).

**In practice:** the agents often emit ~20 extra findings beyond the
eval universe (when the LLM reports on functions not in your sampled
clean pool). These are useful operationally (the agents are saying
"suspect this file:func") but they don't contribute to calibration
metrics. Don't be alarmed when you see 21/40 matching — that's
normal.

## 6. Per-agent weights: when to trust them

`derived_weights` in `calibration.json` are weights from
inverse-Brier, normalized to sum-to-`len(agents)`. An agent with a
Brier of 0.10 (great) gets weight ~1.2; an agent with Brier 0.25
(baseline) gets weight ~0.8. Agents worse than baseline get
`min_weight = 0.5`.

**Trust them when:**
- Total eval universe ≥ 30 coords (per-agent weight is noisy on
  small samples).
- The calibration set uses real held-out labels (not synthetic).
- All agents see the full universe (post-fix `per_agent_calibration`).

**Don't trust them when:**
- Eval universe < 20 coords. Per-agent weight is too noisy.
- Only one agent reports on a coord — common when agents have
  filtering preferences. That coord's signal can't be informed
  by inter-agent weighting.

## 7. Walk-through: reproducing the dixiedata result

The dixiedata calibration report at `.consensus-hunter/REPORT.md` on
dixiedata used:

- Cutoff commit `d395f47140d27c38457b2819fbfa283a46352e25` (2026-04-01).
- Window: 2026-04-01 → 2026-07-01.
- Target: `internal/appshell/`.
- 5 agents on the same parent model with prompt-only reasoning
  variation (the framework's default posture).
- Eval: 40 coords (20 known-buggy from post-cutoff `fix`-keyword
  commits + 20 sampled clean from the same module).

To reproduce: in the framework repo,

```bash
# 1. Pick the cutoff, build the eval universe
python scripts/build_held_out.py \
    --repo /path/to/dixiedata \
    --target internal/appshell \
    --since 2026-04-01 --until 2026-07-01 \
    --output /path/to/dixiedata/.consensus-hunter/eval_coords.json

# 2. Extract function bodies at cutoff
python scripts/extract_function_bodies.py \
    --repo /path/to/dixiedata \
    --cutoff d395f47140d27c38457b2819fbfa283a46352e25 \
    --eval /path/to/dixiedata/.consensus-hunter/eval_coords.json \
    --output /path/to/dixiedata/.consensus-hunter/function_bodies.json

# 3. Drive the 5 agents (each prompt is in
#    skills/consensus-hunter/presets/5-agent-preset.md). For an LLM-driven
#    run, the parent agent or operator invokes each agent with its evidence
#    slice and captures the JSON to .consensus-hunter/captured/agent_<id>.json.
#    Or, for a headless automation, replace the agent slots in this
#    scripts/run_real_agent_calibration.py with calls to your LLM SDK.

# 4. Run the calibration
python skills/consensus-hunter/scripts/run_real_agent_calibration.py \
    --repo /path/to/dixiedata \
    --emit /path/to/dixiedata/.consensus-hunter/calibration.json
```

(V0.1 caveat: the `build_held_out.py` and `extract_function_bodies.py`
scripts are written for the dixiedata session and live as
`scripts-tmp/` there. The pattern generalizes; a v0.2 cleanup moves
them into the framework.)

## 8. Anti-patterns (operational)

- **Run agents without a calibration harness.** Skill Score is a metric,
  not a feeling. If you can't reproduce the metric, you can't trust
  the rank.
- **Run calibration on a single-pass eval.** 30+ coords minimum;
  50+ for stable per-agent weight estimation.
- **Don't subtract post-cutoff history before the eval.** That's data
  leakage; the agents will see the bug they're supposed to find.
- **Don't share agent prompts across runs unless you intend to.** Each
  run should re-prompt fresh with the *current* cutoff's evidence slice.
- **Don't trust `agreement_band` on single-model runs.** See §4.
- **Don't skip the per-agent report.** If one agent is wildly better
  than the others on the calibration set, weight it accordingly.

## 9. What this doc does NOT cover

- **Multi-model agents.** v1.1 work; see §4.
- **Wider label sources** (CVEfixes import, SWE-Bench gold patches
  cross-reference). Currently keyword-match only. A v1.1 plan would
  import CVEfixes for `signing.py`, `crypto.py`, and `http.py` (in
  Python projects) and the GitHub Security Advisory DB for any
  language.
- **The historical risk ledger.** The skill's killer feature is the
  per-run `history/<timestamp>.json` archive, which provides
  per-coord drift over time — the Lehman §10 entropy alarm. This
  doc's calibration focuses on the static skill design; building
  the ledger is v1.1+ work.

## Cross-references

- [`SKILL.md`](SKILL.md) — how the agent-side skill is invoked.
- `USAGE.md` (top-level, adoption guide) — how to set the skill up for
  your codebase from the framework repo.
- `../../core/complexity.md` §6 (enforce boundaries) — why the test
  set for `per_agent_calibration` exists.
- `../../core/complexity.md` §10 (entropy as default) — the
  motivation for the historical risk ledger that's the *real*
  long-term value of this skill.

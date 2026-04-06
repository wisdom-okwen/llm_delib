# Incentivizing Revelation: Strategic Information Disclosure in Multi-Agent LLM Deliberation

**Do LLM agents strategically reveal private information when disclosure is costly?**

This codebase runs controlled experiments on multi-agent deliberation where agents hold *private* features about a case (patient, loan applicant, security incident, etc.), each feature carries a disclosure cost, and agents must collectively reach a binary YES/NO decision. The central experimental axis is the **incentive mechanism**: how reward is structured shapes what agents choose to reveal.


---

## Quick Start

```bash
pip install -r requirements.txt

export OPENAI_API_KEY="your-key-here"

# Sanity check: 2 scenarios, 1 run, sequential
python run.py --preset quick_test --incentive uniform

# Core comparison: uniform vs. contribution vs. oracle (3 runs each)
python run.py --incentive uniform contribution contribution_oracle --num-runs 3

# Full sweep across all conditions
python run.py --incentive uniform contribution contribution_oracle \
    counterfactual_contribution hybrid stake bid_to_speak \
    forced_sharing free_debate no_comm --num-runs 3

# Analyze and plot results
python analyze.py results/<timestamp>/ data/scenarios.json
```

---

## Research Design

Each experiment runs a **deliberation** on a structured scenario:

1. A case is split into private features distributed across N agents.
2. The moderator opens each round with a YES/NO stance and confidence score.
3. Agents decide which of their private features to disclose (paying the feature's cost).
4. After R rounds, the moderator makes a final decision; agents receive rewards.

The key manipulation is the **incentive mechanism** — how the reward pool is allocated — which creates different disclosure incentives. Under `uniform`, agents free-ride (cheap-talk equilibrium). Under `contribution`/`counterfactual_contribution`, agents are rewarded proportionally to the value of what they revealed.

### Three Core Claims

1. **Uniform incentives → systematic under-revelation** of decisive features (free-rider problem).
2. **Contribution-based incentives → partial repair**, increasing decisive surfacing rate and accuracy.
3. **Practical–oracle gap is measurable**: `contribution_oracle` sets the ceiling; the gap between `counterfactual_contribution` and the oracle quantifies how much value a practical mechanism leaves on the table.

### Variant Triplet Design

Each base scenario has two controlled variants for causal analysis:

| Variant | Change | Purpose |
|---------|--------|---------|
| `base` | Original scenario | Primary condition |
| `A_information_structure` | Evidence redistributed across agents (single-pivotal ↔ distributed-pivotal) | Isolates how information structure affects disclosure |
| `B_cost` | Decisive features cheap (1–2), misleading features expensive (4–6) | Isolates cost structure — reverses the natural confound |

---

## Incentive Conditions

| Condition | Description | Experimental Role |
|-----------|-------------|-------------------|
| `uniform` | Equal reward split if correct; disclosure costs deducted | Free-rider baseline |
| `contribution` | Split proportional to moderator-rated per-round contribution | Practical mechanism |
| `contribution_oracle` | Split proportional to posthoc decisive-feature credit | Oracle upper bound (unobservable in deployment) |
| `counterfactual_contribution` | Leave-one-out moderator confidence shift (CMC) | Principled practical mechanism |
| `hybrid` | `alpha × uniform + (1-alpha) × contribution` | Stability floor + incentive blend |
| `stake` | Agents bet a confidence stake before deliberation begins | Costly signaling |
| `bid_to_speak` | Per-turn budget spending; pool multiplied and split | Per-turn costly signaling |
| `free_debate` | No disclosure costs; free-form communication | Cost-free baseline |
| `forced_sharing` | All agents disclose all features | Perfect-information upper bound |
| `no_comm` | Independent majority vote; no communication | No-collaboration baseline |

---

## Architecture

```
IncentivizingRevelation/
├── config.py        Config dataclass + presets (model, incentive, costs, ablations)
├── llm.py           OpenAI-compatible LLM client with exponential-backoff retry
├── prompts.py       All prompt templates (agent, moderator, bid elicitation)
├── data.py          Dataset loading → Scenario / Feature objects + taxonomy properties
├── agents.py        Agent (private features, disclosure decisions) + Moderator
├── incentives.py    Reward computation for all 10 conditions
├── engine.py        Deliberation loop: rounds → agent turns → final decision
├── metrics.py       Aggregate metrics, calibration, Wilcoxon significance tests
├── run.py           CLI entry point; parallel execution, JSONL incremental save/resume
├── analyze.py       Post-hoc plots and tables
└── data/
    ├── scenarios.json                              60 base scenarios (30 YES / 30 NO)
    ├── balanced_variants_A_information_structure.json   60 info-structure variants
    ├── balanced_variants_B_cost.json               60 cost-inverted variants
    └── scenarios_merged.json                       180 scenarios (all three combined)
```

### Data Flow

```
Scenario ──→ Agents (private feature splits) ──→ Deliberation Engine
                                                        │
                    ┌───────────────────────────────────┘
                    │  for each round:
                    │    1. Moderator announces stance + confidence
                    │    2. Agents speak (shuffled round-robin)
                    │       - decide which private features to disclose
                    │       - output <disclosed> block (structured tracking)
                    │       - pay token cost for prose length (if token_cost > 0)
                    │    3. Moderator summarizes; rates contributions if needed
                    │
                    └──→ Final Decision ──→ Reward Computation ──→ Metrics
```

### Key Design Choices

- **Structured disclosure.** Every agent message ends with a `<disclosed>` XML block listing revealed features. Feature values only reach other agents through this block — prose leakage is auto-detected and charged.
- **Moderator as confidence tracker.** The moderator announces a YES/NO stance with confidence (0–1) each round, giving agents an observable signal to condition disclosure decisions on.
- **Two independent cost axes.** Feature disclosure costs (1–5 points) and per-token costs (`token_cost`, default 0) vary independently.
- **CMC scoring.** Enabled via `--enable-cmc`: re-runs moderator evaluation with each agent's message removed (leave-one-out), computing signed confidence deltas as credit signal. Adds N×R extra LLM calls.
- **Novelty tracking.** Per-agent fraction of disclosures that introduced information not yet publicly known from prior agents in the same round.
- **Speaking position.** Each agent's 1-indexed within-round position is recorded, enabling order-sensitivity analysis.
- **Parse-failure tracking.** `Moderator.parse_failures` records `stance_unknown`, `final_fallback`, `final_unknown`, and `bid_fallback` counts; `final_decision` retries up to 2 times.

---

## Dataset

### Structure

180 scenarios across 3 files, all perfectly balanced (50% YES / 50% NO).

| File | Count | Description |
|------|-------|-------------|
| `data/scenarios.json` | 60 | Base scenarios (default) |
| `data/balanced_variants_A_information_structure.json` | 60 | Info-structure perturbations |
| `data/balanced_variants_B_cost.json` | 60 | Cost-inverted variants |
| `data/scenarios_merged.json` | 180 | All three combined (use `--preset full_merged`) |

Domains: healthcare, finance, cybersecurity, operations, environmental, legal, and more.

### Scenario Format

```json
{
  "id": "S01_diabetes_escalate",
  "domain": "healthcare",
  "question": "Escalate for near-term diabetes intervention/testing?",
  "label": "NO",
  "scenario_type": "distributed_pivotal",
  "decision_type": "risk_threshold",
  "label_confidence": 0.86,
  "full_view": {
    "HbA1c_pct": {
      "value": 6.7,
      "cost": 5,
      "signal_strength": "strong",
      "tag": "decisive"
    },
    "BMI": {
      "value": 29.7,
      "cost": 2,
      "signal_strength": "weak"
    }
  },
  "agents_structured": {
    "A1": {"Age": 44, "Sex": "Male", "BP": "138/88"},
    "A7": {"HbA1c_pct": 6.7}
  },
  "information_structure": {
    "type": "distributed_pivotal",
    "num_pivotal_agents": 2,
    "has_omniscient_agent": false,
    "misleading_density": "medium"
  },
  "cost_model": {
    "type": "privacy",
    "interpretation": "Higher-cost features correspond to lab access and protected health information."
  },
  "counterfactuals": {
    "without_pivotal": "UNCERTAIN",
    "with_partial_pivotal": "UNCERTAIN",
    "with_all": "NO"
  }
}
```

### Feature Metadata

- **cost** (1–5): points deducted on disclosure
- **signal_strength**: `weak`, `weak/noisy`, `weak/medium`, `medium`, `strong`, `misleading`
- **tag**: `"decisive"` (changes the correct answer if withheld), `"misleading"` (looks relevant but misleads), or absent (neutral)

### Scenario Taxonomy

Computed properties on each `Scenario` object (used for subgroup analyses):

| Property | Values | Description |
|----------|--------|-------------|
| `decisive_cost_tier` | `low` / `medium` / `high` | Mean cost of decisive features |
| `num_decisive` | integer | Count of decisive features |
| `decisive_redundancy` | `single_holder` / `multi_holder` | How many agents hold decisive features |
| `misleading_pressure` | `none` / `weak` / `strong` | Misleading feature count × inverse cost |
| `information_structure.type` | `single_pivotal` / `distributed_pivotal` / `diffuse` | How evidence is distributed |

### Variant Files

Variant scenarios add `variant_of` (base scenario ID), `variant_type`, and `variant_description`. All share a `variant_group` key with their base (derived from `variant_of` at load time), enabling matched triplet analysis.

```json
{
  "id": "S01_diabetes_escalate_varB_cost",
  "variant_of": "S01_diabetes_escalate",
  "variant_type": "B_cost",
  "variant_description": "Cost perturbation: decisive/strong evidence is cheaper to reveal, while misleading or weak noisy cues are more expensive.",
  "cost_model": {
    "type": "counterfactual_reweighted_costs",
    "interpretation": "Lowers disclosure cost of high-value evidence; raises cost of misleading or low-value cues."
  }
}
```

---

## Metrics

| Metric | Description |
|--------|-------------|
| `accuracy` | Fraction of correct group decisions |
| `balanced_accuracy` | Mean of sensitivity and specificity (robust to label imbalance) |
| `decisive_surfacing_rate` | Fraction of decisive features disclosed during deliberation |
| `selective_disclosure_index` | Decisive disclosures / total disclosures |
| `decisive_holder_disclosure_rate` | Rate at which agents holding decisive features disclose them |
| `non_holder_disclosure_rate` | Disclosure rate for agents without decisive features (free-riding baseline) |
| `free_riding_rate` | Fraction of agents who disclosed nothing across the full deliberation |
| `round_free_riding_rate` | Fraction of individual agent turns with no disclosure |
| `time_to_decisive_surfacing` | Mean first round in which a decisive feature appears |
| `novelty_rate` | Mean fraction of disclosures that introduced new (not-yet-public) information |
| `judge_oracle_correlation` | Spearman r between moderator-rated and oracle contribution scores |
| `misleading_before_wrong_rate` | Rate of misleading disclosure preceding a wrong final decision |
| `counterfactual_sufficiency_rate` | Fraction of cases where disclosed info was sufficient for the ground-truth-achievable decision |
| `accuracy_per_comm_token` | Task accuracy per communication token (efficiency frontier) |

Significance testing uses paired Wilcoxon signed-rank tests on scenario-level aggregated outcomes (matched design).

---

## CLI Reference

```bash
python run.py [OPTIONS]

# Dataset
  --data-path PATH           Path to scenarios JSON (default: data/scenarios.json)
  --scenarios ID [ID ...]    Run only specific scenario IDs
  --preset NAME              Apply a named preset (see below)

# Incentive conditions (one or more)
  --incentive COND [COND ...]
    uniform contribution contribution_oracle counterfactual_contribution
    hybrid stake bid_to_speak free_debate forced_sharing no_comm

# Deliberation parameters
  --num-runs N               Independent runs per scenario (default: 3)
  --num-rounds N             Deliberation rounds per run (default: 3)
  --num-agents N             Override agent count from data
  --token-cost FLOAT         Per-token charge to agents (default: 0)
  --hybrid-alpha FLOAT       Blend weight for hybrid mechanism (default: 0.5)
  --enable-cmc               Enable counterfactual marginal contribution scoring
                             (adds N×R extra LLM calls per scenario)

# Model
  --model MODEL_ID           e.g. gpt-4o, gpt-4o-mini
  --api-key-env VAR          Environment variable holding the API key
  --base-url URL             OpenAI-compatible base URL (for Together, Ollama, etc.)

# Ablations
  --ablate-no-rules          Strip DECISION RULES block from agent prompt
  --neutral-wording          Group-benefit framing instead of self-interested framing
  --no-shuffle               Fixed (not randomized) agent speaking order

# Execution
  --max-concurrent N         Parallel scenario threads (default: 4)
  --run-dir PATH             Resume from an existing results directory
  --no-resume                Ignore cached results; rerun everything
  --seed N                   Random seed (default: 42)
  --quiet                    Suppress per-scenario log lines
```

### Presets

| Preset | Description |
|--------|-------------|
| `quick_test` | 2 scenarios, 1 run, sequential — fast sanity check |
| `openai_mini` | GPT-4o-mini via OpenAI API |
| `llama_together` | Llama 3.3 70B via Together AI |
| `qwen_together` | Qwen 2.5 72B via Together AI |
| `local_ollama` | Local model via Ollama |
| `ablate_no_rules` | Remove decision rules from prompts |
| `neutral_wording` | Group-benefit prompt framing (ablation) |
| `full_merged` | Load all 180 scenarios from `scenarios_merged.json` |

---

## Using Open-Weight Models

```bash
# Llama 3.3 70B via Together AI
export TOGETHER_API_KEY="your-key-here"
python run.py --preset llama_together --incentive uniform contribution

# Qwen 2.5 72B via Together AI
python run.py --preset qwen_together --incentive uniform contribution

# Local model via Ollama
ollama serve   # in a separate terminal
python run.py --preset local_ollama --incentive uniform
```

---

## Output

Each run produces a timestamped directory:

```
results/<timestamp>/
├── config.json                  Full experiment configuration snapshot
├── results_<condition>.jsonl    Incremental per-result log (crash-safe; written as each scenario completes)
├── results_<condition>.json     Finalized full deliberation logs
└── metrics.json                 Aggregate metrics across all conditions
```

To resume after a crash, rerun the same command with `--run-dir results/<timestamp>/`. Completed scenario/run pairs are skipped automatically.

Each result entry contains: scenario ID, final decision, correctness flag, per-agent disclosure logs with feature names/costs/round, speaking positions, reward payoffs, parse failure counts, and API usage.

---

## Ablations

Two prompt-level ablations are supported as independent axes:

| Flag | What changes | Purpose |
|------|-------------|---------|
| `--ablate-no-rules` | Removes the `DECISION RULES` block from agent prompts | Tests whether incentive effects are driven by explicit rule coaching |
| `--neutral-wording` | Replaces self-interested framing ("maximize your payoff") with group-benefit framing ("help the group reach the correct decision") | Isolates mechanism effect from prompt framing effect |

These can be combined with any incentive condition.

---

## Extending

**Add a new incentive condition:**
1. Add reward logic to `incentives.py` (`compute_payoffs` dispatch)
2. Add the agent-facing description to `INCENTIVE_DESCRIPTIONS` in `prompts.py`
3. Add the name to the `Literal` type in `config.py` and the `--incentive` choices in `run.py`

**Add a new communication protocol:**
`engine.py` dispatches to `_run_no_comm_vote`, `_run_free_debate`, `_run_forced_sharing`, or the structured round loop. New protocols plug in as additional dispatch targets; `Agent` and `Moderator` are protocol-agnostic.

**Use results as training data:**
The structured logs capture every agent turn with disclosure decisions, costs, payoffs, and outcomes — suitable for DPO training on preferred (decisive feature disclosed) vs. rejected (decisive feature withheld or noise shared) paired examples.

---


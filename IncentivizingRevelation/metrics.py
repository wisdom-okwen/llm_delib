"""
Metrics computation.

Computes aggregate metrics across multiple deliberation results.
"""

import numpy as np
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from scipy import stats

from engine import DeliberationResult
from data import Scenario


@dataclass
class ConditionMetrics:
    condition: str
    n_scenarios: int
    n_correct: int

    accuracy: float
    decisive_surfacing_rate: float
    selective_disclosure_index: float
    free_riding_rate: float
    round_free_riding_rate: float

    mean_tokens: float
    mean_communication_tokens: float
    mean_disclosure_cost: float
    accuracy_per_comm_token: float
    accuracy_per_disclosure_cost: float

    misleading_before_wrong_rate: float
    misleading_preceded_decisive_rate: float

    accuracy_ci: tuple[float, float]
    surfacing_by_cost: dict[int, float]
    per_domain: dict[str, float]

    # Agent-level calibration for decisive-feature holders
    decisive_holder_disclosure_rate: float  # rate at which holders of decisive features disclose them
    non_holder_disclosure_rate: float       # baseline: rate of disclosure for non-decisive holders

    # Across-scenario variance (aggregate to one mean per scenario, then take std)
    std_accuracy: float
    std_decisive_surfacing_rate: float

    # New metrics for paper
    time_to_decisive_surfacing: float        # mean first round decisive feature appears (nan if never)
    novelty_rate: float                      # mean fraction of disclosures that are novel (not yet public)
    judge_oracle_correlation: float          # Spearman r between moderator and oracle contribution scores

    # Label-balance-robust metrics
    balanced_accuracy: float                 # mean of per-class accuracy (robust to label imbalance)
    counterfactual_sufficiency_rate: float   # fraction where disclosed info was sufficient to reach counterfactual-with_all label


def compute_metrics(
    results: list[DeliberationResult],
    scenarios: Optional[list[Scenario]] = None,
) -> ConditionMetrics:
    n = len(results)
    if n == 0:
        raise ValueError("No results to compute metrics over")

    scenario_map = {s.id: s for s in scenarios} if scenarios else {}

    # ── Core metrics ────────────────────────────────────────────────────
    n_correct = sum(1 for r in results if r.is_correct)
    accuracy = n_correct / n

    surfacing_rates = [r.decisive_surfacing_rate for r in results]
    mean_surfacing = float(np.mean(surfacing_rates)) if surfacing_rates else 0.0

    # Scenario-level aggregation for variance (aggregate runs → one mean per scenario)
    scenario_acc_groups: dict[str, list[float]] = defaultdict(list)
    scenario_dsr_groups: dict[str, list[float]] = defaultdict(list)
    for r in results:
        scenario_acc_groups[r.scenario_id].append(float(r.is_correct))
        scenario_dsr_groups[r.scenario_id].append(r.decisive_surfacing_rate)
    scenario_acc_means = [float(np.mean(v)) for v in scenario_acc_groups.values()]
    scenario_dsr_means = [float(np.mean(v)) for v in scenario_dsr_groups.values()]
    std_acc = float(np.std(scenario_acc_means)) if len(scenario_acc_means) > 1 else 0.0
    std_dsr = float(np.std(scenario_dsr_means)) if len(scenario_dsr_means) > 1 else 0.0

    # Selective disclosure index
    total_decisive_disclosed = 0
    total_features_disclosed = 0
    for r in results:
        scenario = scenario_map.get(r.scenario_id)
        decisive_set = set(scenario.decisive_features) if scenario else set()
        for aid, feats in r.agent_disclosures.items():
            total_features_disclosed += len(feats)
            total_decisive_disclosed += len(set(feats) & decisive_set)

    sdi = total_decisive_disclosed / total_features_disclosed if total_features_disclosed > 0 else 0.0

    # Scenario-level free-riding
    total_agents = 0
    free_riders = 0
    for r in results:
        for aid, feats in r.agent_disclosures.items():
            total_agents += 1
            if len(feats) == 0:
                free_riders += 1
    free_riding_rate = free_riders / total_agents if total_agents > 0 else 0.0

    # Round-level free-riding
    total_turns = 0
    empty_turns = 0
    for r in results:
        for rnd in r.rounds:
            turns = rnd.agent_turns if hasattr(rnd, "agent_turns") else rnd.get("agent_turns", [])
            for t in turns:
                fd = t.get("features_disclosed", {}) if isinstance(t, dict) else t.features_disclosed
                total_turns += 1
                if not fd:
                    empty_turns += 1
    round_free_riding_rate = empty_turns / total_turns if total_turns > 0 else 0.0

    # ── Cost metrics ────────────────────────────────────────────────────
    tokens = [r.total_tokens for r in results]
    comm_tokens = [getattr(r, "total_communication_tokens", r.total_tokens) for r in results]
    costs = [r.total_disclosure_cost for r in results]
    mean_tokens = float(np.mean(tokens))
    mean_comm_tokens = float(np.mean(comm_tokens))
    mean_cost = float(np.mean(costs))
    acc_per_comm = accuracy / mean_comm_tokens if mean_comm_tokens > 0 else 0.0
    acc_per_disc = accuracy / mean_cost if mean_cost > 0 else 0.0

    # ── Bootstrap CI ────────────────────────────────────────────────────
    rng = np.random.default_rng(42)
    correct_vec = np.array([r.is_correct for r in results], dtype=float)
    if n >= 5:
        boot_accs = [rng.choice(correct_vec, size=n, replace=True).mean() for _ in range(2000)]
        ci_lo, ci_hi = float(np.percentile(boot_accs, 2.5)), float(np.percentile(boot_accs, 97.5))
    else:
        ci_lo, ci_hi = accuracy, accuracy

    # ── Surfacing rate by feature cost ──────────────────────────────────
    surfacing_by_cost: dict[int, list[float]] = defaultdict(list)
    for r in results:
        scenario = scenario_map.get(r.scenario_id)
        if not scenario:
            continue
        all_disclosed = set()
        for feats in r.agent_disclosures.values():
            all_disclosed.update(feats)
        for fname, feat in scenario.features.items():
            surfacing_by_cost[feat.cost].append(1.0 if fname in all_disclosed else 0.0)

    surfacing_by_cost_agg = {
        cost: float(np.mean(vals)) for cost, vals in sorted(surfacing_by_cost.items())
    }

    # ── Misleading influence ────────────────────────────────────────────
    mbw_rate = float(np.mean([float(getattr(r, "misleading_before_wrong", False)) for r in results]))
    mpd_rate = float(np.mean([float(getattr(r, "misleading_preceded_decisive", False)) for r in results]))

    # ── Per-domain accuracy ─────────────────────────────────────────────
    domain_correct: dict[str, list[float]] = defaultdict(list)
    for r in results:
        domain_correct[r.domain].append(float(r.is_correct))
    per_domain = {d: float(np.mean(v)) for d, v in domain_correct.items()}

    # ── Agent-level calibration: decisive-feature holders ───────────────
    # For each agent that HOLDS a decisive feature, did they disclose it?
    decisive_holder_disclosures = 0
    decisive_holder_total = 0
    non_holder_disclosures = 0
    non_holder_total = 0

    for r in results:
        scenario = scenario_map.get(r.scenario_id)
        if not scenario:
            continue
        decisive_set = set(scenario.decisive_features)
        agents_with_decisive = set(getattr(r, "agents_holding_decisive", []))

        for aid, feats_disclosed in r.agent_disclosures.items():
            feats_disclosed_set = set(feats_disclosed)
            if aid in agents_with_decisive:
                # This agent holds decisive features — did they disclose them?
                held_decisive = set(scenario.agent_features.get(aid, {}).keys()) & decisive_set
                for df in held_decisive:
                    decisive_holder_total += 1
                    if df in feats_disclosed_set:
                        decisive_holder_disclosures += 1
            else:
                # Non-decisive holder — what fraction of their features did they disclose?
                held = set(scenario.agent_features.get(aid, {}).keys())
                non_holder_total += len(held)
                non_holder_disclosures += len(feats_disclosed_set & held)

    dh_rate = decisive_holder_disclosures / decisive_holder_total if decisive_holder_total > 0 else 0.0
    nh_rate = non_holder_disclosures / non_holder_total if non_holder_total > 0 else 0.0

    # ── Time-to-decisive-surfacing ───────────────────────────────────────
    # Mean first round in which any decisive feature was surfaced.
    # Results with no decisive surfacing are excluded (they cannot contribute a finite value).
    first_decisive_rounds = [
        getattr(r, "first_decisive_round", None) for r in results
        if getattr(r, "first_decisive_round", None) is not None
    ]
    time_to_decisive = float(np.mean(first_decisive_rounds)) if first_decisive_rounds else float("nan")

    # ── Novelty rate ─────────────────────────────────────────────────────
    # Fraction of disclosures that were novel (not already publicly known from earlier agents).
    all_novelty = []
    for r in results:
        rates = getattr(r, "agent_novelty_rates", {})
        all_novelty.extend(v for v in rates.values())
    novelty_rate = float(np.mean(all_novelty)) if all_novelty else 0.0

    # ── Judge–oracle correlation ─────────────────────────────────────────
    # Spearman rank correlation between moderator-rated contribution scores and
    # posthoc oracle decisive-feature scores, pooled across all results.
    judge_scores, oracle_scores = [], []
    for r in results:
        contrib = getattr(r, "contribution_scores", {})
        posthoc = getattr(r, "posthoc_contribution_scores", {})
        for aid in set(contrib) & set(posthoc):
            judge_scores.append(contrib[aid])
            oracle_scores.append(posthoc[aid])
    if len(judge_scores) >= 5:
        try:
            jo_corr = float(stats.spearmanr(judge_scores, oracle_scores).correlation)
        except Exception:
            jo_corr = float("nan")
    else:
        jo_corr = float("nan")

    # ── Balanced accuracy ────────────────────────────────────────────────
    # Mean of sensitivity (YES recall) and specificity (NO recall)
    correct_vec_list = [float(r.is_correct) for r in results]
    gt_yes = [i for i, r in enumerate(results) if r.ground_truth.upper() == "YES"]
    gt_no  = [i for i, r in enumerate(results) if r.ground_truth.upper() != "YES"]
    sensitivity = float(np.mean([correct_vec_list[i] for i in gt_yes])) if gt_yes else 0.0
    specificity = float(np.mean([correct_vec_list[i] for i in gt_no]))  if gt_no  else 0.0
    balanced_acc = (sensitivity + specificity) / 2.0

    # ── Counterfactual sufficiency rate ─────────────────────────────────
    # Fraction of results where decisive features were surfaced AND the final
    # decision matches the counterfactual with_all label.
    cf_sufficient = []
    for r in results:
        scenario = scenario_map.get(r.scenario_id)
        if not scenario or not scenario.counterfactuals:
            continue
        cf_with_all = scenario.counterfactuals.get("with_all", "").upper()
        if not cf_with_all:
            continue
        decisive_surfaced = r.decisive_surfacing_rate > 0.5
        decision_matches_cf = (
            r.final_decision.get("decision", "").upper() == cf_with_all
            if isinstance(r.final_decision, dict) else False
        )
        cf_sufficient.append(float(decisive_surfaced and decision_matches_cf))
    cf_sufficiency = float(np.mean(cf_sufficient)) if cf_sufficient else float("nan")

    # ── Assemble ────────────────────────────────────────────────────────
    condition = results[0].incentive if results else "unknown"

    return ConditionMetrics(
        condition=condition, n_scenarios=n, n_correct=n_correct,
        accuracy=accuracy, decisive_surfacing_rate=float(mean_surfacing),
        selective_disclosure_index=sdi,
        free_riding_rate=free_riding_rate, round_free_riding_rate=round_free_riding_rate,
        mean_tokens=mean_tokens, mean_communication_tokens=mean_comm_tokens,
        mean_disclosure_cost=mean_cost,
        accuracy_per_comm_token=float(acc_per_comm),
        accuracy_per_disclosure_cost=float(acc_per_disc),
        misleading_before_wrong_rate=mbw_rate,
        misleading_preceded_decisive_rate=mpd_rate,
        accuracy_ci=(ci_lo, ci_hi),
        surfacing_by_cost=surfacing_by_cost_agg, per_domain=per_domain,
        decisive_holder_disclosure_rate=dh_rate,
        non_holder_disclosure_rate=nh_rate,
        std_accuracy=std_acc,
        std_decisive_surfacing_rate=std_dsr,
        time_to_decisive_surfacing=time_to_decisive,
        novelty_rate=novelty_rate,
        judge_oracle_correlation=jo_corr,
        balanced_accuracy=balanced_acc,
        counterfactual_sufficiency_rate=cf_sufficiency,
    )


def disclosure_calibration(
    results: list[DeliberationResult],
    scenarios: list[Scenario],
) -> dict:
    """Correlation between feature signal strength and disclosure rate."""
    scenario_map = {s.id: s for s in scenarios}
    strength_map = {
        "weak": 1, "weak/noisy": 1, "weak/medium": 2,
        "medium": 3, "strong": 4, "misleading": 0,
        "misleading (reassuring)": 0,
    }

    records = []
    for r in results:
        scenario = scenario_map.get(r.scenario_id)
        if not scenario:
            continue
        all_disclosed = set()
        for feats in r.agent_disclosures.values():
            all_disclosed.update(feats)
        for fname, feat in scenario.features.items():
            records.append({
                "signal_ordinal": strength_map.get(feat.signal_strength, 1),
                "cost": feat.cost,
                "disclosed": fname in all_disclosed,
                "value_to_cost": strength_map.get(feat.signal_strength, 1) / max(feat.cost, 1),
            })

    if not records:
        return {"n_features": 0}

    signals = np.array([r["signal_ordinal"] for r in records])
    disclosed = np.array([float(r["disclosed"]) for r in records])
    v2c = np.array([r["value_to_cost"] for r in records])

    return {
        "n_features": len(records),
        "correlation_signal_disclosure": float(np.corrcoef(signals, disclosed)[0, 1]) if len(records) > 2 else None,
        "correlation_v2c_disclosure": float(np.corrcoef(v2c, disclosed)[0, 1]) if len(records) > 2 else None,
        "overall_disclosure_rate": float(disclosed.mean()),
        "disclosure_rate_by_strength": {
            s: float(disclosed[signals == v].mean())
            for s, v in [("weak", 1), ("medium", 3), ("strong", 4), ("misleading", 0)]
            if (signals == v).any()
        },
    }


def compute_pairwise_significance(
    results_by_condition: dict[str, list[DeliberationResult]],
) -> dict[str, dict]:
    """Paired Wilcoxon signed-rank tests on scenario-level aggregated outcomes.

    Each scenario may appear multiple times (one per run). We first aggregate
    to a single mean per scenario, then run a paired Wilcoxon signed-rank test
    on the matched scenario means. This respects the matched design (every
    condition sees the same 120 scenarios) and accounts for within-scenario
    correlation across runs.
    """
    conditions = list(results_by_condition.keys())
    pairwise: dict[str, dict] = {}

    def _scenario_agg(
        results: list[DeliberationResult], key_fn
    ) -> dict[str, float]:
        groups: dict[str, list[float]] = defaultdict(list)
        for r in results:
            groups[r.scenario_id].append(key_fn(r))
        return {sid: float(np.mean(vals)) for sid, vals in groups.items()}

    def _fr_rate(r: DeliberationResult) -> float:
        d = r.agent_disclosures
        return sum(1 for f in d.values() if len(f) == 0) / len(d) if d else 0.0

    def _wilcoxon_paired(a_map: dict, b_map: dict, common: list) -> dict:
        diffs = [a_map[s] - b_map[s] for s in common]
        if all(d == 0 for d in diffs):
            return {"test": "Wilcoxon_paired", "stat": 0.0, "p": 1.0,
                    "sig": False, "n_pairs": len(common)}
        try:
            stat, p = stats.wilcoxon(diffs, alternative="two-sided")
            return {"test": "Wilcoxon_paired", "stat": float(stat), "p": float(p),
                    "sig": p < 0.05, "n_pairs": len(common)}
        except ValueError as e:
            return {"test": "Wilcoxon_paired", "stat": 0.0, "p": 1.0,
                    "sig": False, "n_pairs": len(common), "note": str(e)}

    for i, cond_a in enumerate(conditions):
        for cond_b in conditions[i + 1:]:
            res_a = results_by_condition[cond_a]
            res_b = results_by_condition[cond_b]
            key = f"{cond_a}_vs_{cond_b}"

            acc_a = _scenario_agg(res_a, lambda r: float(r.is_correct))
            acc_b = _scenario_agg(res_b, lambda r: float(r.is_correct))
            dsr_a = _scenario_agg(res_a, lambda r: r.decisive_surfacing_rate)
            dsr_b = _scenario_agg(res_b, lambda r: r.decisive_surfacing_rate)
            fr_a  = _scenario_agg(res_a, _fr_rate)
            fr_b  = _scenario_agg(res_b, _fr_rate)

            common = sorted(set(acc_a) & set(acc_b))
            if len(common) < 5:
                pairwise[key] = {"note": f"Only {len(common)} matched scenarios; skipping"}
                continue

            pairwise[key] = {
                "accuracy":    _wilcoxon_paired(acc_a, acc_b, common),
                "decisive":    _wilcoxon_paired(dsr_a, dsr_b, common),
                "free_riding": _wilcoxon_paired(fr_a,  fr_b,  common),
            }

    return pairwise


def format_comparison_table(conditions: list[ConditionMetrics]) -> str:
    lines = []

    # Table 1: Core outcomes
    h1 = (f"{'Condition':<14} {'Acc':>5} {'BalAcc':>7} {'±SD':>5} {'95% CI':>14} "
          f"{'Decis%':>6} {'±SD':>5} {'SDI':>5} {'DH%':>5} {'NH%':>5} "
          f"{'FR%':>5} {'RdFR%':>6}")
    lines.extend([h1, "-" * len(h1)])
    for m in conditions:
        ci = f"[{m.accuracy_ci[0]:.2f},{m.accuracy_ci[1]:.2f}]"
        lines.append(
            f"{m.condition:<14} {m.accuracy:>5.2f} {m.balanced_accuracy:>7.2f} "
            f"{m.std_accuracy:>5.2f} {ci:>14} "
            f"{m.decisive_surfacing_rate:>6.2f} {m.std_decisive_surfacing_rate:>5.2f} "
            f"{m.selective_disclosure_index:>5.2f} "
            f"{m.decisive_holder_disclosure_rate:>5.2f} {m.non_holder_disclosure_rate:>5.2f} "
            f"{m.free_riding_rate:>5.2f} {m.round_free_riding_rate:>6.2f}"
        )
    lines.append("±SD = across-scenario std dev | BalAcc = balanced accuracy (mean sensitivity+specificity) | "
                 "DH% = decisive-feature holders' disclosure rate | "
                 "NH% = non-decisive holders' rate")

    # Table 2: Cost & efficiency
    lines.append("")
    h2 = (f"{'Condition':<14} {'CommTok':>8} {'DiscCost':>9} "
          f"{'Acc/CTok':>10} {'Acc/Cost':>10} "
          f"{'MisWrng%':>8} {'MisFrst%':>8}")
    lines.extend([h2, "-" * len(h2)])
    for m in conditions:
        lines.append(
            f"{m.condition:<14} {m.mean_communication_tokens:>8.0f} "
            f"{m.mean_disclosure_cost:>9.1f} "
            f"{m.accuracy_per_comm_token:>10.6f} {m.accuracy_per_disclosure_cost:>10.4f} "
            f"{m.misleading_before_wrong_rate:>8.2f} {m.misleading_preceded_decisive_rate:>8.2f}"
        )

    # Table 3: Information quality
    lines.append("")
    h3 = (f"{'Condition':<14} {'T2Decis':>8} {'Novelty':>8} {'JOcorr':>7}")
    lines.extend([h3, "-" * len(h3)])
    for m in conditions:
        t2d = f"{m.time_to_decisive_surfacing:.2f}" if not (
            isinstance(m.time_to_decisive_surfacing, float)
            and m.time_to_decisive_surfacing != m.time_to_decisive_surfacing  # nan check
        ) else "nan"
        joc = f"{m.judge_oracle_correlation:.3f}" if not (
            isinstance(m.judge_oracle_correlation, float)
            and m.judge_oracle_correlation != m.judge_oracle_correlation
        ) else "nan"
        lines.append(
            f"{m.condition:<14} {t2d:>8} {m.novelty_rate:>8.3f} {joc:>7}"
        )
    lines.append("T2Decis = mean first round decisive feature surfaced | "
                 "Novelty = novel disclosure fraction | JOcorr = judge-oracle Spearman r")

    return "\n".join(lines)

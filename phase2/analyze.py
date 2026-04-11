#!/usr/bin/env python3
"""
Post-hoc analysis and visualization.

Usage:
    python analyze.py results/20260305_143000/
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats


COLORS = {
    "uniform": "#4C72B0",
    "contribution": "#55A868",
    "contribution_oracle": "#2ca02c",
    "counterfactual_contribution": "#1f77b4",
    "hybrid": "#ff7f0e",
    "stake": "#C44E52",
    "bid_to_speak": "#e377c2",
    "free_debate": "#8172B2",
    "forced_sharing": "#17becf",
    "no_comm": "#CCB974",
}


def load_results(results_dir: Path) -> dict[str, list[dict]]:
    by_condition = {}
    for fpath in sorted(results_dir.glob("results_*.json")):
        condition = fpath.stem.replace("results_", "")
        with open(fpath) as f:
            by_condition[condition] = json.load(f)
    return by_condition


def _bootstrap_ci(values, n_boot=2000, alpha=0.05):
    arr = np.array(values, dtype=float)
    if len(arr) < 3:
        return np.mean(arr), np.mean(arr), np.mean(arr)
    boots = [np.mean(np.random.choice(arr, len(arr))) for _ in range(n_boot)]
    lo, hi = np.percentile(boots, [100*alpha/2, 100*(1-alpha/2)])
    return np.mean(arr), lo, hi


def plot_accuracy_comparison(by_condition, output_dir):
    fig, ax = plt.subplots(figsize=(10, 5))
    conditions = list(by_condition.keys())
    accs, errs = [], []
    for cond in conditions:
        correct = [r["is_correct"] for r in by_condition[cond]]
        mean, lo, hi = _bootstrap_ci(correct)
        accs.append(mean)
        errs.append([mean - lo, hi - mean])

    x = np.arange(len(conditions))
    bar_colors = [COLORS.get(c, "#888") for c in conditions]
    bars = ax.bar(x, accs, color=bar_colors, edgecolor="white", linewidth=1.5)
    ax.errorbar(x, accs, yerr=np.array(errs).T, fmt="none", color="black", capsize=5)
    ax.set_ylabel("Group Accuracy")
    ax.set_title("Group Decision Accuracy by Incentive Structure")
    ax.set_ylim(0, 1.15)
    ax.set_xticks(x)
    ax.set_xticklabels(conditions, rotation=45, ha="right", fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for bar, acc in zip(bars, accs):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()+0.03,
                f"{acc:.2f}", ha="center", fontsize=10, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_dir / "accuracy_comparison.png", dpi=150)
    plt.close()


def plot_decisive_surfacing(by_condition, output_dir):
    fig, ax = plt.subplots(figsize=(10, 5))
    conditions = list(by_condition.keys())
    rates = [np.mean([r["decisive_surfacing_rate"] for r in by_condition[c]]) for c in conditions]
    x = np.arange(len(conditions))
    bar_colors = [COLORS.get(c, "#888") for c in conditions]
    bars = ax.bar(x, rates, color=bar_colors, edgecolor="white", linewidth=1.5)
    ax.set_ylabel("Decisive Feature Surfacing Rate")
    ax.set_title("How Often Decisive Features Are Disclosed")
    ax.set_ylim(0, 1.15)
    ax.set_xticks(x)
    ax.set_xticklabels(conditions, rotation=45, ha="right", fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.03,
                f"{rate:.2f}", ha="center", fontsize=10, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_dir / "decisive_surfacing.png", dpi=150)
    plt.close()


def plot_decisive_holder_calibration(by_condition, output_dir, scenarios_path=None):
    decisive_held: dict[str, dict[str, set]] = {}
    all_held: dict[str, dict[str, set]] = {}
    if scenarios_path:
        try:
            with open(scenarios_path) as f:
                raw = json.load(f)
            for s in raw.get("scenarios", []):
                sid = s["id"]
                fv = s.get("full_view", {})
                decisive_feats = {k for k, v in fv.items() if v.get("tag") == "decisive"}
                agents_struct = s.get("agents_structured", {})
                decisive_held[sid] = {
                    aid: set(feats.keys()) & decisive_feats
                    for aid, feats in agents_struct.items()
                }
                all_held[sid] = {
                    aid: set(feats.keys())
                    for aid, feats in agents_struct.items()
                }
        except Exception:
            pass

    conditions = list(by_condition.keys())
    dh_rates, nh_rates = [], []

    for cond in conditions:
        results = by_condition[cond]
        dh_disc, dh_total, nh_disc, nh_total = 0, 0, 0, 0
        for r in results:
            sid = r.get("scenario_id", "")
            dm = decisive_held.get(sid)
            am = all_held.get(sid)

            if dm and am:
                for aid, feats_disclosed in r.get("agent_disclosures", {}).items():
                    disc_set = set(feats_disclosed)
                    for df in dm.get(aid, set()):
                        dh_total += 1
                        if df in disc_set:
                            dh_disc += 1
                    for nf in am.get(aid, set()) - dm.get(aid, set()):
                        nh_total += 1
                        if nf in disc_set:
                            nh_disc += 1
            else:
                decisive_holders = set(r.get("agents_holding_decisive", []))
                for aid, feats in r.get("agent_disclosures", {}).items():
                    if aid in decisive_holders:
                        dh_total += 1
                        if feats:
                            dh_disc += 1
                    else:
                        nh_total += 1
                        if feats:
                            nh_disc += 1

        dh_rates.append(dh_disc / dh_total if dh_total > 0 else 0.0)
        nh_rates.append(nh_disc / nh_total if nh_total > 0 else 0.0)

    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(conditions))
    w = 0.35
    bars1 = ax.bar(x - w/2, dh_rates, w,
                   color=[COLORS.get(c, "#888") for c in conditions], edgecolor="white")
    bars2 = ax.bar(x + w/2, nh_rates, w,
                   color=[COLORS.get(c, "#888") for c in conditions], alpha=0.4, edgecolor="white")

    metric_label = ("Decisive Feature Disclosure Rate" if decisive_held
                    else "Disclosure Rate — any feature (proxy; no scenario metadata)")
    ax.set_ylabel(metric_label)
    ax.set_title("Decisive-Feature Holder Disclosure Rate by Condition")
    ax.set_xticks(x)
    ax.set_xticklabels(conditions, rotation=45, ha="right", fontsize=9)
    ax.set_ylim(0, 1.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Two-tier legend: solid/faded pattern for DH%/NH%, color patches for conditions
    import matplotlib.patches as mpatches
    pattern_handles = [
        mpatches.Patch(facecolor="gray", edgecolor="white", label="Decisive-feature holders (DH%)"),
        mpatches.Patch(facecolor="gray", edgecolor="white", alpha=0.4, label="Non-decisive holders (NH%)"),
    ]
    cond_handles = [
        mpatches.Patch(facecolor=COLORS.get(c, "#888"), edgecolor="white", label=c)
        for c in conditions
    ]
    legend1 = ax.legend(handles=pattern_handles, loc="upper left", fontsize=8,
                        title="Disclosure type", title_fontsize=8, framealpha=0.85)
    ax.add_artist(legend1)
    ax.legend(handles=cond_handles, loc="upper right", fontsize=7,
              title="Condition", title_fontsize=8, framealpha=0.85, ncol=2)

    for bar, rate in zip(bars1, dh_rates):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f"{rate:.2f}", ha="center", fontsize=8, fontweight="bold")
    for bar, rate in zip(bars2, nh_rates):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f"{rate:.2f}", ha="center", fontsize=8)

    plt.tight_layout()
    plt.savefig(output_dir / "decisive_holder_calibration.png", dpi=150)
    plt.close()


def plot_surfacing_by_cost_per_condition(by_condition, scenarios_path, output_dir):
    try:
        with open(scenarios_path) as f:
            raw = json.load(f)
        scenario_features = {}
        for s in raw.get("scenarios", []):
            scenario_features[s["id"]] = {
                k: v.get("cost", 1) for k, v in s.get("full_view", {}).items()
            }
    except Exception:
        return

    fig, ax = plt.subplots(figsize=(9, 5))
    conditions = list(by_condition.keys())
    all_costs = set()

    for cond in conditions:
        cost_surfaced = defaultdict(list)
        for r in by_condition[cond]:
            sid = r["scenario_id"]
            feats = scenario_features.get(sid, {})
            all_disclosed = set()
            for agent_feats in r.get("agent_disclosures", {}).values():
                all_disclosed.update(agent_feats)
            for fname, cost in feats.items():
                cost_surfaced[cost].append(1.0 if fname in all_disclosed else 0.0)
                all_costs.add(cost)

        costs_sorted = sorted(cost_surfaced.keys())
        rates = [np.mean(cost_surfaced[c]) for c in costs_sorted]
        ax.plot(costs_sorted, rates, marker="o", label=cond,
                color=COLORS.get(cond, "#888"), linewidth=2)

    ax.set_xlabel("Feature Disclosure Cost")
    ax.set_ylabel("Surfacing Rate")
    ax.set_title("Feature Surfacing Rate by Cost (per Condition)")
    ax.set_xticks(sorted(all_costs))
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=8, loc="best", framealpha=0.85)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    plt.savefig(output_dir / "surfacing_by_cost.png", dpi=150)
    plt.close()


def plot_cost_frontiers(by_condition, output_dir):
    """Pareto frontier: accuracy vs. cost, with bootstrap 95% CI error bars."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    conditions = list(by_condition.keys())

    for ax, key, xlabel, title in [
        (axes[0], "total_communication_tokens", "Mean Communication Tokens",
         "Accuracy vs Communication Cost"),
        (axes[1], "total_disclosure_cost", "Mean Disclosure Cost",
         "Accuracy vs Disclosure Cost"),
    ]:
        handles = []
        for cond in conditions:
            results = by_condition[cond]
            x_vals = [r.get(key, r.get("total_tokens", 0)) for r in results]
            y_vals = [float(r["is_correct"]) for r in results]
            x_mean, x_lo, x_hi = _bootstrap_ci(x_vals)
            y_mean, y_lo, y_hi = _bootstrap_ci(y_vals)
            color = COLORS.get(cond, "#888")
            handle = ax.errorbar(
                x_mean, y_mean,
                xerr=[[x_mean - x_lo], [x_hi - x_mean]],
                yerr=[[y_mean - y_lo], [y_hi - y_mean]],
                fmt="o", markersize=10, color=color, label=cond,
                capsize=5, capthick=1.5, linewidth=1.5, zorder=5,
            )
            handles.append(handle)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Accuracy")
        ax.set_title(title)
        ax.legend(handles=handles, labels=conditions,
                  fontsize=8, loc="lower right", framealpha=0.85)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_dir / "cost_frontiers.png", dpi=150)
    plt.close()


def plot_misleading_influence(by_condition, output_dir):
    conditions = list(by_condition.keys())
    x = np.arange(len(conditions))
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for ax, key, title, ylabel in [
        (axes[0], "misleading_before_wrong", "Misleading + Wrong", "Rate"),
        (axes[1], "misleading_preceded_decisive", "Misleading Before Decisive", "Rate"),
    ]:
        rates = [np.mean([float(r.get(key, False)) for r in by_condition[c]]) for c in conditions]
        bar_colors = [COLORS.get(c, "#888") for c in conditions]
        bars = ax.bar(x, rates, color=bar_colors, edgecolor="white", linewidth=1.5)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(conditions, rotation=45, ha="right", fontsize=9)
        ax.set_ylim(0, max(rates)*1.3+0.05 if max(rates) > 0 else 0.2)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for bar, rate in zip(bars, rates):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.01,
                    f"{rate:.2f}", ha="center", fontsize=10, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_dir / "misleading_influence.png", dpi=150)
    plt.close()


def plot_free_riding(by_condition, output_dir):
    fig, ax = plt.subplots(figsize=(10, 5))
    conditions = list(by_condition.keys())
    x = np.arange(len(conditions))
    rates = []
    for cond in conditions:
        total = sum(len(r.get("agent_disclosures", {})) for r in by_condition[cond])
        free = sum(1 for r in by_condition[cond]
                   for f in r.get("agent_disclosures", {}).values() if len(f) == 0)
        rates.append(free / total if total > 0 else 0)
    bar_colors = [COLORS.get(c, "#888") for c in conditions]
    bars = ax.bar(x, rates, color=bar_colors, edgecolor="white", linewidth=1.5)
    ax.set_ylabel("Free-Riding Rate")
    ax.set_title("Agents Disclosing No Features")
    ax.set_xticks(x)
    ax.set_xticklabels(conditions, rotation=45, ha="right", fontsize=9)
    ax.set_ylim(0, max(rates)*1.3+0.05 if max(rates) > 0 else 0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.01,
                f"{rate:.2f}", ha="center", fontsize=10, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_dir / "free_riding.png", dpi=150)
    plt.close()


def plot_moderator_trajectory(by_condition, output_dir):
    fig, ax = plt.subplots(figsize=(9, 5))
    for cond, results in by_condition.items():
        round_confs = defaultdict(list)
        for r in results:
            for entry in r.get("moderator_trajectory", []):
                rn = entry.get("round")
                if isinstance(rn, int):
                    conf = entry.get("confidence", 0.5)
                    correct_yes = r["ground_truth"].upper() == "YES"
                    mod_yes = entry.get("decision", "").upper() == "YES"
                    round_confs[rn].append(conf if correct_yes == mod_yes else -conf)
        if not round_confs:
            continue
        rounds_sorted = sorted(round_confs.keys())
        means = [np.mean(round_confs[rn]) for rn in rounds_sorted]
        ax.plot(rounds_sorted, means, marker="o", label=cond,
                color=COLORS.get(cond, "#888"), linewidth=2)
    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    ax.set_xlabel("Round"); ax.set_ylabel("Signed Confidence (+ = correct)")
    ax.set_title("Moderator Confidence Trajectory")
    ax.legend(fontsize=8, loc="best", framealpha=0.85)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    plt.tight_layout()
    plt.savefig(output_dir / "moderator_trajectory.png", dpi=150)
    plt.close()


def plot_early_disclosure(by_condition, output_dir):
    fig, ax = plt.subplots(figsize=(9, 5))
    conditions = list(by_condition.keys())
    condition_first_rounds: dict[str, list[int]] = {}

    for cond in conditions:
        first_rounds = []
        for r in by_condition[cond]:
            decisive_holders = set(r.get("agents_holding_decisive", []))
            if not decisive_holders:
                continue
            earliest = None
            for rnd in r.get("rounds", []):
                rn = rnd.get("round_num") if isinstance(rnd, dict) else getattr(rnd, "round_num", None)
                turns = rnd.get("agent_turns", []) if isinstance(rnd, dict) else getattr(rnd, "agent_turns", [])
                for t in turns:
                    aid = t.get("agent_id") if isinstance(t, dict) else t.get("agent_id")
                    fd  = t.get("features_disclosed", {}) if isinstance(t, dict) else {}
                    if aid in decisive_holders and fd:
                        if earliest is None or rn < earliest:
                            earliest = rn
            if earliest is not None:
                first_rounds.append(earliest)
        condition_first_rounds[cond] = first_rounds

    data = [condition_first_rounds.get(c, [0]) for c in conditions]
    bp = ax.boxplot(data, patch_artist=True, notch=False)
    for patch, cond in zip(bp["boxes"], conditions):
        patch.set_facecolor(COLORS.get(cond, "#888"))
        patch.set_alpha(0.7)

    ax.set_xticks(range(1, len(conditions) + 1))
    ax.set_xticklabels(conditions, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("First Round a Decisive-Feature Holder Disclosed")
    ax.set_title("First-Mover Analysis: When Do Decisive-Feature Holders Disclose?\n"
                 "(Lower = earlier; contribution incentive should pull disclosure earlier)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    plt.savefig(output_dir / "early_disclosure.png", dpi=150)
    plt.close()


def plot_speaking_order_effects(by_condition, scenarios_path, output_dir):
    decisive_by_scenario: dict[str, set] = {}
    try:
        with open(scenarios_path) as f:
            raw = json.load(f)
        for s in raw.get("scenarios", []):
            fv = s.get("full_view", {})
            decisive_by_scenario[s["id"]] = {
                k for k, v in fv.items() if v.get("tag") == "decisive"
            }
    except Exception:
        pass

    fig, ax = plt.subplots(figsize=(10, 5))
    max_pos = 0

    for cond, results in by_condition.items():
        pos_decisive: dict[int, list[float]] = defaultdict(list)
        for r in results:
            dec_set = decisive_by_scenario.get(r.get("scenario_id", ""), set())
            for rnd in r.get("rounds", []):
                turns = rnd.get("agent_turns", []) if isinstance(rnd, dict) else []
                for t in turns:
                    pos = t.get("speaking_position") if isinstance(t, dict) else None
                    if pos is None:
                        continue
                    fd = t.get("features_disclosed", {}) if isinstance(t, dict) else {}
                    has_decisive = bool(set(fd.keys()) & dec_set) if dec_set else bool(fd)
                    pos_decisive[pos].append(float(has_decisive))
                    max_pos = max(max_pos, pos)

        if not pos_decisive:
            continue
        positions = sorted(pos_decisive.keys())
        rates = [np.mean(pos_decisive[p]) for p in positions]
        ax.plot(positions, rates, marker="o", label=cond,
                color=COLORS.get(cond, "#888"), linewidth=2)

    ax.set_xlabel("Speaking Position Within Round (1 = first speaker)")
    ax.set_ylabel("Decisive Feature Disclosure Rate")
    ax.set_title("Does Speaking Order Affect Decisive Disclosure?\n"
                 "(contribution incentive predicted to show stronger first-mover effect)")
    if max_pos > 0:
        ax.set_xticks(range(1, max_pos + 1))
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=8, loc="best", framealpha=0.85)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    plt.savefig(output_dir / "speaking_order_effects.png", dpi=150)
    plt.close()


def plot_stratified_analysis(by_condition, scenarios_path, output_dir):
    scenario_tier: dict[str, str] = {}
    try:
        with open(scenarios_path) as f:
            raw = json.load(f)
        for s in raw.get("scenarios", []):
            sid = s["id"]
            fv = s.get("full_view", {})
            decisive_costs = [
                v.get("cost", 1) for v in fv.values() if v.get("tag") == "decisive"
            ]
            if not decisive_costs:
                scenario_tier[sid] = "none"
            else:
                mean_cost = sum(decisive_costs) / len(decisive_costs)
                scenario_tier[sid] = (
                    "low" if mean_cost <= 1.5 else
                    "medium" if mean_cost <= 3.0 else
                    "high"
                )
    except Exception:
        return

    tiers = ["low", "medium", "high"]
    conditions = list(by_condition.keys())
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for ax, metric_key, title, ylabel in [
        (axes[0], "is_correct",
         "Accuracy by Decisive Cost Tier", "Accuracy"),
        (axes[1], "decisive_surfacing_rate",
         "Decisive Surfacing Rate by Decisive Cost Tier", "Decisive Surfacing Rate"),
    ]:
        x = np.arange(len(tiers))
        n_conds = len(conditions)
        width = 0.8 / max(n_conds, 1)
        offsets = (
            np.linspace(-(0.8 - width) / 2, (0.8 - width) / 2, n_conds)
            if n_conds > 1 else [0.0]
        )
        for i, cond in enumerate(conditions):
            vals_by_tier: dict[str, list[float]] = {t: [] for t in tiers}
            for r in by_condition[cond]:
                tier = scenario_tier.get(r.get("scenario_id", ""))
                if tier in vals_by_tier:
                    vals_by_tier[tier].append(float(r.get(metric_key, 0.0)))
            means = [np.mean(vals_by_tier[t]) if vals_by_tier[t] else 0.0 for t in tiers]
            sems  = [
                np.std(vals_by_tier[t]) / max(np.sqrt(len(vals_by_tier[t])), 1)
                for t in tiers
            ]
            ax.bar(x + offsets[i], means, width, label=cond,
                   color=COLORS.get(cond, "#888"), alpha=0.85, edgecolor="white")
            ax.errorbar(x + offsets[i], means, yerr=sems,
                        fmt="none", color="black", capsize=3, linewidth=1)

        ax.set_xlabel("Decisive Feature Cost Tier")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(tiers)
        ax.set_ylim(0, 1.1)
        ax.legend(fontsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_dir / "stratified_analysis.png", dpi=150)
    plt.close()


def plot_variant_comparison(results_dir, output_dir):
    """Compare base vs variant-A (information structure) vs variant-B (cost) across conditions.

    Groups results by variant_type and plots per-variant accuracy and decisive surfacing
    rate side by side for each incentive condition, using within-triplet matched comparisons.
    Skips silently if no variant_type data is found in any result.
    """
    by_condition = load_results(results_dir) if isinstance(results_dir, Path) else results_dir

    has_variant_data = any(
        r.get("variant_type") for results in by_condition.values() for r in results
    )
    if not has_variant_data:
        return

    variant_types = ["base", "A_information_structure", "B_cost"]
    conditions = list(by_condition.keys())

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    x = np.arange(len(conditions))
    n_vtypes = len(variant_types)
    width = 0.8 / max(n_vtypes, 1)
    offsets = (
        np.linspace(-(0.8 - width) / 2, (0.8 - width) / 2, n_vtypes)
        if n_vtypes > 1 else [0.0]
    )
    vtype_colors = {"base": "#4C72B0", "A_information_structure": "#55A868", "B_cost": "#C44E52"}
    vtype_labels = {"base": "Base", "A_information_structure": "Variant A (info)", "B_cost": "Variant B (cost)"}

    for ax, metric_key, ylabel, title in [
        (axes[0], "is_correct", "Accuracy", "Accuracy by Variant Type and Condition"),
        (axes[1], "decisive_surfacing_rate", "Decisive Surfacing Rate",
         "Decisive Surfacing Rate by Variant Type and Condition"),
    ]:
        for vi, vtype in enumerate(variant_types):
            means = []
            sems = []
            for cond in conditions:
                vals = [
                    float(r.get(metric_key, 0.0))
                    for r in by_condition[cond]
                    if r.get("variant_type", "base") == vtype
                ]
                means.append(np.mean(vals) if vals else 0.0)
                sems.append(
                    np.std(vals) / max(np.sqrt(len(vals)), 1) if vals else 0.0
                )
            ax.bar(
                x + offsets[vi], means, width,
                label=vtype_labels[vtype],
                color=vtype_colors[vtype], alpha=0.85, edgecolor="white"
            )
            ax.errorbar(x + offsets[vi], means, yerr=sems,
                        fmt="none", color="black", capsize=3, linewidth=1)

        ax.set_xlabel("Incentive Condition")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(conditions, rotation=15, ha="right")
        ax.set_ylim(0, 1.1)
        ax.legend(fontsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_dir / "variant_comparison.png", dpi=150)
    plt.close()


def compute_significance(by_condition):
    def _scenario_agg(results, key_fn):
        groups: dict[str, list] = defaultdict(list)
        for r in results:
            groups[r["scenario_id"]].append(key_fn(r))
        return {sid: float(np.mean(vals)) for sid, vals in groups.items()}

    def _wilcoxon_paired(a_map, b_map, common):
        diffs = [a_map[s] - b_map[s] for s in common]
        if all(d == 0 for d in diffs):
            return {"test": "Wilcoxon_paired", "p": 1.0, "sig": False,
                    "n_pairs": len(common)}
        try:
            _, p = stats.wilcoxon(diffs, alternative="two-sided")
            return {"test": "Wilcoxon_paired", "p": float(p), "sig": p < 0.05,
                    "n_pairs": len(common)}
        except ValueError:
            return {"test": "Wilcoxon_paired", "p": 1.0, "sig": False,
                    "n_pairs": len(common)}

    conditions = list(by_condition.keys())
    pairwise = {}
    for i, ca in enumerate(conditions):
        for cb in conditions[i + 1:]:
            ra, rb = by_condition[ca], by_condition[cb]
            key = f"{ca}_vs_{cb}"

            acc_a = _scenario_agg(ra, lambda r: float(r["is_correct"]))
            acc_b = _scenario_agg(rb, lambda r: float(r["is_correct"]))
            dsr_a = _scenario_agg(ra, lambda r: r.get("decisive_surfacing_rate", 0.0))
            dsr_b = _scenario_agg(rb, lambda r: r.get("decisive_surfacing_rate", 0.0))

            def _fr(r):
                d = r.get("agent_disclosures", {})
                return sum(1 for f in d.values() if len(f) == 0) / len(d) if d else 0.0

            fr_a = _scenario_agg(ra, _fr)
            fr_b = _scenario_agg(rb, _fr)

            common = sorted(set(acc_a) & set(acc_b))
            if len(common) < 5:
                pairwise[key] = {"note": f"Only {len(common)} matched scenarios; skipping tests"}
                continue

            pairwise[key] = {
                "accuracy":    _wilcoxon_paired(acc_a, acc_b, common),
                "decisive":    _wilcoxon_paired(dsr_a, dsr_b, common),
                "free_riding": _wilcoxon_paired(fr_a,  fr_b,  common),
            }
    return pairwise


def print_summary(by_condition):
    header = f"{'Condition':<14} {'Acc':>5} {'Decis%':>7} {'FR%':>5} {'CommTk':>7} {'Cost':>5} {'$':>7}"
    print("\n" + header); print("-" * len(header))
    for cond, results in by_condition.items():
        acc = np.mean([r["is_correct"] for r in results])
        dec = np.mean([r["decisive_surfacing_rate"] for r in results])
        ct = np.mean([r.get("total_communication_tokens", r["total_tokens"]) for r in results])
        cost = np.mean([r["total_disclosure_cost"] for r in results])
        usd = sum(r.get("api_usage", {}).get("estimated_cost_usd", 0) for r in results)
        total_a = sum(len(r["agent_disclosures"]) for r in results)
        free = sum(1 for r in results for f in r["agent_disclosures"].values() if len(f)==0)
        fr = free / total_a if total_a else 0
        print(f"{cond:<14} {acc:>5.2f} {dec:>7.2f} {fr:>5.2f} {ct:>7.0f} {cost:>5.1f} ${usd:>6.4f}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze.py <results_directory> [scenarios.json]")
        sys.exit(1)

    results_dir = Path(sys.argv[1])
    scenarios_path = sys.argv[2] if len(sys.argv) > 2 else "data/scenarios.json"

    by_condition = load_results(results_dir)
    if not by_condition:
        print("No results_*.json found"); sys.exit(1)

    print(f"Conditions: {list(by_condition.keys())}")
    print(f"Counts: { {c: len(r) for c, r in by_condition.items()} }")

    first_results = next(iter(by_condition.values())) if by_condition else []
    if first_results:
        seen: dict[str, str] = {}
        for r in first_results:
            sid = r["scenario_id"]
            if sid not in seen:
                seen[sid] = r.get("ground_truth", "?")
        yes_n = sum(1 for v in seen.values() if v.upper() == "YES")
        no_n  = sum(1 for v in seen.values() if v.upper() == "NO")
        print(f"Scenario balance: {len(seen)} unique — YES={yes_n}, NO={no_n} "
              f"({yes_n/max(len(seen),1):.0%} YES)")

    print_summary(by_condition)

    if len(by_condition) >= 2:
        pw = compute_significance(by_condition)
        print("\nPairwise significance (Wilcoxon signed-rank, scenario-level paired):")
        for pair, tests in sorted(pw.items()):
            if "note" in tests:
                print(f"  {pair}: {tests['note']}")
                continue
            parts = [f"{pair}:"]
            for metric, res in tests.items():
                sig = "*" if res.get("sig") else ""
                parts.append(f"  {metric} p={res['p']:.4f}{sig} (n={res.get('n_pairs','?')})")
            print("  ".join(parts))
        with open(results_dir / "significance.json", "w") as f:
            json.dump(pw, f, indent=2, cls=_NumpyEncoder)

    plot_accuracy_comparison(by_condition, results_dir)
    plot_decisive_surfacing(by_condition, results_dir)
    plot_decisive_holder_calibration(by_condition, results_dir, scenarios_path)
    plot_surfacing_by_cost_per_condition(by_condition, scenarios_path, results_dir)
    plot_cost_frontiers(by_condition, results_dir)
    plot_free_riding(by_condition, results_dir)
    plot_moderator_trajectory(by_condition, results_dir)
    plot_misleading_influence(by_condition, results_dir)
    plot_early_disclosure(by_condition, results_dir)
    plot_speaking_order_effects(by_condition, scenarios_path, results_dir)
    plot_stratified_analysis(by_condition, scenarios_path, results_dir)
    plot_variant_comparison(by_condition, results_dir)

    print(f"\nPlots saved to {results_dir}/")

class _NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        return super().default(obj)


if __name__ == "__main__":
    main()
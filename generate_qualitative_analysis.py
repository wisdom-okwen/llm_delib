#!/usr/bin/env python3
"""
generate_qualitative_analysis.py

Usage:
    python generate_qualitative_analysis.py <model_dir> [--output <output_file>] [--max-scenarios <n>]

Example:
    python generate_qualitative_analysis.py qwen3-14b/
    python generate_qualitative_analysis.py qwen3-8b/ --output analysis_8b.md --max-scenarios 30
"""

import argparse
import json
import sys
import time
from pathlib import Path

from openai import OpenAI

MODEL = "gpt-4o-mini"
MAX_TOKENS = 4000
RATE_LIMIT_SLEEP = 0.3

# Pricing (USD per token)
PRICE_INPUT_PER_TOK  = 0.15 / 1_000_000   # $0.15 / 1M input tokens
PRICE_OUTPUT_PER_TOK = 0.60 / 1_000_000   # $0.60 / 1M output tokens

PREFERRED_ORDER = [
    "free_debate", "contribution", "forced_sharing", "contribution_oracle",
    "counterfactual_contribution", "no_comm", "hybrid", "bid_to_speak",
    "uniform", "stake",
]

SYSTEM_PROMPT = """\
You are a research assistant conducting deep qualitative analysis of multi-agent LLM deliberation experiments.

You will receive data from a hidden-profile deliberation experiment where agents hold private features
and decide whether to disclose them. Each scenario has a ground truth answer (YES/NO) and agents
try to reach the correct group decision.

Key concepts:
- **Free-riding**: An agent withholds private information because the shared reward doesn't cover disclosure cost
- **Decisive feature**: A feature that, if disclosed, changes the correct answer
- **Misleading feature**: A feature that pushes toward the wrong answer
- **spoke_without_new_disclosure**: Agent spoke but disclosed nothing new (pure free-riding turn)
- **disclosure_cost**: The cost an agent pays to share a feature
- **agents_holding_decisive**: Agents who held decisive features
- **decisive_surfacing_rate**: Whether decisive features were disclosed (1.0 = yes, 0.0 = no)

Your task: write a deep qualitative analysis section for ONE mechanism, identifying:
1. Key behavioral patterns (with specific scenario/agent/round citations)
2. Failure modes (when and why the group gets it wrong)
3. Success patterns (what leads to correct decisions)
4. Agent-level patterns (which agents free-ride, which contribute)
5. Round-level dynamics (how deliberation evolves across rounds)
6. Domain-specific behavior (does performance vary by domain?)

Write in the style of a research paper appendix: precise, evidence-based, with specific examples.
Use exact quotes from agent messages when illustrating patterns.
Format with markdown headers and subheaders.
Include frequency counts where possible (e.g., "X of Y scenarios showed this pattern").
"""


def load_scenarios(filepath: Path) -> list:
    scenarios = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    scenarios.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"  Warning: skipping malformed line: {e}", file=sys.stderr)
    return scenarios


def summarize_scenario(s: dict, include_transcript: bool = False) -> str:
    sid = s.get("scenario_id", "?")
    domain = s.get("domain", "?")
    question = s.get("question", "?")
    gt = s.get("ground_truth", "?")
    incentive = s.get("incentive", "?")
    correct = s.get("is_correct", None)
    decisive_surfaced = s.get("decisive_features_surfaced", [])
    decisive_holders = s.get("agents_holding_decisive", [])
    surf_rate = s.get("decisive_surfacing_rate", 0.0)
    total_disclosure_cost = s.get("total_disclosure_cost", 0.0)
    final_decision = s.get("final_decision", {})
    moderator_traj = s.get("moderator_trajectory", [])

    agent_disclosures = s.get("agent_disclosures", {})
    disclosers = {a: v for a, v in agent_disclosures.items() if v}
    free_riders = [a for a, v in agent_disclosures.items() if not v]

    conf_traj = []
    for t in moderator_traj:
        conf_traj.append(f"R{t.get('round','?')}/{t.get('event','?')}:{t.get('confidence','?')}")
    conf_str = " → ".join(conf_traj)

    lines = [
        f"### Scenario {sid} | domain={domain} | GT={gt} | correct={correct}",
        f"Question: {question}",
        f"Incentive: {incentive}",
        f"Decisive holders: {decisive_holders} | Decisive surfaced: {decisive_surfaced} | Surf rate: {surf_rate}",
        f"Total disclosure cost paid: {total_disclosure_cost}",
        f"Moderator trajectory: {conf_str}",
        f"Final decision: {final_decision.get('decision','?')} (confidence={final_decision.get('confidence','?')})",
        f"Disclosers: {dict(list(disclosers.items())[:5])}{'...' if len(disclosers) > 5 else ''}",
        f"Free-riders (no disclosure): {free_riders}",
    ]

    misleading = s.get("misleading_features_surfaced", [])
    if misleading:
        lines.append(f"Misleading features surfaced: {misleading}")
    if s.get("misleading_before_wrong"):
        lines.append("** Misleading feature appeared before wrong group decision **")

    if include_transcript:
        lines.append("\n**DELIBERATION TRANSCRIPT (abbreviated):**")
        for rnd in s.get("rounds", []):
            rnum = rnd.get("round_num", "?")
            mod_open = rnd.get("moderator_open", {})
            lines.append(f"\n[Round {rnum} open] Moderator: {mod_open.get('decision','?')} conf={mod_open.get('confidence','?')}")
            for turn in rnd.get("agent_turns", []):
                agent = turn.get("agent_id", "?")
                msg = turn.get("message", "")
                disclosed = turn.get("features_disclosed", {})
                cost = turn.get("disclosure_cost", 0.0)
                no_new = turn.get("spoke_without_new_disclosure", True)
                msg_short = msg[:200].replace("\n", " ") + ("..." if len(msg) > 200 else "")
                status = "FREE-RIDE" if no_new else f"DISCLOSED({disclosed}) cost={cost}"
                lines.append(f"  [{agent} R{rnum}] [{status}] {msg_short}")
            mod_close = rnd.get("moderator_stance_after", {})
            lines.append(f"[Round {rnum} close] Moderator: {mod_close.get('decision','?')} conf={mod_close.get('confidence','?')}")

    return "\n".join(lines)


def select_scenarios(scenarios: list, max_scenarios: int = 30) -> list:
    incorrect = [s for s in scenarios if not s.get("is_correct", True)]
    decisive_surfaced = [s for s in scenarios if s.get("decisive_surfacing_rate", 0) > 0]
    high_cost = sorted(scenarios, key=lambda s: s.get("total_disclosure_cost", 0), reverse=True)
    misleading = [s for s in scenarios if s.get("misleading_before_wrong", False)]

    selected = set()
    result = []

    def add(s_list, n):
        for s in s_list[:n]:
            sid = s.get("scenario_id")
            if sid not in selected:
                selected.add(sid)
                result.append(s)

    add(incorrect, min(8, max_scenarios // 4))
    add(misleading, min(4, max_scenarios // 6))
    add(decisive_surfaced, min(6, max_scenarios // 4))
    add(high_cost, min(6, max_scenarios // 4))
    add(scenarios, max_scenarios)

    return result[:max_scenarios]


def compute_mechanism_stats(scenarios: list) -> dict:
    n = len(scenarios)
    if n == 0:
        return {}

    correct = sum(1 for s in scenarios if s.get("is_correct", False))
    surf_rates = [s.get("decisive_surfacing_rate", 0) for s in scenarios]
    total_costs = [s.get("total_disclosure_cost", 0) for s in scenarios]

    total_turns = 0
    free_ride_turns = 0
    for s in scenarios:
        for rnd in s.get("rounds", []):
            for turn in rnd.get("agent_turns", []):
                total_turns += 1
                if turn.get("spoke_without_new_disclosure", True):
                    free_ride_turns += 1

    agent_free_ride = {}
    agent_total = {}
    for s in scenarios:
        for rnd in s.get("rounds", []):
            for turn in rnd.get("agent_turns", []):
                a = turn.get("agent_id", "?")
                agent_total[a] = agent_total.get(a, 0) + 1
                if turn.get("spoke_without_new_disclosure", True):
                    agent_free_ride[a] = agent_free_ride.get(a, 0) + 1

    agent_rates = {
        a: agent_free_ride.get(a, 0) / agent_total[a]
        for a in agent_total
    }

    domain_correct = {}
    domain_total = {}
    for s in scenarios:
        d = s.get("domain", "unknown")
        domain_total[d] = domain_total.get(d, 0) + 1
        if s.get("is_correct", False):
            domain_correct[d] = domain_correct.get(d, 0) + 1

    decisive_withheld = sum(
        1 for s in scenarios
        if s.get("agents_holding_decisive") and s.get("decisive_surfacing_rate", 0) == 0
    )

    return {
        "n_scenarios": n,
        "accuracy": correct / n,
        "n_correct": correct,
        "mean_decisive_surfacing": sum(surf_rates) / n,
        "mean_disclosure_cost": sum(total_costs) / n,
        "free_riding_rate": free_ride_turns / total_turns if total_turns else 0,
        "total_turns": total_turns,
        "free_ride_turns": free_ride_turns,
        "agent_free_ride_rates": dict(sorted(agent_rates.items(), key=lambda x: x[1], reverse=True)),
        "domain_accuracy": {
            d: domain_correct.get(d, 0) / domain_total[d]
            for d in domain_total
        },
        "decisive_withheld_count": decisive_withheld,
        "decisive_withheld_rate": decisive_withheld / n,
    }


def stats_to_text(stats: dict, mechanism: str) -> str:
    lines = [
        f"## Aggregate Statistics for mechanism: {mechanism}",
        f"- Total scenarios: {stats['n_scenarios']}",
        f"- Accuracy: {stats['accuracy']:.1%} ({stats['n_correct']}/{stats['n_scenarios']} correct)",
        f"- Mean decisive surfacing rate: {stats['mean_decisive_surfacing']:.2f}",
        f"- Mean disclosure cost paid per scenario: {stats['mean_disclosure_cost']:.2f}",
        f"- Overall free-riding rate: {stats['free_riding_rate']:.1%} ({stats['free_ride_turns']}/{stats['total_turns']} turns with no new disclosure)",
        f"- Scenarios where decisive holders never disclosed: {stats['decisive_withheld_count']} ({stats['decisive_withheld_rate']:.1%})",
        "",
        "**Agent-level free-riding rates:**",
    ]
    for agent, rate in stats["agent_free_ride_rates"].items():
        lines.append(f"  {agent}: {rate:.1%}")
    lines.append("")
    lines.append("**Domain accuracy:**")
    for domain, acc in stats["domain_accuracy"].items():
        lines.append(f"  {domain}: {acc:.1%}")
    return "\n".join(lines)


# ── Cost tracking ─────────────────────────────────────────────────────────────

_cost_log: list[dict] = []   # accumulates per-call usage

def cost_calc(label: str = "") -> str:
    """
    Return a concise cost summary string and optionally print it.
    Reads from the global _cost_log populated by analyze_mechanism().
    """
    if not _cost_log:
        return "No API calls recorded yet."
    total_in  = sum(r["input_tokens"]  for r in _cost_log)
    total_out = sum(r["output_tokens"] for r in _cost_log)
    total_usd = sum(r["cost_usd"]      for r in _cost_log)
    n_calls   = len(_cost_log)
    summary = (
        f"[cost] {label+' ' if label else ''}"
        f"{n_calls} calls | "
        f"in={total_in:,} out={total_out:,} tokens | "
        f"${total_usd:.4f}"
    )
    return summary


def analyze_mechanism(client, mechanism: str, scenarios: list, max_scenarios: int = 30) -> str:
    stats = compute_mechanism_stats(scenarios)
    stats_text = stats_to_text(stats, mechanism)

    selected = select_scenarios(scenarios, max_scenarios)
    print(f"  Selected {len(selected)} of {len(scenarios)} scenarios for analysis")

    scenario_texts = []
    for i, s in enumerate(selected):
        include_transcript = i < 10
        scenario_texts.append(summarize_scenario(s, include_transcript=include_transcript))

    scenarios_block = "\n\n---\n\n".join(scenario_texts)

    user_content = f"""{stats_text}

---

## Sampled Scenarios ({len(selected)} of {len(scenarios)} total)

{scenarios_block}

---

## Your Task

Write a comprehensive qualitative analysis section for the **{mechanism.upper()}** mechanism.

Structure your analysis with the following sections:
1. **Overview** — what the mechanism does and headline behavioral summary
2. **Key Findings** — 4-6 numbered subsections, each covering a distinct behavioral pattern
   - Each subsection must cite specific scenarios, round numbers, and agent IDs
   - Include verbatim quotes from agent messages where illustrative
   - Include frequency counts (e.g., "N of M scenarios showed...")
3. **Failure Modes** — specific conditions under which the mechanism fails
4. **Success Patterns** — what conditions lead to correct decisions
5. **Agent Heterogeneity** — which agents behave differently, and how
6. **Domain Performance** — if the data shows domain variation, explain why

Be specific and evidence-based. Avoid generic statements. Every claim should be grounded in the scenario data provided.
"""

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_content},
        ],
    )
    # Record usage for cost tracking
    usage = response.usage
    in_tok  = usage.prompt_tokens
    out_tok = usage.completion_tokens
    usd     = in_tok * PRICE_INPUT_PER_TOK + out_tok * PRICE_OUTPUT_PER_TOK
    _cost_log.append({"mechanism": mechanism, "input_tokens": in_tok,
                       "output_tokens": out_tok, "cost_usd": usd})
    return response.choices[0].message.content


def main():
    parser = argparse.ArgumentParser(description="Generate qualitative analysis for LLM deliberation experiments")
    parser.add_argument("model_dir", help="Path to model directory containing results_*.json files")
    parser.add_argument("--output", help="Output markdown file")
    parser.add_argument("--max-scenarios", type=int, default=30,
                        help="Max scenarios to sample per mechanism (default: 30)")
    parser.add_argument("--mechanisms", nargs="+",
                        help="Specific mechanisms to analyze (default: all found)")
    args = parser.parse_args()

    model_dir = Path(args.model_dir)
    if not model_dir.exists():
        print(f"Error: directory not found: {model_dir}", file=sys.stderr)
        sys.exit(1)

    result_files = sorted(model_dir.glob("results_*.json"))
    if not result_files:
        print(f"Error: no results_*.json files found in {model_dir}", file=sys.stderr)
        sys.exit(1)

    mechanisms_found = {f.stem.replace("results_", ""): f for f in result_files}
    if args.mechanisms:
        mechanisms_found = {k: v for k, v in mechanisms_found.items() if k in args.mechanisms}

    def sort_key(name):
        try:
            return PREFERRED_ORDER.index(name)
        except ValueError:
            return len(PREFERRED_ORDER)

    mechanisms_ordered = sorted(mechanisms_found.keys(), key=sort_key)

    print(f"Model directory: {model_dir}")
    print(f"Mechanisms found: {mechanisms_ordered}")
    print(f"Max scenarios per mechanism: {args.max_scenarios}")
    print()

    if args.output:
        output_path = Path(args.output)
    else:
        model_name = model_dir.name.rstrip("/")
        output_path = Path(f"QUALITATIVE_ANALYSIS_{model_name}.md")

    client = OpenAI()

    model_name = model_dir.name.rstrip("/") or model_dir.parent.name
    doc_lines = [
        f"# QUALITATIVE ANALYSIS: Multi-Agent Deliberation Mechanisms",
        f"",
        f"**Model:** {model_name}  ",
        f"**Mechanisms analyzed:** {', '.join(mechanisms_ordered)}  ",
        f"**Scenarios sampled per mechanism:** up to {args.max_scenarios}  ",
        f"",
        "---",
        "",
    ]

    for i, mechanism in enumerate(mechanisms_ordered, 1):
        filepath = mechanisms_found[mechanism]
        print(f"[{i}/{len(mechanisms_ordered)}] Analyzing mechanism: {mechanism} ...")
        print(f"  Loading {filepath} ...")

        scenarios = load_scenarios(filepath)
        print(f"  Loaded {len(scenarios)} scenarios")

        if not scenarios:
            print(f"  Warning: no scenarios loaded, skipping")
            continue

        t0 = time.time()
        try:
            analysis = analyze_mechanism(
                client=client,
                mechanism=mechanism,
                scenarios=scenarios,
                max_scenarios=args.max_scenarios,
            )
            elapsed = time.time() - t0
            print(f"  Analysis complete ({len(analysis)} chars, {elapsed:.1f}s)")
            print(f"  {cost_calc(mechanism)}")
        except Exception as e:
            print(f"  Error analyzing {mechanism}: {e}", file=sys.stderr)
            analysis = f"*Error generating analysis for {mechanism}: {e}*"

        doc_lines.append(f"## {i}. {mechanism.upper()} MECHANISM")
        doc_lines.append("")
        doc_lines.append(analysis)
        doc_lines.append("")
        doc_lines.append("---")
        doc_lines.append("")

        output_path.write_text("\n".join(doc_lines), encoding="utf-8")
        print(f"  Saved incrementally to {output_path}")

        if i < len(mechanisms_ordered):
            time.sleep(RATE_LIMIT_SLEEP)

    output_path.write_text("\n".join(doc_lines), encoding="utf-8")
    print(f"\nDone! Full analysis written to: {output_path}")
    print(cost_calc("TOTAL"))


if __name__ == "__main__":
    main()
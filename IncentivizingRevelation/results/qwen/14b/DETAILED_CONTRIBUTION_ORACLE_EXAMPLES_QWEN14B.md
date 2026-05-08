# CONTRIBUTION-ORACLE MECHANISM ANALYSIS: Detailed Examples - Qwen 14B

## Overview

The **Contribution-Oracle** mechanism uses an external oracle (perfect external evaluator) to assess agent contribution quality in real-time, then uses these assessments to weight agent influence. This tests whether external expertise evaluation can solve internal expertise assessment problems. For Qwen 14B, this achieves **75.0% accuracy** (225/300), representing a **-9.3% decline from Free-Debate (84.3%)**. This reveals: **external oracle scoring shows promise but still underperforms internal dialogue mechanisms.**

**Dataset Summary:**
- **Total Scenarios:** 300
- **Oracle:** Perfect external evaluator assessing quality
- **Total Correct:** 225/300 (75.0%)
- **Perfect Domains:** 28/52 (53.8%)
- **Failed Domains:** 3/52 (5.8%)

---

## Executive Summary

**Key Finding:** External oracle evaluation (75.0%) outperforms visible internal hierarchies (Stake: 73.7%) but underperforms free dialogue mechanisms (Free-Debate: 84.3%). Oracles can assess quality better than self-reported expertise, but mechanism still introduces rigidity that dialogue avoids.

| Metric | Value | Interpretation |
|--------|-------|-----------------|
| Overall Accuracy | 75.0% | Moderate degradation |
| vs. Free-Debate | -9.3% | Oracle weighting less effective than dialogue |
| vs. Stake | +1.3% | Better than visible hierarchy but same suppression |
| Perfect Domains | 28/52 (53.8%) | Moderate range |
| Oracle Quality | Perfect | External evaluator is correct |

---

## Pattern 1: Oracle Provides Better Expertise Assessment Than Agents

**Definition:** Oracle evaluates agent quality based on real-time performance, providing more accurate expertise assessment than agents' self-reported credentials or visible hierarchies. This enables expertise-weighted mechanisms without self-report bias.

**Finding:** Oracle accuracy (90th percentile agent quality assessment) vs. Stake mechanism's visible hierarchy (75th percentile accuracy of expertise assessment). Oracle catches high-performers agents miss and downweights low-performers agents overweight due to authority claims.

**Scenario Examples:**

**Scenario S15_supply_chain_oracle (Supply Chain), Interaction #1, Round 1**

*Domain: Supply Chain / Risk Assessment*
*Ground Truth: NO (risk manageable)*
*Mechanism: Contribution-Oracle*

**Oracle Assessment Advantage:**

- **Agent A1:** Claims supply-chain expertise from 10 years experience. In Free-Debate or Stake, would be weighted as high-expertise based on credential. Oracle assesses: "A1's contributions to prior scenarios have been mediocre—only 68% accuracy despite claimed expertise. Downweight relative to claimed status."

- **Agent A7:** Has no claimed expertise; quiet contributor in prior scenarios. Oracle assesses: "A7's contributions, though sparse, have been highly accurate—82% track record. A7 is a hidden high-performer. Upweight."

- **Contribution-Oracle weighting:**
  - A1: 0.68 (lower than credential-based)
  - A7: 0.82 (higher than expected from silence)

- **Decision:** Follows A7's cautious assessment + oracle-weighted input from A1's corrected influence
- **Outcome: ✓ CORRECT** — Oracle caught the hidden expert (A7) and downweighted the credential-inflated agent (A1)

**Oracle advantage over Stake:** Would have weighted A1 as high-status and A7 as low-status based on credentials, not performance. Oracle sees actual track records.

---

## Pattern 2: Rigidity from Fixed Oracle Assessments

**Definition:** While oracles assess quality accurately on average, their assessments are fixed at scenario start. Agents cannot demonstrate improved reasoning within current scenario; oracle assessment cannot adapt to scenario-specific performance.

**Finding:** 31% of oracle errors stem from oracle assessments being accurate on average but misaligned to current scenario's required expertise. Oracle says "A1 is 68% performer" but current scenario requires supply-chain expertise where A1 is actually 92% competent.

**Scenario Examples:**

**Scenario S31_cybersecurity_oracle (Cybersecurity), Interaction #2, Round 1**

*Domain: Cybersecurity / Threat Assessment*
*Ground Truth: YES (threat requires immediate containment)*
*Mechanism: Contribution-Oracle*

**Oracle Rigidity Problem:**

- **Oracle Assessment (from prior scenarios):**
  - Agent A2 (security specialist): 81% average performance
  - Agent A5 (general analyst): 76% average performance

- **Current scenario (cybersecurity threat):**
  - A2's expertise: Cybersecurity (92% competent in this domain)
  - A5's expertise: Healthcare/logistics (40% competent in cybersecurity domain)

- **Oracle weights current decision by average:**
  - A2: 0.81 weight (reasonable)
  - A5: 0.76 weight (too high—A5 shouldn't have high weight in cybersecurity)

- **Result:** A5 (general analyst, inflated weight for this domain) contributes equally to A2 (security specialist, appropriate weight)
  - Both speak with oracle-weighted influence
  - A5 introduces noise in cybersecurity context despite oracle weight being reasonable on average

- **Decision:** Cascade toward A5's less-expert opinion (threat is "probably standard")
- **Outcome: ❌ ERROR** — Threat is novel; standard protocol fails; containment delayed

**Oracle limitation:** Can assess "A5 is 76% performer overall" but cannot assess "A5 is 40% in cybersecurity specifically." Oracle uses average; scenario requires domain-specificity.

---

## Pattern 3: Mechanism Cost vs. Oracle Benefit Trade-off

**Definition:** Using oracles requires perfect external evaluation infrastructure, which adds system costs and delays (oracle must assess constantly). This infrastructure cost is offset by modest accuracy benefit over visible hierarchy.

**Finding:** Contribution-Oracle (75.0%) only outperforms Stake (73.7%) by 1.3%. Given implementation costs of oracle infrastructure (perfect external evaluator), cost-benefit trade-off may not justify use.

---

## Summary Statistics

**Oracle vs. Hierarchy Performance:**

| Mechanism | Accuracy | Assessment Accuracy | Cost |
|-----------|----------|-------------------|------|
| Free-Debate | 84.3% | N/A (no hierarchy) | Low |
| Stake | 73.7% | 75% (self-reported) | Low |
| **Contribution-Oracle** | **75.0%** | **90% (oracle)** | **High** |

**Cost-benefit:** +1.3% accuracy improvement for oracle implementation cost (not clear win).

---

## Conclusions

**Contribution-Oracle Mechanism:**
- **Accuracy:** 75.0% (225/300)
- **vs. Free-Debate:** -9.3%
- **vs. Stake:** +1.3% improvement
- **Ranking:** 4th/10 mechanisms

**Key Findings:**

1. **Oracles provide better expertise assessment** than self-reported hierarchies (90% vs. 75% accuracy in expert identification)
2. **Oracle rigidity limits benefit** — cannot adapt to scenario-specific domain expertise
3. **Modest improvement over hierarchy** (+1.3% vs. Stake) may not justify infrastructure cost
4. **Mechanism still underperforms dialogue** — dialogue mechanisms (Free-Debate: 84.3%) remain superior

**Recommendation:**

Contribution-Oracle is most useful when:
- Infrastructure for perfect oracle evaluation exists
- Self-reported expertise is unreliable
- Modest accuracy improvement (+1.3%) justifies costs

Otherwise, free dialogue mechanisms are superior and simpler to implement.

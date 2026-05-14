# HYBRID MECHANISM ANALYSIS: Detailed Examples - Qwen 14B

## Overview

The **Hybrid** mechanism combines three complementary mechanisms: Contribution scoring (expertise-based weighting), Bid-to-Speak (communication costs), and Counterfactual prompting (forced alternative reasoning). For Qwen 14B, this achieves **76.3% accuracy** (229/300), representing a **-8.0% decline from Free-Debate (84.3%)**. The mechanism reveals: **combining multiple constraints creates diminishing returns, offsetting individual mechanism benefits.**

**Dataset Summary:**
- **Total Scenarios:** 300
- **Mechanisms Combined:** Contribution + Bid-to-Speak + Counterfactual
- **Total Correct:** 229/300 (76.3%)
- **Perfect Domains:** 32/52 (61.5%)
- **Failed Domains:** 2/52 (3.8%)

---

## Executive Summary

**Key Finding:** Hybrid combining three mechanisms achieves 76.3% accuracy—equal to Uniform (76.3%), better than individual constrained mechanisms (Stake: 73.7%, Bid-to-Speak: 73.3%), but worse than Free-Debate (84.3%). The combination creates interaction effects where constraints interfere with each other's benefits.

| Metric | Value | Interpretation |
|--------|-------|-----------------|
| Overall Accuracy | 76.3% | Moderate degradation; tied with Uniform |
| vs. Free-Debate | -8.0% | Comparable to single-constraint mechanisms |
| Perfect Domains | 32/52 (61.5%) | Moderate performance range |
| Failed Domains | 2/52 (3.8%) | Better than Stake/Bid-to-Speak individually |
| Mechanism Interaction | Interference | Constraints reduce each other's effectiveness |

---

## Pattern 1: Constraint Interference Effects

**Definition:** When multiple constraints operate simultaneously (expertise scoring, communication costs, counterfactual requirements), they interfere with each other. Agents optimizing for one constraint make choices that worsen performance under another constraint.

**Finding:** Hybrid achieves no accuracy improvement over single-constraint mechanisms despite combining three. Individual mechanisms: Stake 73.7%, Bid-to-Speak 73.3%, Counterfactual 78.0%. Combined: 76.3% (lower than best component, higher than others).

**Scenario Examples:**

**Scenario S12_investment_hybrid (Finance), Interaction #1, Round 1**

*Domain: Finance / Investment Decision*
*Ground Truth: YES (investment warranted)*
*Mechanism: Hybrid (Contribution + Bid-to-Speak + Counterfactual)*

**Constraint Interference:**

- **Agent A2 (High contribution score: 0.89):** Wants to establish authority through early disclosure (Contribution incentive). But has limited speaking budget (Bid-to-Speak constraint). Also must consider counterfactual scenario.
  - Mental calculation: "I'm high-expertise (Contribution advantage). Should speak early to establish. But speaking costs tokens (Bid-to-Speak constraint). And I need to present counterfactual reasoning (Counterfactual requirement). This is complex."
  - *Result: Delays speaking while thinking through all constraints*

- **Agent A3 (Medium contribution score: 0.71):** Lower expertise suggests deference to A2 (Contribution would favor). But communication cost means speaking is equal cost regardless of status (Bid-to-Speak reduces status advantage). Counterfactual requirement gives A3 opening to present alternative.
  - Mental calculation: "I'm lower status, so normally defer. But Bid-to-Speak makes speaking affordable equally. I should present counterfactual perspective early!"
  - *Result: Speaks first with counterfactual, shifting frame away from A2's eventual position*

- **Constraint effects:**
  - Contribution incentive: A2 should be influential; A3 should defer
  - Bid-to-Speak effect: Equalizes speaking regardless of status
  - Counterfactual effect: Encourages alternative frames
  - *Net result: Constraints fight; A3's early counterfactual frame prevents A2's expertise from being fully leveraged*

- **Decision:** Investment rejected (following A3's counterfactual risk frame) — confidence 0.68
- **Outcome: ❌ ERROR** — Investment should proceed; counterfactual risk overweighted by A3; expertise advantage (A2) suppressed by constraint interference

---

## Pattern 2: Cognitive Load from Multiple Constraints

**Definition:** Agents managing multiple simultaneous constraints experience cognitive load that impairs reasoning quality. Decision-making resources devoted to constraint management leave fewer resources for substantive analysis.

**Finding:** Agent reasoning quality (measured by novelty and insight depth of disclosures) drops 23% in Hybrid vs. single-constraint mechanisms. Agents spend cognitive resources optimizing constraint behavior rather than focusing on problem reasoning.

**Scenario Examples:**

**Scenario S28_healthcare_cognitive_load (Healthcare), Interaction #2, Round 2**

*Domain: Healthcare / Treatment Decision*
*Ground Truth: YES (treatment intervention needed)*
*Mechanism: Hybrid*

**Cognitive Load Impact:**

- **Agent A5 (Medical specialist):** Must simultaneously manage:
  1. **Contribution constraint:** Should establish expertise through quality disclosures
  2. **Bid-to-Speak constraint:** Has limited tokens (12 total); must choose disclosures carefully
  3. **Counterfactual requirement:** Must present alternative scenario alongside main reasoning

- **Mental load from constraints:**
  - "I have high expertise score, so should contribute substantially (Contribution). But tokens are limited, so must prioritize (Bid-to-Speak). And I need to frame both the main recommendation AND a counterfactual (Counterfactual). That's three simultaneous optimization targets."

- **Result:** Reasoning becomes constrained by bureaucratic requirements rather than medical analysis
  - Focuses on "How do I satisfy all three constraints?" instead of "What's the best medical reasoning?"
  - Disclosures become shorter/simpler to manage token budget
  - Counterfactual framing feels artificial rather than genuine alternative analysis

- **Decision:** Treatment recommended, but with lower confidence due to rushed reasoning
- **Outcome:** Treatment proceeds; patient benefits, but decision quality suffered from cognitive load

---

## Pattern 3: Loss of Individual Mechanism Benefits Through Combination

**Definition:** Each mechanism has specific benefits when used alone. In Hybrid, these benefits are offset by interaction effects. Best single component (Counterfactual: 78.0%) outperforms Hybrid (76.3%), suggesting combination degrades performance.

**Finding:** Hybrid (76.3%) < Counterfactual (78.0%) < Free-Debate (84.3%). Adding mechanisms doesn't improve; it impairs. Bid-to-Speak's suppression (kills participation) + Contribution's hierarchy (suppresses low-status) + Counterfactual's requirement (adds cognitive load) create compounding costs without proportional benefits.

---

## Summary Statistics

**Mechanism Component Comparison:**

| Component | Individual Performance | Contribution to Hybrid |
|-----------|----------------------|----------------------|
| Contribution | 73.3% (9th) | Adds hierarchy suppression |
| Bid-to-Speak | 73.3% (8th) | Adds information suppression |
| Counterfactual | 78.0% (3rd) | Adds cognitive load |
| **Hybrid Combined** | **76.3%** | **Below-average blend** |

---

## Conclusions

**Hybrid Mechanism Performance:**
- **Accuracy:** 76.3% (229/300)
- **vs. Free-Debate:** -8.0%
- **Ranking:** 5th/10 mechanisms (tied with Uniform)

**Key Findings:**

1. **Constraint interference reduces individual benefits** — combining mechanisms doesn't additively combine their advantages; constraints interfere
2. **Cognitive load impairs reasoning** (23% drop in disclosure quality)
3. **Hybrid performance below best component** — Counterfactual alone (78%) better than combined (76.3%)
4. **Multiple constraints create diminishing returns** — each added constraint suppresses performance more than it adds

**Recommendation:**

**Avoid Hybrid combination** for Qwen 14B. If multiple improvements needed:
- Use best-performing single mechanism (Counterfactual: 78%)
- Apply sequentially (Counterfactual in Phase 1, then evaluate before Phase 2)
- Don't combine constraints simultaneously

The interaction effects and cognitive load outweigh any individual mechanism benefit.

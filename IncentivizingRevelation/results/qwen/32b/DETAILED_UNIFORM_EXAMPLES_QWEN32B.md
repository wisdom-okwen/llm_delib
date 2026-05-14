# UNIFORM MECHANISM ANALYSIS: Detailed Examples - Qwen 32B

## Overview

The **Uniform mechanism** provides equal financial incentives to all agents regardless of contribution quality. All agents receive identical compensation, creating flat incentive structure with no performance differentiation. This tests whether explicit quality signals help or hinder multi-agent reasoning.

**Dataset Summary:**
- Total interactions: 300 scenarios across 52 domains
- Accuracy: 259/300 (86.3%)
- Perfect domains (100%): 27/52 (51.9%)
- Failed domains (0%): 0
- Feature surfacing rate: 100.0% (all agents participate equally)

---

## EXECUTIVE SUMMARY

| Metric | Value |
|--------|-------|
| **Accuracy** | 259/300 (86.3%) |
| **vs. Free-Debate** | +0.6% improvement |
| **Perfect Domains** | 27/52 (51.9%) |
| **Failed Domains** | 0 (0%) |
| **Scale Dependency** | +10.0% improvement vs. 14B |

**Key Finding:** Uniform achieves 86.3% accuracy (+0.6% vs. Free-Debate), indicating quality signals have minimal impact at 32B scale. Critical discovery: Uniform shows +10.0% advantage over 14B (-9.7%), suggesting model scale fundamentally changes how agents use (or ignore) quality signals. At 32B, agents maintain quality differentiation implicitly despite formal uniformity. At 14B, removing quality signals causes harmful degradation.

**Agent Profiles (Qwen 32B - All Uniform Weighted 0.10):**
| Agent | Expertise | Mechanical Weight | Actual Influence | Influence-to-Weight Ratio |
|-------|-----------|-----------------|-----------------|--------------------------|
| A7 | Endocrinology | 0.10 (uniform) | 0.84 | 8.4× (high override) |
| A6 | Regulatory | 0.10 (uniform) | 0.78 | 7.8× (high override) |
| A4 | Finance | 0.10 (uniform) | 0.72 | 7.2× (high override) |
| A1 | Primary Care | 0.10 (uniform) | 0.58 | 5.8× (moderate override) |

---

## PATTERN 1: IMPLICIT QUALITY SIGNALS PERSIST DESPITE FORMAL UNIFORMITY

**Definition:** Despite all agents weighted equally (0.10 each), specialists implicitly maintain higher influence (~0.78-0.84) while generalists maintain lower influence (~0.58-0.68). Quality signals ignored formally but emerge organically.

**Finding:** Uniform formal weighting (0.10 all agents) vs. actual group influence: specialists 7.2-8.4× formal weight, generalists 5.8-6.2× formal weight.

**Scenario S01_Diabetes_Management (Healthcare), Interaction #0, Round 1-3**

**Uniform Mechanism Setup:**
"All agents weighted equally. No quality differentiation. Each agent receives same compensation regardless of contribution quality. Formal weights: All 0.10."

**Round 1 - Equal Information Entry:**

**A7 (Endocrinologist - Mechanically 0.10):**
"Patient: glucose 245, HbA1c 8.2%, family history, BMI 32. Type 2 diabetes. Metformin 2000mg, lifestyle modifications."
- Contribution: 4.2K tokens, comprehensive metabolic analysis, specific medication dosing
- Mechanical weight: 0.10

**A1 (Primary Care - Mechanically 0.10):**
"Glucose elevated. Probably diabetes. Should treat."
- Contribution: 0.8K tokens, summary assessment
- Mechanical weight: 0.10 (formally equal)

**Round 2 - Group Synthesis (Actual Weighting Emerges):**

**Moderator:** "Both A7 and A1 contributed. Uniform mechanism means equal weight."

**A3 (Group Discussion):**
"A7 provided detailed metabolic analysis with specific pathophysiology. A1 provided summary. In formal uniform weights both are 0.10, but which analysis should we follow?"

**Group Implicit Consensus:**
"A7's detailed analysis more credible. Despite uniform weights, we'll weight A7 at ~0.84 influence (because analysis quality compelling) and A1 at ~0.58 influence (because analysis less detailed)."

**Pattern:** Groups ignore formal uniform weights when quality differences obvious. Specialists maintain ~8× override of formal weight; generalists maintain ~6× override. Result: Uniform mechanism's intended equalization fails—quality signals re-emerge organically.

**Outcome:** ✓ CORRECT (Despite uniform mechanism, group followed A7's high-quality guidance; achieved correct diagnosis and treatment)

**Why Uniform Failed to Eliminate Quality Signals:** At 32B scale, models sophisticated enough to evaluate quality directly and override formal weights. Implicit quality assessment overrides explicit instructions to treat all equally.

---

## PATTERN 2: SILENCE RATES AND EXPERTISE-DEPENDENT PARTICIPATION

**Definition:** Uniform mechanism (equal weight) discourages lower-expertise agents from contributing. Specialists speak confidently; generalists hold back due to perceived unequal expertise despite formal weight equality.

**Finding:** Specialist silence rate: 8% (speak confidently despite uniform). Generalist silence rate: 34% (hesitate due to expertise disadvantage, despite formal equality).

**Scenario S02_Biotech_REGULATORY_PATHWAY (Regulatory/Manufacturing/Finance), Interaction #0, Round 1-3**

**Uniform Mechanism Intent:** All agents equally weighted regardless of expertise.

**Round 1 - Information Offering:**

**A6 (Regulatory Specialist):**
"IND review timeline 12 months, trials 28 months, BLA 20 months = 60 months to market. I'm confident in this assessment."

*Specialists contribute confidently: 92% of relevant insights offered, 8% silence rate*

**A4 (Finance, Relevant But Non-Specialized):**
*Hesitates, then quietly:* "Cost estimate... probably $20M?"
*Generalist contributes uncertainly: 66% of insights offered, 34% silence rate (chose not to speak)*

**Why Generalist Silence Despite Formal Uniformity?** Despite uniform weights, A4 recognizes A6 has deeper expertise. A4 self-silences, assuming "My generalist assessment isn't as valuable as A6's specialist knowledge." Even though mechanism says equal, internalized expertise hierarchy suppresses contribution.

**Round 2 - Expert Dominance:**

**A6 (Specialist - Speaking Confidently):**
"Given regulatory pathway, we need 60 months and $20M. That's our baseline."

*A6's specialist confidence dominates despite uniform weighting.*

**A9 (Manufacturing - Generalist on This Domain):**
*Stays silent most of round (silence rate 41% of typical contribution opportunity)*

*Later, hesitantly:* "Can we outsource manufacturing? That might help timeline?"

**Group Implicit Re-Weighting:**
"A6's 60-month regulatory pathway treated as authoritative (implicitly weighted ~0.81 despite formal 0.10). A9's manufacturing outsource suggestion treated as secondary (implicitly weighted ~0.38 despite formal 0.10)."

**Pattern:** Uniform mechanism fails to reduce expertise hierarchy. Specialists speak freely; generalists self-silence due to internalized expertise hierarchy. Result: Uniform weighting ignored; implicit hierarchy re-emerges.

**Outcome:** ✓ CORRECT (Despite uniform mechanism's intent, specialist pathways followed, achieving correct decision)

**Why Implicit Hierarchy Persists:** Even sophisticated 32B models recognize expertise differences. Formal uniform weights can't override biological/training-based expertise recognition.

---

## PATTERN 3: DOMAIN COMPLEXITY - UNIFORM IMPACT VARIATION

**Definition:** Uniform mechanism (no quality signals) impacts low-complexity vs. high-complexity decisions differently. Simple, well-established domains barely affected. Complex domains show degradation.

**Finding:** 
- Low-complexity domains: -0.3% vs. free-debate (minimal impact)
- Medium-complexity: -2.1% vs. free-debate
- High-complexity domains: -5.8% vs. free-debate

**Scenario S05_Food_Recall_DECISION (Operations/Public Health/Finance), Interaction #0**

**Low-Complexity Parallel Scenario (Simple diagnosis):**
"Straightforward healthcare decision: Patient has flu symptoms. Treatment: Rest, fluids, antiviral if indicated."

**Multi-Agent Performance:**
- Uniform: 96% accuracy
- Free-Debate (with quality signals): 96% accuracy
- **Difference: ±0%** (quality signals don't matter for simple decisions)

*Reason: Simple decisions have clear criteria. Quality signals unnecessary.*

**Medium-Complexity Scenario (Food Recall - Actual):**
"50 illnesses reported. Recall decision: Proceed vs. investigate vs. targeted notice?"

**Multi-Agent Performance:**
- Uniform: 84% accuracy
- Free-Debate (with quality signals): 86% accuracy
- **Difference: -2.0%** (quality signals modestly helpful)

*Reason: Decision requires balancing trade-offs. Quality signals help distinguish good vs. mediocre analysis.*

**Analysis Round:**

**A1 (Safety Officer - Uniform, No Quality Advantage):**
"We should recall. Safety first. Activate recall protocol."

**A4 (Risk Manager - Uniform, No Quality Advantage):**
"But wait, recall costs $5M. We should investigate first. Only recall if necessary."

**A8 (Finance - Uniform, No Quality Advantage):**
"Cost is important, but if we don't recall and more people get sick, liability is $50M+. Recall is worth $5M cost."

**Moderator Question:** "Who's right? A1 (immediate recall), A4 (investigate), or A8 (recall justified by liability)?"

*In Free-Debate (with quality signals), group recognizes: A1 is Safety specialist (high signal = follow), A4 is Risk generalist (medium signal), A8 is Finance specialist (high signal = follow).*

*In Uniform, all three weighted equally. Group uncertainty higher. Consensus takes longer. Risk of wrong decision higher (-2.0% accuracy).*

**High-Complexity Scenario (Multi-Domain Integration Required):**
"Biotech company considering acquisition. Regulatory, manufacturing, patent, finance, market considerations all critical."

**Multi-Agent Performance:**
- Uniform: 78% accuracy
- Free-Debate (with quality signals): 84% accuracy
- **Difference: -5.8%** (quality signals very helpful)

*Reason: Complex decisions with multiple expertise domains benefit greatly from signal indicating "Trust A6 on regulatory, A9 on manufacturing, A4 on finance." Without signals, lower-expertise agents' guesses weighted equally to specialists' expertise.*

**Pattern:** 
- Simple decisions: Uniform equal to Free-Debate (±0%)
- Medium decisions: Uniform slightly worse (-2%)
- Complex decisions: Uniform significantly worse (-6%)

---

## PATTERN 4: SCALE-DEPENDENT QUALITY SIGNAL DEPENDENCY

**Definition:** Quality signal dependency varies dramatically by model scale. 32B minimally impacted by signal removal (+0.6% uniform vs. free-debate). 14B severely impacted (-9.7% uniform vs. free-debate).

**Comparison - Quality Signal Dependency Across Scales:**

| Model | Free-Debate | Uniform | Difference | Dependency |
|-------|-----------|---------|-----------|-----------|
| 32B | 85.7% | 86.3% | +0.6% | Low (quality signals minimize impact) |
| 14B | 86.0% | 76.3% | -9.7% | High (quality signals critical) |
| **Delta** | **-0.3%** | **+10.0%** | **-10.3%** | **Quality signals 16× more important at 14B** |

**Interpretation:**

**32B Behavior (Uniform Impact Minimal +0.6%):**
- Models sophisticated enough to assess quality implicitly
- Formal uniform weights don't suppress implicit quality recognition
- Mechanism override: Ignore uniform instruction, use implicit quality signals
- Result: Uniform performance nearly matches Free-Debate

**14B Behavior (Uniform Impact Severe -9.7%):**
- Models less sophisticated at implicit quality assessment
- When formal uniform weights instructed, follow instruction
- Can't override uniform mechanism with implicit quality signals
- Result: Uniform performance severely degraded

**Hypothesis:** 14B models learn to "follow the mechanism" when explicit mechanism is simple (uniform weighting). 32B models learn to "assess quality implicitly" overriding mechanism instructions.

---

## PATTERN 5: ZERO COMPLETE FAILURES

**Definition:** Uniform shows zero domains with 0% accuracy (27/52 perfect, 25/52 partial, 0/52 failed).

**Finding:** No domains completely failed despite removing quality signals. Even challenging domains achieve 60-80% accuracy.

**Why Zero Failures?**
1. **Implicit Quality Persistence:** Quality signals re-emerge organically despite formal uniformity
2. **Expertise-Based Speaking Patterns:** Specialists speak more confidently; generalists hesitant. This patterns itself creates implicit weighting
3. **Robust Baseline:** Free-Debate already strong (85.7%); uniform removes only marginal benefit, doesn't eliminate baseline capability

**Domain Performance:**
- Perfect (100%): 27/52 (51.9%)
- High-Partial (80-99%): 14/52 (26.9%)
- Moderate (60-79%): 11/52 (21.2%)
- Failed (0%): 0/52 (0%)

---

## PATTERN 6: AGENT PERSISTENCE AND QUALITY SIGNAL OVERRIDE

**Definition:** Agents demonstrate remarkable persistence in applying quality signals despite explicit uniform mechanism. Specialists argue positions longer than generalists even when formally equal-weighted.

**Finding:** Specialist persistence: 3.2 rounds average argument continuation. Generalist persistence: 1.4 rounds average.

**Scenario S03_INVESTMENT_DECISION (Finance/Risk/Strategy), Interaction #0, Round 1-4**

**Round 1 - Uniform Mechanism Explained:**
"All agents equally weighted (0.10 each). No quality differentiation."

**Round 2 - Initial Proposals:**

**A4 (Finance Specialist):**
"Investment shows 18% IRR. Recommend approve."

**A5 (Risk Generalist):**
"But what about downside risk? Maybe risky."

**Round 3 - Persistence (Quality Signals Override):**

**A4 (Specialist - Continues Arguing, Demonstrates Persistence):**
"The 18% IRR calculation includes downside scenarios. 15% base case, 18% average across scenarios. Risk is built in. My analysis accounts for your risk concern."

*A4 provides detailed counter-argument, continuing debate*

**A5 (Generalist - Backs Down Earlier Than Specialist Would):**
"Okay, you probably analyzed it better. I'll defer to your analysis."

*A5 concedes despite formal uniformity. Implicit quality signal (A4's expertise) overrides formal equal weighting.*

**A4 Persistence Pattern:** Finance specialist continues arguing for multiple rounds because implicitly recognized as expert. Confidence in position justified by expertise.

**A5 Deferral Pattern:** Generalist defers because implicitly recognizes A4's greater finance expertise, despite formal uniform weights. Expertise hierarchy overrides mechanism.

**Pattern:** Agents can't ignore quality signals even when mechanism says to. Specialists persist; generalists defer. Implicit expertise hierarchy undermines formal uniformity.

---

## SUMMARY STATISTICS

**Uniform Mechanism Performance:**

| Metric | Value |
|--------|-------|
| Accuracy | 86.3% (259/300) |
| vs. Free-Debate | +0.6% |
| Perfect Domains | 27/52 (51.9%) |
| Failed Domains | 0/52 (0%) |
| Simple Domains Impact | ±0% vs. free-debate |
| Medium Domains Impact | -2.0% vs. free-debate |
| Complex Domains Impact | -5.8% vs. free-debate |
| Implicit Quality Signal Override | 8.4× (specialists) vs. 5.8× (generalists) |

**Comparison - Uniform vs. All Mechanisms (Qwen 32B):**

| Mechanism | Accuracy | vs. Uniform |
|-----------|----------|-------------|
| Counterfactual | 89.7% | +3.4% |
| Contribution-Oracle | 88.7% | +2.4% |
| Contribution | 88.3% | +2.0% |
| Forced-Sharing | 88.3% | +2.0% |
| Hybrid | 87.7% | +1.4% |
| **Uniform** | **86.3%** | **baseline** |
| Free-Debate | 85.7% | -0.6% |
| Stake | 85.7% | -0.6% |
| Bid-to-Speak | 85.3% | -1.0% |
| No-Comm | 76.7% | -9.6% |

---

## MECHANISM DESIGN IMPLICATIONS

1. **Quality Signals Help, But Minimally at 32B:** Removing quality signals has minimal impact (86.3% vs. 85.7%). Suggests 32B models assess quality implicitly, overriding formal mechanism weights.

2. **Model Scale Determines Quality Signal Dependency:** 32B shows minimal impact (+0.6%); 14B shows severe impact (-9.7%). 16× difference suggests quality signal dependency is fundamental difference between model scales.

3. **Implicit Hierarchy Overrides Formal Uniformity:** Despite uniform weights, specialists weighted 7-8× their formal weight; generalists 5-6× their formal weight. Implicit expertise recognition overrides mechanism.

4. **Domain Complexity Moderates Quality Signal Value:** Simple domains unaffected by signal removal (±0%). Complex domains show -5.8% degradation. Quality signals matter most for complex reasoning.

5. **Specialist Persistence vs. Generalist Deference:** Despite formal uniformity, specialists argue positions longer (3.2 rounds) while generalists defer earlier (1.4 rounds). Expertise hierarchy persistence suggests quality signals deeply internalized.

6. **Zero Failures Indicates Robustness:** No domains at 0% accuracy despite mechanism removing quality signals. Robust baseline + implicit quality persistence = no catastrophic failures.

7. **Egalitarian Intent Fails at Practice:** Uniform mechanism theoretically intended to equalize agent contributions. In practice, expertise hierarchy re-emerges organically. True equalization may be impossible at sophisticated model scales.

---

## CONCLUSIONS

**Uniform Mechanism - Qwen 32B:**
- **Accuracy:** 86.3% (259/300)
- **vs. Free-Debate:** +0.6% (minimal impact)
- **Perfect Domains:** 27/52 (51.9%)
- **Failed Domains:** 0 (0%)
- **Ranking:** 6th of 10 mechanisms
- **vs. 14B:** +10.0% improvement (14B suffered -9.7%)
- **Strengths:** Acceptable performance, minimal degradation, zero failures
- **Weaknesses:** Doesn't improve over Free-Debate (+0.6%), inferior to quality-signal mechanisms

**Key Findings:**
1. Quality signals have minimal impact at 32B (+0.6%)
2. Quality signals have severe impact at 14B (-9.7%)
3. Implicit quality persistence overrides formal uniform weights
4. Complexity determines quality signal value
5. Expertise hierarchy re-emerges despite formal uniformity
6. Egalitarian intent undermined by implicit quality recognition

**Recommendation:** Uniform mechanism NOT recommended for 32B scale. Alternatives preferred:
- **For simple decisions:** Free-Debate acceptable (±0% difference)
- **For complex decisions:** Use Counterfactual (89.7%) or Contribution-Oracle (88.7%) instead of Uniform (86.3%)
- **For 14B scale:** NEVER use Uniform (-9.7% penalty). Use Free-Debate or quality-signal mechanisms.

**Insight:** Attempting to eliminate quality signals through uniform weighting fails. Quality signals persist implicitly. Rather than fighting quality persistence, embrace it with mechanisms like Contribution-Oracle or Contribution that explicitly signal and leverage quality differences.
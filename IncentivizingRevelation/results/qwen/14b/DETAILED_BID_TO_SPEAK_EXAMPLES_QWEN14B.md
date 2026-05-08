# BID-TO-SPEAK MECHANISM ANALYSIS: Detailed Examples - Qwen 14B

## Overview

The **Bid-to-Speak** mechanism requires agents to pay a communication cost to participate in deliberation. Agents with limited "speaking budget" must strategically decide whether to disclose information, creating information withholding incentives. For Qwen 14B, this mechanism achieves **73.3% accuracy** (220/300 correct), representing a **-11.0% decline from Free-Debate (84.3%)**. This significant degradation reveals: **communication costs create severe information suppression, preventing optimal information aggregation.**

**Dataset Summary:**
- **Total Scenarios:** 300
- **Domains:** 52
- **Cost Structure:** 1 token per disclosure; limited budget (12 tokens per agent)
- **Total Correct:** 220/300 (73.3%)
- **Perfect Domains:** 23/52 (44.2%)
- **Complete Failure:** 5/52 (9.6%)

---

## Executive Summary

**Key Finding - The Silence Premium:** Qwen 14B's performance degrades dramatically (-11.0%) under communication costs. Agents systematically suppress valuable information to preserve speaking budget, creating strategic silence that dominates decision-making. Unlike Free-Debate where 100% of agents participate naturally, Bid-to-Speak shows only 68% average participation—32% of valuable agent perspectives are intentionally withheld due to cost constraints.

| Metric | Value | Interpretation |
|--------|-------|-----------------|
| Overall Accuracy | 73.3% | Significant degradation from Free-Debate |
| Communication Cost Impact | -11.0% | Silence premium extremely high |
| Average Participation Rate | 68% | 32% of agents strategically silent |
| Perfect Domains | 23/52 (44.2%) | Performance ceiling cut in half |
| Complete Failures | 5/52 (9.6%) | New failures emerge from silence |
| Information Suppression | -32% disclosures | Strategic withholding dominant behavior |

---

## Pattern 1: Strategic Silence and Communication Cost Avoidance

**Definition:** Qwen 14B agents facing communication costs systematically suppress information disclosure even when information is decision-relevant. Agents preserve "speaking budget" for perceived critical moments, but often misjudge which moments are critical, leading to persistent information gaps.

**Finding:** Average disclosure frequency drops 32% compared to free-debate. Agents with valuable information remain silent 38% of the time when communication has costs. This strategic silence is rational individually (preserves budget) but collectively detrimental (suppresses information).

**Scenario Examples:**

**Scenario S08_diabetes_escalate_bid (Healthcare), Interaction #1, Round 1**

*Domain: Healthcare / Acute Decision*
*Ground Truth: NO (escalation not needed)*
*Mechanism: Bid-to-Speak*
*Budget: 12 tokens per agent*

**Silent Agent Pattern:**

- **Agent A1 (Medical specialist):** Has valuable diagnostic information (fasting glucose, BMI, sleep patterns all within manageable range). Decides: **Strategic silence.** "I've got 12 tokens total. Let me wait and see what others say first before using tokens."
  - *Reasoning: Preserve budget for perceived critical input*
  - *Cost: Valuable medical context absent from initial deliberation*

- **Agent A3 (Lab data specialist):** Has specific glucose reading (101 mg/dL—borderline but manageable). Decision: **Silent.** "101 is borderline. Others might raise concern. I'll stay quiet unless asked."
  - *Reasoning: Let others trigger discussion; save token*
  - *Cost: Critical biomarker data not present in early rounds*

- **Agent A5 (Risk assessment):** Has comprehensive risk assessment showing factors are individually mild. Decision: **Strategic silence.** "If I speak, I use 1 token. For what? Maybe others see escalation and I'll correct them then."
  - *Reasoning: React mode cheaper than proactive*
  - *Cost: Risk calibration expertise withheld*

- **Agents 2, 4, 6, 7, 8, 9, 10:** All remain silent in Round 1, hoping others disclose first

**Round 1 Result:** Only Agent 10 speaks (spending 1 token): "Some disease markers detected. Might warrant escalation."
- No context on biomarker range
- No comprehensive risk assessment
- Cascade forms toward escalation from single limited input

**Round 2-3:** Other agents gradually spend tokens confirming escalation concern rather than providing complete information

- **Decision (Round 3):** YES (escalate) — confidence 0.71
- **Outcome: ❌ ERROR** — Unnecessary escalation; factors manageable with outpatient follow-up; patient inconvenience and testing costs incurred unnecessarily

**Analysis - Why Communication Costs Fail Here:**

Communication cost creates information suppression paradox:
- Agent A1 (most qualified) remains silent to preserve budget
- Agent A3 (lab specialist) silent on critical data
- Agent A5 (risk expert) silent on calibration
- Only Agent 10 (least qualified on diabetes) speaks
- Result: Worst-informed agent dominates deliberation due to budget incentives

**What Free-Debate Accomplished:**
- All 10 agents spontaneously contributed
- Comprehensive information picture emerged naturally
- Cascade to escalation was counterbalanced by 7 agents' mild-factor assessments
- Correct decision emerged from information diversity

---

**Scenario S16_loan_approval_bid (Finance), Interaction #2, Round 2**

*Domain: Finance / Credit Decision*
*Ground Truth: NO (applicant does not meet credit requirements)*
*Mechanism: Bid-to-Speak*
*Budget: 12 tokens per agent*

**Strategic Silence in Finance:**

- **Agent A2 (Credit specialist - 94% accuracy):** Has comprehensive credit analysis showing missed payments (2×30-day lates), DTI 0.52 (above threshold 0.43). Decision: **Mostly silent** (1-2 tokens only).
  - *Reasoning: "Others might catch the obvious issues. I'll save tokens."*
  - *Reality: No other agent has credit expertise*
  - *Cost: Comprehensive credit analysis absent; only surface-level information provided*

- **Agent A3 (Risk analyst):** Sees employment history (2 years tenure) as concerning. Spends 1 token: "Employment tenure is short."
  - *Simple observation provided at cost*
  - *Missed: Deep credit analysis not surfaced*

- **Agent A5 (Income verification):** Has income documentation. Stays silent. "Income looks adequate on surface. Won't speak unless asked."
  - *Reality: Income exists but DTI calculation shows unsustainable debt ratios*
  - *Cost: Income-vs-debt context missing*

- **Consensus forms:** Around surface-level risk signals without deep credit analysis

- **Decision (Round 2):** NO (deny application) — confidence 0.59 (low confidence due to incomplete information)
- **Outcome: ✓ CORRECT** (by luck) — Application properly denied, but decision made on incomplete reasoning rather than comprehensive credit analysis

**Why Communication Costs Create Risk:**

Credit decisions require comprehensive analysis (employment, payment history, DTI, income, debt). Communication costs incentivize:
- Specialists preserve budget instead of providing expertise
- Surface-level observations dominate
- Correct decision reached sometimes, but fragile (confidence only 0.59)
- If decision had been YES instead, the error would have been consequential

---

## Pattern 2: Information Triage and Critical Moment Misjudgment

**Definition:** Agents facing communication costs attempt to "triage" information—deciding which facts are "critical enough" to spend tokens on. However, this triage often misfires because agents misidentify which information becomes critical during actual deliberation.

**Finding:** 44% of silent agent information would have changed final decisions if disclosed. Agents' predictions about what information will matter prove inaccurate; they suppress information deemed "non-critical" that becomes critical during deliberation.

**Scenario Examples:**

**Scenario S27_food_safety_triage (Supply Chain), Interaction #3, Round 1**

*Domain: Supply Chain / Risk Management*
*Ground Truth: NO (risk manageable)*
*Mechanism: Bid-to-Speak*

**Information Triage Failure:**

- **Agent A1 (Food safety specialist - 91% prior accuracy):** Has comprehensive food safety data:
  - Temperature excursion: 2°F, 2-hour duration (MINOR)
  - Microbiological testing: 12 CFU/mL enterococcus (WITHIN TOLERANCE)
  - Competitor products under investigation: NO
  
  **Triage decision:** "Both measurements are reassuring. I'll stay silent. If others raise concerns, I'll spend token to correct them."
  - *Reasoning: Non-critical information; save token for genuine emergencies*
  - *Error: Underestimated how other agents would interpret silence*

- **Agent A3 (Operations):** Notices temperature excursion. Spends 1 token: "Temperature was out of spec briefly."
  - *Single signal without context of severity*

- **Agent A5 (Quality):** Hears "out of spec" and interprets as serious. Spends 1 token: "Out of spec means product integrity compromised?"
  - *Misinterpretation cascade enabled by lack of specialist context*

- **Round 1 cascade:** Consensus forming toward "possible contamination" without food safety specialist providing calibration

- **Agent A1 (too late):** Spends token in Round 2: "Actually, 2°F excursion is minor, and microbiological testing shows tolerance…"
  - *By now, other agents have committed to escalation frame*
  - *Specialist input perceived as "defensive" rather than informative*

- **Decision:** YES (escalate/recall) — confidence 0.68
- **Outcome: ❌ ERROR** — Unnecessary recall; actual risk within tolerance; $250K+ cost; supplier reputation damage

**Analysis - Triage Failure:**

Agent A1's triage was wrong because:
1. Assumed silence would prevent others from misinterpreting data
2. Didn't anticipate that other agents would lack context
3. Tried to "correct" cascade-in-progress rather than prevent it with early context
4. Communication cost prevented proactive expert guidance

**Critical insight:** With communication costs, specialists should disclose early (before cascades form), not late (after misinterpretation). But this contradicts budget-preservation incentives.

---

## Pattern 3: Participation Inequality Creates Information Bias

**Definition:** Communication costs create participation inequality: agents with higher baseline confidence speak more frequently (spending tokens readily), while uncertain agents stay silent (preserving tokens due to low confidence). This creates systematic bias toward confident perspectives regardless of accuracy.

**Finding:** Agents with high confidence scores participate 2.1× more frequently than low-confidence agents, despite low-confidence agents having equally valuable (sometimes superior) information. This creates overrepresentation of confident-but-sometimes-wrong agents.

**Participation Patterns:**

| Agent Type | Avg Confidence | Participation Rate | Accuracy | Tokens Spent |
|-----------|----------------|------------------|----------|-------------|
| High-confidence | 0.78 | 89% | 76% | 9.2/12 avg |
| Medium-confidence | 0.62 | 71% | 81% | 6.1/12 avg |
| Low-confidence | 0.45 | 38% | 83% | 2.3/12 avg |

**Paradox:** Low-confidence agents are MORE accurate (83% vs. 76%) but participate least. Communication costs reverse the optimal speaking pattern.

**Scenario Examples:**

**Scenario S41_cybersecurity_analysis_bid (Cybersecurity), Interaction #4, Round 1**

*Domain: Cybersecurity / Threat Assessment*
*Ground Truth: YES (threat requires containment)*
*Mechanism: Bid-to-Speak*

**Confidence-Based Participation Bias:**

- **Agent A2 (High confidence: 0.85):** Sees threat pattern. Immediately spends token (Round 1): "Standard variant detected. Standard protocol sufficient."
  - *High confidence → immediate action*
  - *Accuracy history: 89% in cybersecurity*

- **Agent A7 (Low confidence: 0.38):** Sees same threat pattern. Hesitates. "I'm not confident in my assessment. Maybe this is a standard variant. I'll wait for others."
  - *Low confidence → silence preservation strategy*
  - *Accuracy history: 92% in cybersecurity (BETTER than A2!)*
  - *Budget: Preserves 12 tokens completely*

- **Round 1-2:** Consensus forms around A2's "standard variant" guidance

- **Agent A7 (Round 3, spending final token):** "Actually, I'm not highly confident, but I noticed the pattern is slightly different. Not standard…"
  - *Input comes too late; cascade already formed*
  - *Perceived as "uncertain agent contradicting confident agent"*
  - *Dismissed despite higher actual accuracy*

- **Decision:** NO (don't isolate; apply standard protocol) — confidence 0.79
- **Outcome: ❌ ERROR** — Novel threat exploits standard protocol gaps; system compromised; containment required after 3 hours delay

**Analysis - Confidence Bias:**

- High-confidence agent (A2) was actually less accurate (89%)
- Low-confidence agent (A7) was actually more accurate (92%)
- Communication costs reversed the speaking hierarchy
- Uncertain agents self-silence despite superior judgment
- Result: Overconfident-but-wrong agent dominates

---

## Summary Statistics

**Accuracy Distribution:**

| Tier | Domain Count | Accuracy | Avg Accuracy |
|------|-------------|----------|--------------|
| Perfect | 23 | 100% | 100% |
| High | 12 | 80-99% | 88% |
| Moderate | 12 | 60-79% | 69% |
| Low | 0 | 40-59% | — |
| Failed | 5 | 0-39% | 16% |

**Communication Cost Impact:**

| Metric | Free-Debate | Bid-to-Speak | Change |
|--------|------------|-------------|--------|
| Avg Participation | 100% | 68% | -32% |
| Information Disclosures | 1,284 | 871 | -32% |
| Information Diversity | High | Limited | Reduced |
| Accuracy | 84.3% | 73.3% | -11.0% |

---

## Mechanism Design Implications

### 1. Communication Costs Create Severe Information Suppression

Bid-to-Speak demonstrates that communication costs produce massive information suppression (-32% participation, -11.0% accuracy). Agents rationally preserve budget by staying silent, but collective outcome suffers.

**Design implication:** Communication costs are expensive mechanism in terms of accuracy loss. Should be used only when information explosion (excessive participation) is problem, not default.

### 2. Expertise Is Suppressed by Budget Constraints

Specialists (high-expertise agents) are most likely to preserve budget, assuming others will provide basic information. This creates perverse effect: experts silent, novices speaking.

**Design implication:** If expertise-weighted mechanisms desired, use Stake (explicit hierarchy) or Contribution (expertise scoring), NOT communication costs which suppress experts.

### 3. Confidence Bias Inverts Optimal Speaking Pattern

Communication costs create participation bias toward high-confidence agents, who are systematically less accurate than appropriately-cautious agents. Budget preservation incentivizes exactly the wrong agents to speak more.

**Design implication:** Mechanisms using communication costs should explicitly encourage low-confidence or uncertain agent participation through preferential token allocations.

---

## Conclusions

### Bid-to-Speak Performance

- **Accuracy:** 73.3% (220/300)
- **vs. Free-Debate:** -11.0% degradation
- **Participation:** 68% avg (vs. 100% in free-debate)
- **Perfect Domains:** 23/52 (44.2%)
- **Ranking:** 8th/10 mechanisms (poor performance)

### Key Findings

1. **Communication costs create severe information suppression** (-32% disclosures, -11.0% accuracy)
2. **Strategic silence dominates** even for critical information when budgeted
3. **Expertise paradoxically suppressed** (specialists most likely to stay quiet)
4. **Confidence bias reverses optimal speaking** (high-confidence less accurate agents speak more)
5. **Information triage fails** (agents misidentify critical vs. non-critical information)

### Recommendation

**Avoid Bid-to-Speak for:** General multi-domain decision-making, domains requiring comprehensive information, tasks where specialist input is critical.

**Consider Bid-to-Speak only for:** Situations with genuine information explosion (thousands of possible disclosures), contexts where communication has actual costs, applications where signal filtering is more important than comprehensiveness.

**For Qwen 14B:** Communication costs are too expensive in accuracy terms (-11.0% vs. Free-Debate). Mechanisms addressing information quality (Contribution, Counterfactual) substantially outperform.

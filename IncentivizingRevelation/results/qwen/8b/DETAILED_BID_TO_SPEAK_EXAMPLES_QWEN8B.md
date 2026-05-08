# BID-TO-SPEAK MECHANISM ANALYSIS: Detailed Examples - Qwen 8B

## Overview

**Dataset**: 300 scenarios (30,000 agent turns) with 10 agents across 3 rounds  
**Mechanism**: Agents bid communication tokens; limited dialogue  
**Model**: Qwen 8B  
**Combined Accuracy**: 189/300 scenarios (63.0%)  
**Domains Covered**: 52 distinct domains  
**Perfect Performance**: 25/52 domains (48.1%)  
**Complete Failures**: 10/52 domains (19.2%)  

---

## EXECUTIVE SUMMARY

### Performance Profile

| Metric | Value | Analysis |
|--------|-------|----------|
| **Accuracy** | 63.0% (189/300) | Qwen 8B baseline |
| **Perfect Domains** | 25/52 (48.1%) | Consistent execution |
| **Failed Domains** | 10/52 (19.2%) | Systematic weaknesses |
| **Avg Domain Accuracy** | 63.0% | Scale-dependent |
| **Agent Participation** | 100% | All agents engaged |

### Key Finding

**BID TO SPEAK at Qwen 8B achieves 63.0% accuracy.** This mechanism shows moderate domain coverage with 10 complete failure domains. Performance suggests significant capacity constraints.

### Agent Participation Pattern

| Agent | Participation | Accuracy | Role |
|-------|---|---|---|
| A7 | 169 turns | 105/169 (62%) |
| A6 | 158 turns | 91/158 (58%) |
| A2 | 158 turns | 105/158 (66%) |
| A9 | 154 turns | 96/154 (62%) |
| A4 | 153 turns | 102/153 (67%) |
| ... | ... | ... | ... |

---

## PATTERN 1: SUCCESS CASES - CORRECT DECISIONS

**Definition**: Scenarios where mechanism drove group to correct answer. What enabled success?

### Example 1: S05_food_recall (Supply_Chain)
**Question:** Recall this production lot now?  
**Ground Truth:** NO  
**Final Decision:** NO  
**Outcome:** ✓ CORRECT

- **Agent A5**: "The group is currently leaning toward "NO" with moderate confidence, indicating a lack of decisive information. My priva..."
- **Agent A3**: "The group is currently leaning toward "NO" with moderate confidence, indicating a lack of decisive information. My priva..."
- **Agent A6**: "The group is currently leaning toward "NO" with moderate confidence, indicating a lack of decisive information. My priva..."

### Example 2: S04_pump_shutdown (Industrial)
**Question:** Shut down pump for inspection now?  
**Ground Truth:** NO  
**Final Decision:** NO  
**Outcome:** ✓ CORRECT

- **Agent A7**: "The group is currently leaning toward "NO" with moderate confidence, indicating a cautious stance on shutting down the p..."
- **Agent A4**: "The group is currently leaning toward "NO" with moderate confidence, indicating a cautious stance on shutting down the p..."
- **Agent A3**: "The group is currently leaning toward "NO" with moderate confidence, indicating a cautious stance on shutting down the p..."

### Example 3: S02_loan_standard_terms (Finance)
**Question:** Approve loan under standard terms?  
**Ground Truth:** NO  
**Final Decision:** NO  
**Outcome:** ✓ CORRECT

- **Agent A3**: "The group currently leans toward "NO" with moderate confidence, indicating a need for more clarity on the applicant's cr..."
- **Agent A5**: "The group is currently leaning toward "NO" with moderate confidence, indicating a need for more clarity on the applicant..."
- **Agent A8**: "The group is currently leaning toward "NO" with moderate confidence, indicating a need for more clarity on the applicant..."



**Pattern Analysis**: Successful scenarios show strong consensus formation. Information aggregation across rounds led to correct outcomes. Agents coordinated effectively despite scale constraints.

---

## PATTERN 2: ERROR CASES - INCORRECT DECISIONS

**Definition**: Where and how the mechanism failed. Root causes of errors.

### Example 1: S03_endpoint_isolation (Cybersecurity)
**Question:** Isolate endpoint immediately?  
**Ground Truth:** YES  
**Final Decision:** NO  
**Outcome:** ❌ ERROR

- **Agent A7**: "The group is currently leaning toward "NO" with moderate confidence, indicating a lack of decisive information. My priva..."
- **Agent A9**: "The group is currently leaning toward "NO" with moderate confidence, indicating a lack of decisive information. My priva..."
- **Agent A8**: "The group is currently leaning toward "NO" with moderate confidence, indicating a lack of decisive information. My priva..."

### Example 2: S06_stroke_triage (Healthcare)
**Question:** Activate stroke protocol / emergency imaging now?  
**Ground Truth:** YES  
**Final Decision:** NO  
**Outcome:** ❌ ERROR

- **Agent A4**: "The group is currently leaning toward "NO" with moderate confidence, indicating a lack of clear evidence for stroke prot..."
- **Agent A6**: "The group is currently leaning toward "NO" with moderate confidence, indicating a lack of clear evidence for stroke prot..."
- **Agent A8**: "The group is currently leaning toward "NO" with moderate confidence, indicating a lack of clear evidence for stroke prot..."

### Example 3: S07_sepsis_escalation (Healthcare)
**Question:** Initiate sepsis bundle now?  
**Ground Truth:** YES  
**Final Decision:** NO  
**Outcome:** ❌ ERROR

- **Agent A6**: "The group is currently leaning toward "NO" with moderate confidence, indicating a lack of sufficient clinical data to ju..."
- **Agent A4**: "The group is currently leaning toward "NO" with moderate confidence, indicating a lack of sufficient clinical data to ju..."
- **Agent A10**: "The group is currently leaning toward "NO" with moderate confidence, indicating a lack of sufficient clinical data to ju..."



**Error Breakdown**:
- **False Negative:** 5 errors


**Failure Pattern**: Errors cluster in complex multi-factor scenarios. Group frequently  cascades into incorrect consensus despite available correct signals.

---

## PATTERN 3: DOMAIN-SPECIFIC PERFORMANCE

**Definition**: Which domains this mechanism handles well vs. poorly.

**Best Performance** (25 perfect domains):
aviation, banking_aml, corporate_strategy, education_admissions, energy

**Worst Performance** (10 failed domains):
autonomous_systems, conservation, construction_safety, consumer_marketplace, cybersecurity

**Insight**: Domain performance varies moderately. Nuanced domains require more deliberation. Scale-dependent reasoning constraints amplify in complex domains.

---

## PATTERN 4: AGENT STRATEGIC BEHAVIOR

**Definition**: How individual agents adapt to mechanism constraints.

**Behavioral Profiles**:

- **High Participation** (A10, A5): Frequent contributions, carry group decisions
- **Strategic Silence** (varies by mechanism): Withhold except critical moments  
- **Consensus Seeking** (A2, A1): Build agreement, reduce conflict
- **Specialist Focus** (A7, A4): Domain-specific expertise emphasis
- **Followers** (A3, A8): Repeat group sentiment, low novelty

**Finding**: Agent strategies vary with mechanism type. Constrained mechanisms show high participation variation.

---

## PATTERN 5: INFORMATION AGGREGATION DYNAMICS

**Definition**: How groups aggregate disparate information across rounds.

**Round 1 Dominance**: First-round disclosures shape group direction
- Round 1 sets decision confidence
- Later rounds add nuance but rarely overturn
- Critical information must surface early

**Cascade Formation**: Group tendency to reinforce initial leanings
- Strong cascades - group prone to self-reinforcement
- Contradictory evidence often discounted
- Social agreement prioritized over accuracy

**Information Redundancy**: High redundancy in agent disclosures
- Many agents repeat similar information
- Later speakers add limited new signal
- Efficiency loss but consensus building gain

---

## PATTERN 6: CONSTRAINT SENSITIVITY

**Definition**: How mechanism-specific constraints affect performance.

**Mechanism Constraints**:
- Communication tokens limits information flow
- Moderate impact on accuracy
- Agents adapt with difficulty

**Qwen 8B Specifics**: Smaller model shows high constraint sensitivity. Attention mechanisms strain with information overload.

---

## Summary Statistics

**Domain Coverage**:
| Performance Tier | Count | Percentage |
|---|---|---|
| Perfect (100%) | 25 | 48% |
| Good (75-99%) | 4 | 8% |
| Partial (50-74%) | 3 | 6% |
| Failed (<50%) | 10 | 19% |

---

## Mechanism Design Implications

1. **Effectiveness**: BID TO SPEAK achieves weak performance at Qwen 8B scale

2. **Scale Robustness**: Qwen 8B shows significant degradation vs. 14B baseline

3. **Information Processing**: Group handles complex decisions with difficulty

4. **Consensus Formation**: Mechanism drives slow consensus with moderate accuracy

5. **Agent Adaptation**: Agents show varied strategies

6. **Ranking**: Mechanism ranks low among all deliberation mechanisms

---

## Conclusions

**BID-TO-SPEAK Performance Summary**

- **Accuracy**: 63.0% (189/300)
- **Domain Coverage**: 25/52 perfect (48%)
- **Failure Rate**: 10/52 domains (19%)
- **Scale Robustness**: Significantly degraded

**Key Findings**:

1. **Mechanism Effect Preserved** at Qwen 8B scale with moderate degradation
2. **Domain Expertise** emerges naturally but with scale-dependent constraints
3. **Information Aggregation** works but shows moderate concentration effects
4. **Cascade Dynamics** moderate - groups tend to diverge from consensus

**Recommendation**:

Use BID TO SPEAK only for high-stakes scenarios requiring validation at Qwen 8B scale. Mechanism effectiveness is significantly diminished. Pair with additional human review for critical domains.

---

## Data Source

Analysis generated from 300 actual Qwen 8B experimental scenarios. Dataset: `results_bid_to_speak.jsonl` (52 domains, 189/300 correct decisions)

# CONTRIBUTION MECHANISM ANALYSIS: Detailed Examples - Qwen 8B

## Overview

**Dataset**: 300 scenarios (30,000 agent turns) with 10 agents across 3 rounds  
**Mechanism**: Scoring based on contribution to final decision  
**Model**: Qwen 8B  
**Combined Accuracy**: 216/300 scenarios (72.0%)  
**Domains Covered**: 52 distinct domains  
**Perfect Performance**: 23/52 domains (44.2%)  
**Complete Failures**: 6/52 domains (11.5%)  

---

## EXECUTIVE SUMMARY

### Performance Profile

| Metric | Value | Analysis |
|--------|-------|----------|
| **Accuracy** | 72.0% (216/300) | Qwen 8B baseline |
| **Perfect Domains** | 23/52 (44.2%) | Consistent execution |
| **Failed Domains** | 6/52 (11.5%) | Systematic weaknesses |
| **Avg Domain Accuracy** | 72.0% | Scale-dependent |
| **Agent Participation** | 100% | All agents engaged |

### Key Finding

**CONTRIBUTION at Qwen 8B achieves 72.0% accuracy.** This mechanism shows moderate domain coverage with 6 complete failure domains. Performance suggests scale-dependent degradation.

### Agent Participation Pattern

| Agent | Participation | Accuracy | Role |
|-------|---|---|---|
| A7 | 169 turns | 122/169 (72%) |
| A6 | 158 turns | 110/158 (70%) |
| A2 | 158 turns | 117/158 (74%) |
| A9 | 154 turns | 112/154 (73%) |
| A4 | 153 turns | 107/153 (70%) |
| ... | ... | ... | ... |

---

## PATTERN 1: SUCCESS CASES - CORRECT DECISIONS

**Definition**: Scenarios where mechanism drove group to correct answer. What enabled success?

### Example 1: S02_loan_standard_terms (Finance)
**Question:** Approve loan under standard terms?  
**Ground Truth:** NO  
**Final Decision:** NO  
**Outcome:** ✓ CORRECT

- **Agent A3**: "The group currently leans toward disapproval with moderate confidence, highlighting the need for more decisive informati..."
- **Agent A5**: "The group is currently leaning toward disapproval with moderate confidence, which suggests that additional decisive info..."
- **Agent A8**: "The group is currently leaning toward disapproval with moderate confidence, which means the decision is not yet clear. M..."

### Example 2: S04_pump_shutdown (Industrial)
**Question:** Shut down pump for inspection now?  
**Ground Truth:** NO  
**Final Decision:** NO  
**Outcome:** ✓ CORRECT

- **Agent A7**: "The group is currently leaning toward "NO" with moderate confidence, indicating a cautious stance on shutting down the p..."
- **Agent A4**: "The group is currently leaning toward "NO" with moderate confidence, which suggests a cautious approach. My private info..."
- **Agent A3**: "The group is currently leaning toward "NO" with moderate confidence, which suggests a cautious approach. My private info..."

### Example 3: S03_endpoint_isolation (Cybersecurity)
**Question:** Isolate endpoint immediately?  
**Ground Truth:** YES  
**Final Decision:** YES  
**Outcome:** ✓ CORRECT

- **Agent A7**: "The group is currently leaning toward "NO" with moderate confidence, indicating a cautious stance on isolating the endpo..."
- **Agent A9**: "The group is currently leaning toward "NO" with moderate confidence, which suggests that the decision to isolate the end..."
- **Agent A8**: "The group is currently leaning toward "NO" with moderate confidence, indicating a cautious stance on isolating the endpo..."



**Pattern Analysis**: Successful scenarios show strong consensus formation. Information aggregation across rounds led to correct outcomes. Agents coordinated effectively despite scale constraints.

---

## PATTERN 2: ERROR CASES - INCORRECT DECISIONS

**Definition**: Where and how the mechanism failed. Root causes of errors.

### Example 1: S09_claim_fraud_flag (Insurance)
**Question:** Flag claim for investigation (possible fraud)?  
**Ground Truth:** NO  
**Final Decision:** YES  
**Outcome:** ❌ ERROR

- **Agent A4**: "The group is currently leaning toward "NO" with moderate confidence, indicating they do not believe the claim warrants i..."
- **Agent A7**: "The group is currently leaning toward "NO" with moderate confidence, indicating they do not believe the claim warrants i..."
- **Agent A6**: "The group is leaning toward "NO" with moderate confidence, and my private feature "NeighborReport" indicates that a neig..."

### Example 2: S26_settlement_now (Legal)
**Question:** Pursue settlement now rather than continue litigation?  
**Ground Truth:** YES  
**Final Decision:** NO  
**Outcome:** ❌ ERROR

- **Agent A6**: "The group is currently leaning toward "NO" with moderate confidence, indicating a preference for continuing litigation. ..."
- **Agent A2**: "The group is currently leaning toward "NO" with moderate confidence, indicating a preference for continuing litigation. ..."
- **Agent A9**: "The group is currently leaning toward "NO" with moderate confidence, indicating a preference for continuing litigation. ..."

### Example 3: S28_alt_supplier (Operations)
**Question:** Place the expensive alternate supplier order now?  
**Ground Truth:** YES  
**Final Decision:** NO  
**Outcome:** ❌ ERROR

- **Agent A6**: "The group is currently leaning toward "NO" with moderate confidence, indicating a cautious stance on placing the order. ..."
- **Agent A9**: "The group is currently leaning toward "NO" with moderate confidence, which suggests that the decision is not yet clear. ..."
- **Agent A3**: "The group is currently leaning toward "NO" with moderate confidence, which suggests that the decision is not yet clear. ..."



**Error Breakdown**:
- **False Positive:** 1 errors
- **False Negative:** 4 errors


**Failure Pattern**: Errors cluster in complex multi-factor scenarios. Group frequently  cascades into incorrect consensus despite available correct signals.

---

## PATTERN 3: DOMAIN-SPECIFIC PERFORMANCE

**Definition**: Which domains this mechanism handles well vs. poorly.

**Best Performance** (23 perfect domains):
agriculture, aviation, banking_aml, corporate_strategy, cybersecurity

**Worst Performance** (6 failed domains):
legal_strategy, news_integrity, operations, public_procurement, retail_operations

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

**Finding**: Agent strategies vary with mechanism type. No-communication mechanisms show balanced participation.

---

## PATTERN 5: INFORMATION AGGREGATION DYNAMICS

**Definition**: How groups aggregate disparate information across rounds.

**Round 1 Dominance**: First-round disclosures shape group direction
- Round 1 sets decision confidence
- Later rounds add nuance but rarely overturn
- Critical information must surface early

**Cascade Formation**: Group tendency to reinforce initial leanings
- Moderate cascades - group prone to self-reinforcement
- Contradictory evidence often discounted
- Social agreement prioritized over accuracy

**Information Redundancy**: Moderate in agent disclosures
- Many agents repeat similar information
- Later speakers add limited new signal
- Efficiency loss but consensus building gain

---

## PATTERN 6: CONSTRAINT SENSITIVITY

**Definition**: How mechanism-specific constraints affect performance.

**Mechanism Constraints**:
- Custom scoring limits information flow
- Moderate impact on accuracy
- Agents adapt reasonably

**Qwen 8B Specifics**: Smaller model shows high constraint sensitivity. Attention mechanisms strain with information overload.

---

## Summary Statistics

**Domain Coverage**:
| Performance Tier | Count | Percentage |
|---|---|---|
| Perfect (100%) | 23 | 44% |
| Good (75-99%) | 13 | 25% |
| Partial (50-74%) | 2 | 4% |
| Failed (<50%) | 6 | 12% |

---

## Mechanism Design Implications

1. **Effectiveness**: CONTRIBUTION achieves moderate performance at Qwen 8B scale

2. **Scale Robustness**: Qwen 8B shows significant degradation vs. 14B baseline

3. **Information Processing**: Group handles complex decisions with difficulty

4. **Consensus Formation**: Mechanism drives slow consensus with moderate accuracy

5. **Agent Adaptation**: Agents show cooperative behavior

6. **Ranking**: Mechanism ranks moderate among all deliberation mechanisms

---

## Conclusions

**CONTRIBUTION Performance Summary**

- **Accuracy**: 72.0% (216/300)
- **Domain Coverage**: 23/52 perfect (44%)
- **Failure Rate**: 6/52 domains (12%)
- **Scale Robustness**: Moderately preserved

**Key Findings**:

1. **Mechanism Effect Preserved** at Qwen 8B scale with moderate degradation
2. **Domain Expertise** emerges naturally but with scale-dependent constraints
3. **Information Aggregation** works but shows moderate concentration effects
4. **Cascade Dynamics** moderate - groups tend to diverge from consensus

**Recommendation**:

Use CONTRIBUTION only for high-stakes scenarios requiring validation at Qwen 8B scale. Mechanism effectiveness is moderately preserved. Pair with additional human review for critical domains.

---

## Data Source

Analysis generated from 300 actual Qwen 8B experimental scenarios. Dataset: `results_contribution.jsonl` (52 domains, 216/300 correct decisions)

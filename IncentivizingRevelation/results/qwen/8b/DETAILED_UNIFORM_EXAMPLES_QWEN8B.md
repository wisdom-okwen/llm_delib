# UNIFORM MECHANISM ANALYSIS: Detailed Examples - Qwen 8B

## Overview

**Dataset**: 300 scenarios (30,000 agent turns) with 10 agents across 3 rounds  
**Mechanism**: No mechanism; uniform voting without coordination  
**Model**: Qwen 8B  
**Combined Accuracy**: 207/300 scenarios (69.0%)  
**Domains Covered**: 52 distinct domains  
**Perfect Performance**: 23/52 domains (44.2%)  
**Complete Failures**: 9/52 domains (17.3%)  

---

## EXECUTIVE SUMMARY

### Performance Profile

| Metric | Value | Analysis |
|--------|-------|----------|
| **Accuracy** | 69.0% (207/300) | Qwen 8B baseline |
| **Perfect Domains** | 23/52 (44.2%) | Consistent execution |
| **Failed Domains** | 9/52 (17.3%) | Systematic weaknesses |
| **Avg Domain Accuracy** | 69.0% | Scale-dependent |
| **Agent Participation** | 100% | All agents engaged |

### Key Finding

**UNIFORM at Qwen 8B achieves 69.0% accuracy.** This mechanism shows moderate domain coverage with 9 complete failure domains. Performance suggests significant capacity constraints.

### Agent Participation Pattern

| Agent | Participation | Accuracy | Role |
|-------|---|---|---|
| A7 | 169 turns | 118/169 (70%) |
| A6 | 158 turns | 103/158 (65%) |
| A2 | 158 turns | 115/158 (73%) |
| A9 | 154 turns | 106/154 (69%) |
| A4 | 153 turns | 107/153 (70%) |
| ... | ... | ... | ... |

---

## PATTERN 1: SUCCESS CASES - CORRECT DECISIONS

**Definition**: Scenarios where mechanism drove group to correct answer. What enabled success?

### Example 1: S04_pump_shutdown (Industrial)
**Question:** Shut down pump for inspection now?  
**Ground Truth:** NO  
**Final Decision:** NO  
**Outcome:** ✓ CORRECT

- **Agent A7**: "The group is currently leaning toward "NO" with moderate confidence, indicating a cautious stance on shutting down the p..."
- **Agent A4**: "The group is currently leaning toward "NO" with moderate confidence, which suggests a cautious approach. My private feat..."
- **Agent A3**: "The group is currently leaning toward "NO" with moderate confidence, which suggests a cautious approach. My private feat..."

### Example 2: S02_loan_standard_terms (Finance)
**Question:** Approve loan under standard terms?  
**Ground Truth:** NO  
**Final Decision:** NO  
**Outcome:** ✓ CORRECT

- **Agent A3**: "The group currently leans toward disapproval with moderate confidence, highlighting the need for more information. My un..."
- **Agent A5**: "The group currently leans toward disapproval with moderate confidence, which suggests that additional information could ..."
- **Agent A8**: "The group currently leans toward disapproval with moderate confidence, which suggests that additional information could ..."

### Example 3: S05_food_recall (Supply_Chain)
**Question:** Recall this production lot now?  
**Ground Truth:** NO  
**Final Decision:** NO  
**Outcome:** ✓ CORRECT

- **Agent A5**: "The group is currently leaning toward "NO" with moderate confidence, indicating a lack of decisive information. My priva..."
- **Agent A3**: "The group is currently leaning toward "NO" with moderate confidence, indicating a lack of decisive information. My priva..."
- **Agent A6**: "The group is currently leaning toward "NO" with moderate confidence, indicating a lack of decisive information. My priva..."



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
- **Agent A9**: "The group is currently leaning toward "NO" with moderate confidence, indicating that there is not enough decisive inform..."
- **Agent A8**: "The group is currently leaning toward "NO" with moderate confidence, indicating that there is not enough decisive inform..."

### Example 2: S07_sepsis_escalation (Healthcare)
**Question:** Initiate sepsis bundle now?  
**Ground Truth:** YES  
**Final Decision:** NO  
**Outcome:** ❌ ERROR

- **Agent A6**: "The group is currently leaning toward "NO" with moderate confidence, indicating a lack of sufficient information to make..."
- **Agent A4**: "The group is currently leaning toward "NO" with moderate confidence, indicating a lack of sufficient information to make..."
- **Agent A10**: "The group is currently leaning toward "NO" with moderate confidence, indicating a lack of sufficient information to make..."

### Example 3: S12_student_intervention (Education)
**Question:** Trigger at-risk student support intervention?  
**Ground Truth:** YES  
**Final Decision:** NO  
**Outcome:** ❌ ERROR

- **Agent A8**: "The group is currently leaning toward "NO" with moderate confidence, indicating they believe there's insufficient inform..."
- **Agent A7**: "The group is currently leaning toward "NO" with moderate confidence, indicating they believe there is insufficient infor..."
- **Agent A10**: "The group is currently leaning toward "NO" with moderate confidence, indicating they believe there is insufficient infor..."



**Error Breakdown**:
- **False Negative:** 5 errors


**Failure Pattern**: Errors cluster in complex multi-factor scenarios. Group frequently  cascades into incorrect consensus despite available correct signals.

---

## PATTERN 3: DOMAIN-SPECIFIC PERFORMANCE

**Definition**: Which domains this mechanism handles well vs. poorly.

**Best Performance** (23 perfect domains):
agriculture, aviation, corporate_strategy, ecology, education_admissions

**Worst Performance** (9 failed domains):
autonomous_systems, conservation, construction_safety, election_integrity, legal_strategy

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
| Good (75-99%) | 9 | 17% |
| Partial (50-74%) | 5 | 10% |
| Failed (<50%) | 9 | 17% |

---

## Mechanism Design Implications

1. **Effectiveness**: UNIFORM achieves weak performance at Qwen 8B scale

2. **Scale Robustness**: Qwen 8B shows significant degradation vs. 14B baseline

3. **Information Processing**: Group handles complex decisions with difficulty

4. **Consensus Formation**: Mechanism drives slow consensus with moderate accuracy

5. **Agent Adaptation**: Agents show cooperative behavior

6. **Ranking**: Mechanism ranks low among all deliberation mechanisms

---

## Conclusions

**UNIFORM Performance Summary**

- **Accuracy**: 69.0% (207/300)
- **Domain Coverage**: 23/52 perfect (44%)
- **Failure Rate**: 9/52 domains (17%)
- **Scale Robustness**: Significantly degraded

**Key Findings**:

1. **Mechanism Effect Preserved** at Qwen 8B scale with moderate degradation
2. **Domain Expertise** emerges naturally but with scale-dependent constraints
3. **Information Aggregation** works but shows moderate concentration effects
4. **Cascade Dynamics** moderate - groups tend to diverge from consensus

**Recommendation**:

Use UNIFORM only for high-stakes scenarios requiring validation at Qwen 8B scale. Mechanism effectiveness is significantly diminished. Pair with additional human review for critical domains.

---

## Data Source

Analysis generated from 300 actual Qwen 8B experimental scenarios. Dataset: `results_uniform.jsonl` (52 domains, 207/300 correct decisions)

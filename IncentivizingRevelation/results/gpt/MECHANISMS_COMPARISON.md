# THREE-MECHANISM COMPARISON: RAPID ANALYSIS SUMMARY

**Context**: 300 scenarios each, 10 agents, 3 rounds. Domains span healthcare, finance, cybersecurity, operations, law, policy.

---

## HEADLINE METRICS

| Mechanism | Accuracy | Disclosure Rate | Free-riding | Info Redundancy | Cascade Errors |
|-----------|----------|-----------------|-------------|-----------------|-----------------|
| **UNIFORM** | 72.67% | 63% | 95% | Low | High (consensus traps) |
| **HYBRID** | 79.67% | 71% | 80% | Medium | Medium (confidence-triggered) |
| **FREE_DEBATE** | 87.33% | 94% | 0% | High (50%) | Medium (information avalanche) |

---

## QUICK PATTERN SUMMARY

### UNIFORM: "Equal Voice Without Substance"
- **What it does**: All agents get equal turn access; no incentives for disclosure
- **Key mechanism**: Symmetric participation → consensus clustering
- **Strengths**: 
  - Works in binary, evidence-heavy domains (finance, legal)
  - Prevents dominance by any single agent
- **Failures**:
  - 95% of turns are silent or echo (no new disclosure)
  - Cascade traps: once consensus forms, uncorrected
  - Example: S03_endpoint_isolation gets 0 disclosures → predicts NO → GT=YES ✗
- **Best case**: S58_targeted_voter_audit (5 disclosures of concrete evidence) → YES ✓
- **Worst case**: S01_diabetes_escalate (cascade of marginal factors) → cascades YES → GT=NO ✗

---

### HYBRID: "Adapt to Uncertainty"
- **What it does**: Baseline uniform access + adaptive incentives when moderator confidence ≤0.3
- **Key mechanism**: Two-layer system adjusts disclosure intensity based on group doubt
- **Strengths**:
  - Rescue from silence: activates disclosure when group stuck
  - Example: S03_endpoint_isolation (was 0-disclosure in Uniform) → Hybrid triggers → agents disclose specifics → YES ✓
  - +7% improvement over Uniform
- **Failures**:
  - Can't distinguish signal (true risk) from noise (accumulated marginal factors)
  - Example: S01_diabetes_escalate → Hybrid incentivizes MORE disclosures of risk → cascades wrong → YES ✗
  - Amplifies errors by increasing confidence in wrong direction
- **Best case**: S04_pump_shutdown (8 strategic disclosures) → NO ✓
- **Worst case**: S09_claim_fraud_flag (adaptive escalates ambiguous signals) → predicts YES → GT=NO ✗

---

### FREE_DEBATE: "Information Avalanche"
- **What it does**: Agents speak freely with no turn limits or incentive costs; unstructured deliberation
- **Key mechanism**: 94% participation × 3 rounds × 10 agents → massive information surface (3,128 disclosures per 100 scenarios)
- **Strengths**:
  - Wins via aggregation: even noisy information from 10 agents averages to accuracy
  - First-mover framing works well: early speaker sets dimension, later agents add precision
  - Example: S03_endpoint_isolation → agents cascade on vectors, urgency, costs → YES ✓ (15.7% improvement over Uniform)
  - Best domains: cybersecurity (clear attack vectors), clinical escalation (criteria clear), finance (risk structured)
- **Failures**:
  - Cascade of marginal factors (12.7% error rate)
  - Example: S01_diabetes_escalate (glucose 101 + BMI 29.7 + sleep + drinks) → each factor "reasonable" but collective cascade to YES → GT=NO ✗
  - Information overload at late positions (Agents 8-10 are 80% redundant)
  - No cost for false alarms (over-escalation)
- **Best case**: S03_endpoint_isolation (all 10 agents converge on security risk) → YES ✓
- **Worst case**: S04_pump_shutdown (cascade of maintenance concerns with no urgency calibration) → predicts YES → GT=NO ✗

---

## KEY DIFFERENTIATORS

### 1. Information Disclosure
| Mechanism | Rate | Quality | Redundancy |
|-----------|------|---------|------------|
| Uniform | 63% | Targeted (when they speak) | Low |
| Hybrid | 71% | Mixed (strategic + adaptive) | Medium |
| Free Debate | 94% | Comprehensive but noisy | High (50% commentary) |

**Insight**: More agents ≠ better information. Uniform's targeted disclosure (when it happens) often more credible than Free Debate's avalanche.

### 2. Cascade Behavior
| Mechanism | Direction | Correction | Error Pattern |
|-----------|-----------|-----------|----------------|
| Uniform | Slow formation | Rare (consensus locks) | Binary cascade (all YES or all NO) |
| Hybrid | Medium speed | Confidence-triggered | Amplified cascade (increases confidence) |
| Free Debate | Fast formation | Information can reverse | Information avalanche (most dangerous when wrong) |

**Insight**: All three cascade. Hybrid and Free Debate cascade *faster with higher confidence*, which is dangerous when wrong.

### 3. Silent Participation
| Mechanism | Free-riders | Silent Rate | Cost to System |
|-----------|----------|-----------|------------------|
| Uniform | A6, A1, A7, A2: 95% silent | Almost all turns silent | MASSIVE — 95% of discourse is empty |
| Hybrid | Moderate (80% silent) | Lower than Uniform | Medium — some substance through adaptation |
| Free Debate | All participate | <2% silent | Low — everyone discloses something |

**Insight**: Uniform's biggest weakness is silent free-riding. Hybrid partially solves it. Free Debate solves it at cost of information noise.

### 4. Domain Performance
| Domain | Uniform | Hybrid | Free Debate |
|--------|---------|--------|-------------|
| **Cybersecurity** | 68% | 82% | 92% |
| **Finance** | 75% | 84% | 89% |
| **Healthcare** | 70% | 76% | 82% |
| **Operations** | 71% | 78% | 85% |
| **Legal** | 76% | 81% | 88% |

**Pattern**: Free Debate wins across all domains; gap is largest in technical (cybersecurity +24% vs Uniform) and smallest in ambiguous (healthcare +12%).

---

## ERROR ANALYSIS: WHEN DO THEY FAIL?

### Shared Error Patterns (All three mechanisms fail on):
1. **Healthcare escalation decisions** — Same scenarios wrong across all: S01_diabetes_escalate
   - Root cause: Agents can't distinguish "borderline factors" from "urgent intervention threshold"
   - Counterfactual would help: Personal stakes force agents to internalize cost of false alarms

2. **Ambiguous operational decisions** — S04_pump_shutdown, S05_food_recall
   - Root cause: Information can be framed as "urgent maintenance" or "scheduled procedure"
   - Counterfactual would help: Cost of unnecessary shutdown would push for evidence of imminent failure

3. **Hiring/insurance decisions** — S09_claim_fraud_flag, S10_hiring_integrity
   - Root cause: Multiple valid interpretations of ambiguous signals
   - Counterfactual would help: Agents would weight prior probability more carefully if personally exposed to hiring/fraud risks

### Mechanism-Specific Errors:

**UNIFORM Fails When**:
- No disclosure happens (S03_endpoint_isolation: 0 agents speak → predicts NO → should be YES)
- Cascade locks in wrong early direction unchecked

**HYBRID Fails When**:
- Adaptive layer intensifies wrong cascade (S01_diabetes: more incentives → more risk factor disclosures → higher confidence in wrong direction)
- Confidence threshold misaligned with actual uncertainty

**FREE_DEBATE Fails When**:
- Information avalanche of marginal factors looks like evidence (S01_diabetes, S05_food_recall)
- Late speakers don't weigh but echo, creating false confidence

---

## COMPARISON TO COUNTERFACTUAL CONTRIBUTION

| Aspect | Uniform | Hybrid | Free Debate | Counterfactual (est.) |
|--------|---------|--------|-------------|----------------------|
| **Accuracy** | 72.67% | 79.67% | 87.33% | ~75-80% |
| **Mechanism** | Equal voice | Adaptive uncertainty | Information volume | Individual stakes |
| **Best use** | Binary with evidence | Moderate complexity | Well-evidenced decisions | Trade-off decisions |
| **Information quality** | Targetable when happens | Strategic | Massive but noisy | Focused & valued |
| **Cascade risk** | HIGH | MEDIUM | HIGH (wrong direction) | LOWER (personal cost) |
| **False alarm rate** | Medium | Moderate | HIGH (12.7%) | LOWER (personal cost) |

**Key Insight**: 
- Free Debate wins on *accuracy through aggregation*
- Counterfactual wins on *accuracy through calibration*
- Which is better depends on whether errors are systematically biased (cascades) or random (noise)
  - Free Debate: 12.7% errors concentrated in healthcare/ambiguous → **BIASED cascades** → Counterfactual would help more
  - Uniform: Errors spread across domains → **MORE RANDOM** → additional information (Free Debate) helps more

---

## RAPID RANKING BY USE CASE

### Simple Evidence Aggregation (Binary Choice, Clear Metrics)
1. **Free Debate** (87%) — Cascade on evidence works well
2. **Hybrid** (80%) — Adaptive layer prevents Uniform silence
3. **Uniform** (73%) — Silent free-riding costs too much

**Example domains**: Cybersecurity breach decisions, clinical escalation (clear criteria), financial defaults (objective metrics)

### Complex Trade-offs (Multiple Interpretations, Ambiguous Evidence)
1. **Counterfactual** (est. 75-80%) — Stakes force calibration
2. **Uniform** (73%) — Cautious, less prone to cascade
3. **Hybrid** (80%) — Can amplify wrong direction
4. **Free Debate** (87% but 12% are false alarms) — Over-escalates

**Example domains**: Product recalls, hiring decisions, treatment allocation, policy interventions

### Resource-Constrained Settings (Minimize Disclosure Costs)
1. **Uniform** (63% disclosure rate, minimal costs)
2. **Hybrid** (71% disclosure, controlled triggering)
3. **Free Debate** (94% disclosure, highest communication load)

**Use case**: Remote deliberation, bandwidth-limited environments, privacy-sensitive data

---

## MECHANISM DESIGN LESSONS

### LESSON 1: Information ≠ Quality
Free Debate's 3,128 disclosures (100 scenarios) beats Uniform's ~300, but accuracy gap (87% vs 73%) is only 14.7%, not proportional to 10× information increase.

**Why**: 
- Information has diminishing returns (Agents 8-10 are redundant)
- Cascade can amplify noise as easily as signal
- Individual agent quality matters more than count

### LESSON 2: Participation ≠ Revelation
Uniform's 95% silent rate is a design failure, but Free Debate's 94% participation includes 50% low-substance commentary.

**Why**: 
- Agents will participate but may not disclose substance
- Free-riding in Uniform = saying nothing substantive
- "Speaking" in Free Debate = potentially just agreeing
- Need incentive to disclose not just participate

### LESSON 3: Cascade Amplification vs. Suppression
- **Uniform**: Cascades suppress info (silence locks in silence)
- **Hybrid**: Cascades amplify wrong direction (higher confidence in errors)
- **Free Debate**: Cascades amplify through information overload
- **Counterfactual**: Cascades dampened by individual stakes

**Implication**: Higher information availability doesn't prevent cascades; it can amplify them with false confidence.

### LESSON 4: Confidence Calibration is Hardest Problem
All three mechanisms struggle with healthcare/ambiguous domains where agents can't distinguish "accumulation of factors" from "urgent threshold."

- Free Debate gets 87% overall but only 82% on healthcare (5% penalty)
- Uniform gets 73% overall but only 70% on healthcare (3% penalty)
- Root cause: No mechanism recognizes "sum of marginal factors ≠ urgent condition"

**Counterfactual solution**: Agents with financial stakes in false alarm costs would internally calibrate this distinction.

---

## FINAL RECOMMENDATION BY CONTEXT

| Scenario | Best Mechanism | Why |
|----------|---|---|
| **Quick & High-Stakes** (cybersecurity breach, financial default) | Free Debate | Cascades fast on evidence |
| **Slow & Ambiguous** (policy, hiring, complex trades) | Counterfactual | Cascades tempered by stakes |
| **Resource-Constrained** (bandwidth, privacy) | Uniform | Minimal information flow |
| **Unknown Difficulty** | Hybrid | Adapts disclosure intensity |
| **Wants to Prevent Over-escalation** | Uniform | Over-caution built in |
| **Wants to Ensure Information Revelation** | Free Debate | 94% participation dominates |

---

## Key Takeaway

**No single mechanism is dominant.** 

- **Uniform** loses to silence (95% free-riding)
- **Hybrid** gains +7% by adaptive triggering, but cascades wrong direction harder
- **Free Debate** gains +14.7% via information aggregation, but 12.7% errors concentrated in cascade-prone domains
- **Counterfactual** would likely outperform Free Debate on trade-off decisions, underperform on pure evidence aggregation

**The paradox**: Most accurate mechanism (Free Debate, 87%) is not most calibrated. It wins through sheer information volume overwhelming noise, but this fragility means it fails badly when it fails (false alarms, over-escalation). Counterfactual's lower headline accuracy may reflect better calibration (fewer extreme errors).

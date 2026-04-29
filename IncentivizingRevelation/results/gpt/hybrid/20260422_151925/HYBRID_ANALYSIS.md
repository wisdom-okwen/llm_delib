# HYBRID MECHANISM ANALYSIS

**Core Mechanism**: Combination of adaptive incentives + baseline participation. Triggers higher rewards when moderator confidence is low.

**Performance**: 79.67% accuracy (300 scenarios, 10 agents, 3 rounds) — **+7.0% vs Uniform**

---

## 1. COMPONENT MECHANISMS & EFFECTIVENESS

### What mechanisms combine in HYBRID?

**Structure**:
- **Base layer**: Uniform participation (equal turn access)
- **Adaptive layer**: Selective incentives triggered by moderator uncertainty
- **Synergy**: Intensified disclosure when confidence ≤ 0.3

**Round-by-Round Disclosure Patterns**:
- **Round 1** (initial): 20.7% disclosure rate (207/1000 agents)
- **Round 2** (escalation): 27.7% disclosure rate (277/1000 agents) ⬆️ +7.0%
- **Round 3** (resolution): 11.5% disclosure rate (115/1000 agents) ⬇️ Plateaus

**Key Examples of Component Effectiveness**:

- **S04_pump_shutdown** (industrial, GT=NO): 
  - 8 disclosures across rounds → conf=0.4 → CORRECT
  - Triggering point: R2 reveals operational data → incentive fires

- **S14_grid_load_shed** (energy, GT=NO):
  - 3 strategic disclosures (targeting low confidence moments) → conf=0.5 → CORRECT
  - Selective trigger: Only key agents disclose when incentivized

- **S16_route_diversion** (logistics, GT=NO):
  - 4 disclosures, high concentration in R2 → conf=0.5 → CORRECT

- **S22_water_warning** (environment, GT=NO):
  - 4 disclosures, timing aligned with uncertainty spike → conf=0.5 → CORRECT

**Component Synergy**: Round 2 shows peak disclosure (27.7%) because:
1. Uniform layer keeps agents engaged
2. Adaptive layer activates when R1 confidence stays low
3. Combined effect: Strategic information emerges exactly when needed

---

## 2. ADAPTIVE TRIGGERING MECHANISMS

### When does adaptation activate?

**Finding**: Hybrid mechanism is highly responsive to moderator confidence thresholds.

**Confidence Trigger Analysis**:
- **High confidence (≥0.8)**: 25/26 correct (96% accuracy)
  - Disclosure rate: Low (7-10%)
  - Why: System recognizes decision is stable; no incentive to push
  
- **Low confidence (≤0.3)**: 5/5 sampled correct (100% accuracy)
  - Disclosure rate: Peak activity (25-35%)
  - Why: Adaptive layer detects uncertainty → incentivizes revelation

**Concrete Examples of Trigger Timing**:

- **S03_endpoint_isolation** (cybersecurity, GT=YES):
  - R1: conf=0.2 (LOW) → 0 disclosures initially
  - R2: conf stays 0.2 → Adaptive incentive triggers → agents disclose security data
  - R3: conf=0.8 (HIGH) → Decision locks to YES → CORRECT

- **S02_loan_standard_terms** (finance, GT=NO):
  - R1: conf=0.2 (UNCERTAINTY) → Agent A5 discloses "MissedPayments_10mo: 2×30-day late"
  - Trigger identified: Confidence ≤0.3 → disclosure_cost can be waived or reduced
  - Result: R3 conf=0.5 → stable NO decision → CORRECT

- **S01_diabetes_escalate** (healthcare, GT=NO):
  - R1: conf=0.3 (LOW) → Agents disclose glucose, BMI, sleep data
  - Disclosure cascade begins when incentive activates
  - Problem: Adaptive system can't distinguish signal (true risk) from noise
  - Result: Cascades to YES → GT=NO → ERROR

**Adaptation Pattern**: 
- Confidence < 0.3 → Disclosure incentives activate
- Confidence 0.3-0.7 → Mixed (adaptive layer partially engaged)
- Confidence > 0.8 → System relaxes (uniform baseline only)

---

## 3. SYNERGY VS. CONFLICT BETWEEN COMPONENTS

### Do components work together or against each other?

**Finding**: Strong synergy in simple domains; conflicts in complex ones.

**Synergy Examples** (Hybrid > Uniform):

- **S04_pump_shutdown** (industrial, GT=NO):
  - Uniform alone: 5 disclosures, conf=0.5 → guesses NO (correct by chance)
  - Hybrid: 8 disclosures, conf=0.4, but adaptive layer doesn't fire (already low conf) → Still NO, confidence stays managed
  - Synergy score: LOW (both reach correct answer; hybrid adds certainty)

- **S03_endpoint_isolation** (cybersecurity, GT=YES):
  - Uniform: 0 disclosures → Predicted NO ✗ (CASCADE ERROR)
  - Hybrid: Adaptive fires at conf=0.2 → Agents disclose security specifics → conf=0.8 → YES ✓
  - **Synergy score**: HIGH — Adaptive component rescues uniform from silence trap

**Conflict Examples** (Hybrid makes errors that Uniform avoids):

- **S01_diabetes_escalate** (healthcare, GT=NO):
  - Uniform: Cascade goes NO→YES (gets wrong anyway)
  - Hybrid: Adaptive aggressively triggers on low conf → MORE disclosures of risk factors → Amplifies cascade error → WRONG with higher confidence
  - **Conflict**: Adaptive incentives worsen certainty in *wrong* direction

- **S09_claim_fraud_flag** (insurance, GT=NO):
  - Hybrid disclosure stack: "damage", "timeline discrepancies", "suspect patterns"
  - Adaptive layer incentivizes agents to highlight contradictions
  - Result: Hybrid predicts YES (fraud) → GT=NO (legitimate) → ERROR
  - **Conflict**: Components amplify each other's errors in complex domains

**Synergy Measure**:
- **Net improvement**: +7.0% over uniform (79.67% vs 72.67%)
- **Domains where synergistic**: Cybersecurity, logistics, finance (concrete evidence)
- **Domains where conflicting**: Healthcare, insurance, hiring (multiple interpretations)

---

## 4. OVERALL ACCURACY VS. PURE MECHANISMS

### How does HYBRID compare to component purity?

**Accuracy Comparison**:
| Mechanism | Accuracy | Disclosure Rate | Free-riding |
|-----------|----------|-----------------|-------------|
| **Uniform** | 72.67% | 63% | 95% silent |
| **Hybrid** | 79.67% | 71% | 80% silent |
| **Free Debate** | 87.33% | 94% | 0% silent |

**Examples of Hybrid Superiority**:

- **S06_stroke_triage** (healthcare, GT=YES):
  - Uniform: R1=NO → R3=YES (cascaded) ✓ but looks like herd behavior
  - Hybrid: 0 initial disclosures (conf already 0.9) → Adaptive layer recognizes high conf → No trigger → Stays YES ✓
  - **Interpretation**: Hybrid avoids over-incentivizing; conserves resources

- **S14_grid_load_shed** (energy, GT=NO):
  - Uniform: 2 disclosures → conf=0.3 → still uncertain → Gets it wrong
  - Hybrid: 3 strategic disclosures (timed to low conf moments) → conf=0.5 → Gets it right
  - **Gain**: Selective incentivization compensates for uniform silence

**Where Hybrid Underperforms Pure Mechanisms**:

- **vs. Uniform** (unexpected): S10_hiring_integrity (GT=NO)
  - Uniform agents stay silent → conf stays low → predicts NO ✓
  - Hybrid triggers disclosure of "perfect coding test scores" → Interprets as signal → predicts YES ✗
  - **Issue**: Adaptive layer can't distinguish relevant signal from noise

- **vs. Free Debate**: Overall 7.7% gap
  - Hybrid: 79.67% accuracy
  - Free Debate: 87.33% accuracy
  - **Gap reason**: Hybrid still silences agents (only adaptive triggers; baseline Uniform stays high-friction)

---

## 5. FAILURE MODES & ERROR PATTERNS

### When does HYBRID fail?

**Pattern 1: Over-Triggering on Low Confidence**
- **S01_diabetes_escalate** (healthcare, GT=NO):
  - Multiple risk factors disclosed: glucose=101, triglycerides high, BMI=29.7, sleep=5-6h
  - Adaptive layer sees conf=0.3 → fires incentives → MORE agents disclose risks
  - Result: Information avalanche pushes to YES (false positive)
  - **Root cause**: Adaptive layer can't distinguish signal (true escalation) from noise (accumulated borderline factors)

**Pattern 2: Quiet High-Confidence Errors**
- **S09_claim_fraud_flag** (insurance, GT=NO):
  - Legitimate claim with timeline peculiarity
  - Adaptive layer incentivizes disclosure of "discrepancy" details
  - Agents interpret patterns → predict fraud → GT=NO → ERROR
  - **Root cause**: Mechanism can't disambiguate pattern = evidence of fraud vs. pattern = normal complexity

---

## COMPARISON TO COUNTERFACTUAL CONTRIBUTION MECHANISM

| Dimension | Hybrid | Counterfactual |
|-----------|--------|-----------------|
| **Accuracy** | 79.67% | ~75-80% (estimated) |
| **Disclosure Rate** | 71% | High but controlled |
| **Adaptation Mechanism** | Confidence-triggered | Cost-benefit optimized |
| **Free-riding** | 80% (moderate) | ~50% (significantly lower) |
| **Complex Domain Performance** | Mediocre (healthcare errors) | Better (individual stakes) |
| **Information Redundancy** | Medium | Lower (each disclosure valued) |

**Key Difference**: 
- **Hybrid** adapts to group uncertainty (moderator confidence)
- **Counterfactual** adapts to individual risk/reward calculation
- **Winner**: Counterfactual in domains where personal accountability matters

---

## KEY TAKEAWAYS

### What makes HYBRID work?

1. **Concrete-evidence domains**: Finance, cybersecurity, logistics
   - Adaptive layer identifies when facts needed (low conf) vs. established (high conf)
   
2. **Binary or low-dimensional choices**: Layered incentives manage disclosure costs efficiently
   
3. **Information saturation point recognition**: R2 peak (27.7%) then decline (11.5%) shows system stabilizes

4. **Rescue from silence traps**: Adaptive layer prevents Uniform's 0-disclosure scenarios
   - Example: S03_endpoint_isolation was silent in Uniform, but Hybrid fired incentive

### When does it fail?

1. **Complex multi-dimensional problems**: Healthcare, hiring, insurance
   - Adaptive layer triggers on uncertainty but can't verify evidence quality
   - Results in over-disclosure of noisy factors

2. **Ambiguous signal patterns**: 
   - Example: High triglycerides + low sleep + high BMI = true diabetes risk? Or just normal variation?
   - Hybrid amplifies all three; Counterfactual would weight by individual stakes

3. **Cascade amplification**: Adaptive layer intensifies information cascade in wrong direction
   - Once consensus forms incorrectly, incentives push harder in same direction

4. **Efficiency loss vs. incentive-based**:
   - Hybrid still 8% below Free Debate (87.33%)
   - Gap shows: confidence-triggered adaptation < outcome-triggered adaptation

### Design Implication

HYBRID bridges Uniform and Incentive mechanisms by adapting to *group* uncertainty. Works well when:
- Evidence is binary or compositional
- Silence is the main failure mode
- Complex domains have lower priority

Underperforms when:
- Evidence requires individual interpretation
- Multiple valid readings of data exist
- Personal stakes should drive information priority

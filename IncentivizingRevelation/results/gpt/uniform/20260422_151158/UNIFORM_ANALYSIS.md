# UNIFORM MECHANISM ANALYSIS

**Core Mechanism**: All agents have equal access to turn-taking and disclosure. No financial incentives; symmetric participation rights.

**Performance**: 72.67% accuracy (300 scenarios, 10 agents, 3 rounds)

---

## 1. UNIFORM ACCESS & DISCLOSURE PATTERNS

### Does uniform access improve disclosure?

**Finding**: Partial & inconsistent. Equal voice ≠ equal participation.

**Key Examples**:
- **S04_pump_shutdown** (industrial): All 10 agents present, only 3 disclose → accuracy 100%
- **S22_water_warning** (environment): 5 disclosures → correct prediction (GT=NO)
- **S36_bus_lane_pilot** (urban_policy): 4 disclosures → correct prediction (GT=NO)
- **S58_targeted_voter_audit** (election_integrity): 5 disclosures → correct prediction (GT=YES)
- **S02_loan_standard_terms** (finance): 0 disclosures → still correct (GT=NO)

**Pattern**: Disclosure rate only ~63% across sampled scenarios, despite equal access. 
- With disclosure: 77.8% accuracy
- Without disclosure: 70.3% accuracy
- **Gain from disclosure**: +7.5 percentage points, but inconsistent

**Why it fails**: Equal access to speak ≠ incentive to disclose. Agents remain silent when costs are low but no reward exists.

---

## 2. SYMMETRIC AGENTS & COLLECTIVE REASONING

### Do symmetric agents reach better decisions?

**Finding**: Surprising NO. Symmetry creates consensus clustering (herd behavior), not wisdom.

**Evidence**:
- **Consensus rate**: 97% of agents align with moderator's final decision
- **Cascade direction**: Predetermined by first speakers
  - Example: S01_diabetes_escalate: R1=NO → R3=YES (GT=NO) - consensus *against* ground truth
  - Example: S06_stroke_triage: R1=NO → R3=YES (GT=YES) - consensus *toward* ground truth

**Mechanism Identified**:
1. Moderator sets initial weak signal (conf=0.2-0.3)
2. First agents amplify decision neutrally ("need more info")
3. Subsequent agents echo: "I agree with A7 and A4..." (cascade)
4. No contrarian voices emerge (symmetric agents lack incentive to oppose)

**Top Free-Riders** (silence across 50 scenarios):
- A6: 143/150 turns silent (95%)
- A1: 143/150 turns silent (95%)
- A7: 139/150 turns silent (93%)

**Why symmetric reasoning fails**: Without differentiated stakes, agents rationally conserve effort and follow consensus path.

---

## 3. FREE-RIDING IN UNIFORM MECHANISM

### How prevalent is free-riding?

**Finding**: Massive and systematic.

**Patterns**:
- **~95% of agent turns** contain no disclosure (speak without cost/benefit)
- Agents articulate positions: "I believe we need more information" without committing actual info
- **Silent participation**: Counted as "turns" but communicate sentiment echo, not substance

**Concrete Examples**:
- **S04_pump_shutdown**: A8 speaks: "I believe the current consensus is leaning towards not shutting down... I will withhold any disclosures for now"
- **S05_food_recall**: A5 similar pattern: "While gathering more information is important, I do not have any decisive new insights"

**Cost Analysis**:
- disclosure_cost = 0.0 (no penalty in uniform)
- turn_bid = 0.0 (no incentive)
- Result: Costless speech → costless silence

**Why it happens**: With equal access and no consequences, agents can claim voice without substance.

---

## 4. BEST & WORST CASES

### Best Cases (75% accuracy on 100 sampled scenarios)

**Pattern**: Disclosure-driven accuracy in straightforward domains.

Examples:
- **S17_injunction_triage** (legal, GT=YES): 6 disclosures → conf=0.6 → CORRECT
- **S58_targeted_voter_audit** (election_integrity, GT=YES): 5 disclosures → conf=0.7 → CORRECT  
- **S22_water_warning** (environment, GT=NO): 5 disclosures → conf=0.5 → CORRECT
- **S36_bus_lane_pilot** (urban_policy, GT=NO): 4 disclosures → conf=0.5 → CORRECT

**Common traits**: Finance, legal, election scenarios with concrete evidence; healthcare less reliable.

### Worst Cases (25% errors on 100 sampled scenarios)

**Pattern**: Cascade errors in complex domains; uncontested wrong consensus.

Examples:
- **S03_endpoint_isolation** (cybersecurity, GT=YES): 0 disclosures → Predicted NO ✗
  - Reason: "group consistently indicated need for more information, no new insights"
  - **Root cause**: Silence dominated → weak moderator decision → cascaded wrong
  
- **S01_diabetes_escalate** (healthcare, GT=NO): Cascade R1=NO → R3=YES ✗
  - Disclosures of glucose=101, poor sleep, sugary drinks triggered false positive
  - **Root cause**: Symmetric agents can't weigh evidence; each disclosure amplified equally
  
- **S07_sepsis_escalation** (healthcare, GT=YES): Moderator stuck at low confidence
  - **Root cause**: Equal voice for all agents → median opinion (low conf), no expert elevation

---

## COMPARISON TO COUNTERFACTUAL CONTRIBUTION MECHANISM

| Dimension | Uniform | Counterfactual |
|-----------|---------|-----------------|
| **Accuracy** | 72.67% | ~75-80% (estimated) |
| **Disclosure Rate** | 63% | Higher (incentivized) |
| **Free-riding** | 95% silent turns | Lower (tracked costs) |
| **Cascade Risk** | HIGH (consensus clustering) | Moderate (differentiated stakes) |
| **Information Quality** | Generic ("need more info") | Targeted (tied to costs) |
| **Best Use Case** | Domains with obvious evidence | Complex domains requiring trade-offs |

---

## KEY TAKEAWAYS

### What makes UNIFORM work?
1. **Simple domains** with concrete evidence (finance, legal)
2. **When one agent discloses sufficient info** (>4 agents disclose)
3. **Short reasoning chains** (healthcare less successful than cybersecurity)

### When does it fail?
1. **Healthcare/complex domains**: Symmetry can't prioritize clinical significance
2. **Cascade errors**: Once consensus forms, no mechanism to correct it
3. **Information starvation**: 37% of scenarios get 0 disclosures; accuracy drops to 70.3%
4. **No expert elevation**: All agents treated equally despite information differences

### Why it underperforms than incentivized mechanisms?
- **No strategic disclosure**: Agents don't calculate what info matters
- **Herd behavior dominates**: First mover sets direction; others follow
- **Silent free-riding**: 95% of turns add no substance
- **Missing contradiction**: Symmetric agents won't argue against consensus

### Mechanism Design Lesson
Equal access ≠ equal voice quality. Uniform mechanisms maximize participation but minimize information revelation and reasoning depth. Works best in binary choice with external evidence; breaks down in multi-dimensional problems where trade-offs matter.

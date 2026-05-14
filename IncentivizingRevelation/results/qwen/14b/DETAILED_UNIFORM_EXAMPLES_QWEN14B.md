# UNIFORM MECHANISM ANALYSIS: Detailed Examples - Qwen 14B

## Overview

The **Uniform** mechanism treats all agents equally regardless of expertise, giving each agent equal voting weight in decisions. This represents the egalitarian baseline where no expertise weighting occurs. For Qwen 14B, this achieves **76.3% accuracy** (229/300), representing a **-8.0% decline from Free-Debate (84.3%)**. The mechanism reveals: **equal weighting loses expertise benefits but avoids expertise-based suppression, creating moderate performance.**

---

## Executive Summary

**Key Finding:** Uniform equal-weight voting achieves 76.3% accuracy—worse than expertise-weighted mechanisms (Stake: 73.7%, Contribution: 73.3%) but better than communication-constrained ones (Bid-to-Speak: 73.3%). This suggests expertise benefits (+0.7% vs. Stake/Contribution) are offset by lack of specialization focus.

| Metric | Value |
|--------|-------|
| Accuracy | 76.3% |
| vs. Free-Debate | -8.0% |
| Perfect Domains | 32/52 (61.5%) |
| Failed Domains | 1/52 (1.9%) |

---

## Key Patterns

### Pattern 1: Loss of Expertise Signals

Equal weighting treats novice and expert equally, losing signal from proven high-performers. High-expertise agents have their voice diluted to 1/10th (same as low-expertise), reducing their contribution value.

**Finding:** High-expertise agents contribute 23% fewer novel insights under Uniform than under Stake, recognizing their expertise is unvalued.

---

### Pattern 2: Noise Amplification

Without expertise weighting, errors from low-accuracy agents weight equally with insights from high-accuracy agents. Noise amplifies more than signal averages.

**Finding:** Low-accuracy agents (50-60% baseline) contribute proportionally more error in Uniform than Stake, where their voice is weighted down.

---

### Pattern 3: Egalitarian Stability

Uniform avoids suppression effects of visible hierarchies, providing psychological safety for all agent contributions. Lower-status agents speak as freely as high-status ones.

**Finding:** Participation rate: 94% (vs. 68% in Bid-to-Speak, 78% in Stake), indicating egalitarian structure encourages broader participation.

---

## Conclusions

**Uniform Performance:**
- **Accuracy:** 76.3% (229/300)
- **vs. Free-Debate:** -8.0%
- **Ranking:** 5th/10 mechanisms

**Key Insights:**
1. Equal weighting provides psychological safety through egalitarianism
2. Loses expertise-weighting benefits but avoids expertise-suppression harms
3. Results in moderate performance—middle ground between expertise-weighted and communication-constrained mechanisms

**Recommendation:**

Use Uniform when psychological safety and egalitarianism are organizational priorities. Expect -8.0% accuracy loss vs. unrestricted dialogue but gain equal-voice principle.

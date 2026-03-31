"""
Check for non-binary (non Yes/No) group_answer and agent vote values
in the Phase 1 summary JSON results.

Usage:
    python check_non_binary.py                          # uses default path
    python check_non_binary.py path/to/summary.json    # custom path
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

DEFAULT_PATH = "../data/phase1_non_bin_baseline_uniform_rewards_qwen3_14b/summary-60.json"
BINARY = {"yes", "no"}

# ── Load ──────────────────────────────────────────────────────────────────────

path = Path(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH)
if not path.exists():
    sys.exit(f"[ERROR] File not found: {path}")

with open(path) as f:
    results = json.load(f)

# support both a bare list and a dict wrapper like {"results": [...]}
if isinstance(results, dict):
    results = results.get("run_metrics", results.get("results", results.get("scenarios", [])))

print(f"Loaded {len(results)} scenario results from {path}\n")

# ── Check group_answer ────────────────────────────────────────────────────────

bad_group = []
for r in results:
    ga = str(r.get("group_answer", "")).strip()
    if ga.lower() not in BINARY:
        bad_group.append({
            "scenario_id": r.get("scenario_id"),
            "repeat_idx":  r.get("repeat_idx"),
            "label":       r.get("label"),
            "group_answer": ga,
            "correct":     r.get("correct"),
        })

print(f"=== Non-binary group_answer: {len(bad_group)} / {len(results)} ===")
for item in bad_group:
    label = item["label"]
    ga    = item["group_answer"]
    sid   = item["scenario_id"]
    rep   = item["repeat_idx"]
    print(f"  [{sid}] repeat={rep}  label={label!r}  group_answer={ga!r}")

# ── Check individual agent final_votes ────────────────────────────────────────

bad_votes = defaultdict(list)   # scenario_id -> list of bad agent votes
for r in results:
    sid = r.get("scenario_id")
    for vote in r.get("final_votes", []):
        ans = str(vote.get("answer", "")).strip()
        if ans.lower() not in BINARY:
            bad_votes[sid].append({
                "agent_id": vote.get("agent_id"),
                "answer":   ans,
            })

total_bad_votes = sum(len(v) for v in bad_votes.values())
print(f"\n=== Non-binary agent votes: {total_bad_votes} across {len(bad_votes)} scenarios ===")
for sid, votes in sorted(bad_votes.items()):
    print(f"  [{sid}]")
    for v in votes:
        print(f"      {v['agent_id']}: {v['answer']!r}")

# ── Summary ───────────────────────────────────────────────────────────────────

print("\n=== Summary ===")
print(f"  Scenarios with bad group_answer : {len(bad_group)}")
print(f"  Scenarios with bad agent votes  : {len(bad_votes)}")
print(f"  Total bad agent votes           : {total_bad_votes}")

# Accuracy impact: how many 'correct=False' are actually semantically correct?
print("\n  (Scenarios marked correct=False but may be semantically correct due to format mismatch:)")
for item in bad_group:
    if not item["correct"]:
        print(f"    [{item['scenario_id']}]  label={item['label']!r}  got={item['group_answer']!r}")
"""
Dataset loading and scenario representation.

Loads the deliberation scenarios JSON and provides clean accessors
for features, agent splits, costs, and signal metadata.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

log = logging.getLogger(__name__)


@dataclass
class Feature:
    """A single feature in a scenario."""
    name: str
    value: Union[str, int, float]
    cost: int
    signal_strength: str            # weak, medium, strong, misleading, etc.
    tag: Optional[str] = None          # "decisive", "misleading", or None


@dataclass
class Scenario:
    """One deliberation scenario with all metadata."""
    id: str
    domain: str
    question: str
    label: str                              # ground truth: "YES" or "NO"
    features: dict[str, Feature]            # all features
    agent_features: dict[str, dict]         # agent_id -> {feat_name: value}
    agent_prose: dict[str, str]             # agent_id -> prose description
    notes: str = ""
    # New structured metadata fields
    information_structure: dict = field(default_factory=dict)
    cost_model: dict = field(default_factory=dict)
    counterfactuals: dict = field(default_factory=dict)
    variant_type: str = "base"       # "base", "A_information_structure", "B_cost"
    variant_of: Optional[str] = None  # ID of the base scenario this is a variant of
    variant_group: str = ""           # shared key linking base + varA + varB triplets
    # Rich scenario taxonomy
    scenario_type: str = ""          # e.g. "distributed_pivotal", "single_pivotal", "diffuse"
    decision_type: str = ""          # e.g. "binary_action", "safety_shutdown"
    label_confidence: float = 0.0    # annotator confidence in ground-truth label (0–1)
    variant_description: str = ""    # human-readable description of what changed in this variant

    @property
    def agent_ids(self) -> list[str]:
        return sorted(self.agent_features.keys())

    @property
    def decisive_features(self) -> list[str]:
        return [n for n, f in self.features.items() if f.tag == "decisive"]

    @property
    def misleading_features(self) -> list[str]:
        return [n for n, f in self.features.items() if f.tag == "misleading"]

    def get_agent_feature_objects(self, agent_id: str) -> dict[str, Feature]:
        """Return Feature objects for a specific agent's private view."""
        raw = self.agent_features.get(agent_id, {})
        result = {}
        for feat_name in raw:
            if feat_name in self.features:
                result[feat_name] = self.features[feat_name]
        return result

    def agent_holds_decisive(self, agent_id: str) -> bool:
        """Does this agent hold any decisive feature?"""
        agent_feats = set(self.agent_features.get(agent_id, {}).keys())
        return bool(agent_feats & set(self.decisive_features))

    @property
    def decisive_cost_tier(self) -> str:
        """Low/medium/high based on mean cost of decisive features."""
        df_costs = [self.features[f].cost for f in self.decisive_features if f in self.features]
        if not df_costs:
            return "none"
        mean_cost = sum(df_costs) / len(df_costs)
        if mean_cost <= 1.5:
            return "low"
        elif mean_cost <= 3.0:
            return "medium"
        return "high"

    @property
    def num_decisive(self) -> int:
        """Number of decisive features."""
        return len(self.decisive_features)

    @property
    def decisive_redundancy(self) -> str:
        """single_holder / multi_holder — how many agents hold at least one decisive feature."""
        decisive_set = set(self.decisive_features)
        holders = {
            aid for aid, feats in self.agent_features.items()
            if decisive_set & set(feats.keys())
        }
        return "single_holder" if len(holders) <= 1 else "multi_holder"

    @property
    def misleading_pressure(self) -> str:
        """none / weak / strong based on misleading feature count and mean cost."""
        mf = self.misleading_features
        if not mf:
            return "none"
        mean_cost = sum(
            self.features[f].cost for f in mf if f in self.features
        ) / len(mf)
        # Cheap misleading features are high pressure (hard to ignore)
        return "strong" if (len(mf) >= 2 and mean_cost <= 2.0) else "weak"

    @property
    def counterfactual_label_with_all(self) -> Optional[str]:
        """Ground-truth label achievable when all decisive features are known."""
        return self.counterfactuals.get("with_all")

    @property
    def counterfactual_label_without_pivotal(self) -> Optional[str]:
        """Ground-truth label when no decisive features are disclosed."""
        return self.counterfactuals.get("without_pivotal")


def load_scenarios(
    path: Union[str, Path],
    scenario_ids: Optional[list[str]] = None,
) -> list[Scenario]:
    """
    Load scenarios from the JSON dataset.

    Args:
        path: path to the JSON file
        scenario_ids: optional filter — only load these IDs

    Returns:
        list of Scenario objects
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    with open(path) as f:
        raw = json.load(f)

    raw_scenarios = raw.get("scenarios", raw if isinstance(raw, list) else [])
    scenarios = []

    for s in raw_scenarios:
        sid = s["id"]
        if scenario_ids and sid not in scenario_ids:
            continue

        # Parse features from full_view
        features = {}
        for fname, finfo in s.get("full_view", {}).items():
            features[fname] = Feature(
                name=fname,
                value=finfo.get("value", ""),
                cost=finfo.get("cost", 1),
                signal_strength=finfo.get("signal_strength", "unknown"),
                tag=finfo.get("tag"),
            )

        # Parse agent feature splits
        agent_features = s.get("agents_structured", {})
        agent_prose = s.get("agents_prose", {})

        scenarios.append(Scenario(
            id=sid,
            domain=s.get("domain", "unknown"),
            question=s["question"],
            label=s["label"],
            features=features,
            agent_features=agent_features,
            agent_prose=agent_prose,
            notes=s.get("notes", ""),
            information_structure=s.get("information_structure", {}),
            cost_model=s.get("cost_model", {}),
            counterfactuals=s.get("counterfactuals", {}),
            variant_type=s.get("variant_type", "base"),
            variant_of=s.get("variant_of"),
            # Use explicit variant_group if present; else derive from variant_of (for
            # variant files that omit the field) or fall back to own ID (base scenarios).
            variant_group=s.get("variant_group") or s.get("variant_of") or s["id"],
            scenario_type=s.get("scenario_type", ""),
            decision_type=s.get("decision_type", ""),
            label_confidence=float(s.get("label_confidence", 0.0)),
            variant_description=s.get("variant_description", ""),
        ))

    log.info(f"Loaded {len(scenarios)} scenarios from {path}")
    return scenarios

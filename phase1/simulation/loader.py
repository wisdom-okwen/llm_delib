from __future__ import annotations

from typing import Any, Dict, List, Tuple

from simulation.agent import Agent, Feature
from simulation.utils import load_json


def load_scenarios(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    scenario_path = config["data"]["scenario_path"]
    raw_data = load_json(scenario_path)

    if isinstance(raw_data, dict):
        scenarios = raw_data.get("scenarios", [])
    else:
        scenarios = raw_data

    scenario_ids = config["data"].get("scenario_ids")
    max_scenarios = config["data"].get("max_scenarios")

    if scenario_ids:
        scenarios = [s for s in scenarios if s.get("id") in scenario_ids]

    if max_scenarios is not None:
        scenarios = scenarios[:max_scenarios]

    return scenarios


def build_agent_objects_for_scenario(
    scenario: Dict[str, Any],
    config: Dict[str, Any],
) -> Tuple[List[Agent], Dict[str, List[Feature]], Dict[str, Any]]:
    view_key = config["data"]["use_private_view"]
    model_cfg = config["model"]
    agent_cfg = config["agents"]

    agent_views = scenario.get(view_key, {})
    full_view = scenario.get("full_view", [])

    tags_map = _build_feature_tags_map(full_view)

    agents: List[Agent] = []
    agent_feature_map: Dict[str, List[Feature]] = {}

    for agent_id, raw_features in agent_views.items():
        features = _parse_agent_features(raw_features, tags_map, full_view)
        agent_feature_map[agent_id] = features

        agent = Agent(
            agent_id=agent_id,
            private_features=features,
            model_type=model_cfg["model_type"],
            model_name=model_cfg["model_name"],
            temperature=model_cfg.get("temperature", 0.2),
            max_message_words=agent_cfg.get("max_message_words", 80),
        )
        agents.append(agent)

    metadata = {
        "scenario_id": scenario.get("id"),
        "question": scenario.get("question"),
        "label": scenario.get("label"),
        "full_view": full_view,
        "decisive_features": _extract_tagged_features(full_view, "decisive"),
        "misleading_features": _extract_tagged_features(full_view, "misleading"),
    }

    return agents, agent_feature_map, metadata


def _build_feature_tags_map(full_view: Dict[str, Any]) -> Dict[str, List[str]]:
    tags_map: Dict[str, List[str]] = {}
    for feature_name, feature_data in full_view.items():
        tags = feature_data.get("tags", []) or []
        if feature_name:
            tags_map[feature_name] = tags
    return tags_map


def _extract_tagged_features(full_view: Dict[str, Any], tag: str) -> List[str]:
    result = []
    for feature_name, feature_data in full_view.items():
        if tag in (feature_data.get("tags", []) or []):
            result.append(feature_name)
    return result


def _parse_agent_features(
    raw_features: Any,
    tags_map: Dict[str, List[str]],
    full_view: Dict[str, Any] = None,
) -> List[Feature]:
    parsed_features: List[Feature] = []

    if isinstance(raw_features, list):
        for item in raw_features:
            feature = _feature_from_raw(item, tags_map, full_view)
            if feature is not None:
                parsed_features.append(feature)

    elif isinstance(raw_features, dict):
  
        if "name" in raw_features:
            feature = _feature_from_raw(raw_features, tags_map, full_view)
            if feature is not None:
                parsed_features.append(feature)
        else:
            for feature_name, feature_value in raw_features.items():
                feature = _feature_from_simple_format(
                    feature_name=feature_name,
                    feature_value=feature_value,
                    tags_map=tags_map,
                    full_view=full_view
                )
                if feature is not None:
                    parsed_features.append(feature)

    return parsed_features


def _feature_from_simple_format(
    feature_name: str,
    feature_value: Any,
    tags_map: Dict[str, List[str]],
    full_view: Dict[str, Any] = None,
) -> Feature | None:
    """Create a Feature from simple {name: value} format, using full_view for metadata."""
    if not feature_name:
        return None
    
    # Get metadata from full_view if available
    cost = 0
    signal_strength = None
    tags = tags_map.get(feature_name, [])
    
    if full_view and feature_name in full_view:
        cost = int(full_view[feature_name].get("cost", 0))
        signal_strength = full_view[feature_name].get("signal_strength")
        tags = full_view[feature_name].get("tags", tags) or tags
    
    return Feature(
        name=feature_name,
        value=feature_value,
        cost=cost,
        signal_strength=signal_strength,
        tags=tags,
    )


def _feature_from_raw(
    item: Dict[str, Any],
    tags_map: Dict[str, List[str]],
    full_view: Dict[str, Any] = None,
) -> Feature | None:
    if not isinstance(item, dict):
        return None

    name = item.get("name")
    if not name:
        return None

    value = item.get("value")
    cost = int(item.get("cost", 0))
    signal_strength = item.get("signal_strength", None)
    tags = item.get("tags", tags_map.get(name, [])) or []

    return Feature(
        name=name,
        value=value,
        cost=cost,
        signal_strength=signal_strength,
        tags=tags,
    )
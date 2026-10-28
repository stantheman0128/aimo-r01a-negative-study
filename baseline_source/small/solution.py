"""Offline AIMO predictor, exported under the frozen R01 decision rule.

No network, training rows, target outcomes, or external packages are required.
The artifact's 'kind' distinguishes a trivial prior from a fitted text proxy.
"""
from __future__ import annotations
from functools import lru_cache
import json
import math
from pathlib import Path

@lru_cache(maxsize=1)
def _artifact() -> dict:
    data = json.loads((Path(__file__).resolve().parent / "predictor_artifact.json").read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("kind") not in {"majority", "configuration_prior", "configuration_structure"}:
        raise ValueError("Unsupported predictor artifact")
    if data.get("threshold") != 0.5:
        raise ValueError("Unexpected decision threshold")
    return data

def probabilities(model_id: str, reasoning_effort: str, problems: list[str]) -> list[float]:
    if not isinstance(model_id, str) or not isinstance(reasoning_effort, str):
        raise TypeError("model_id and reasoning_effort must be strings")
    if not isinstance(problems, list) or not all(isinstance(p, str) for p in problems):
        raise TypeError("problems must be a list of strings")
    data = _artifact()
    if data["kind"] in {"majority", "configuration_prior"}:
        lookup = {(c["model_id"], c["reasoning_effort"]): c["probability"] for c in data.get("configuration_probabilities", [])}
        probability = lookup.get((model_id, reasoning_effort), data["global_probability"])
        if not math.isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError("Invalid exported probability")
        return [float(probability) for _ in problems]
    from runtime_features import FEATURE_NAMES, structure_vector
    if list(FEATURE_NAMES) != data["feature_names"]:
        raise ValueError("Feature order mismatch")
    categories = data["categories"]
    config = [float(model_id == c) for c in categories[0]] + [float(reasoning_effort == c) for c in categories[1]]
    result = []
    for problem in problems:
        values = structure_vector(problem)
        values = [(v-m)/s for v, m, s in zip(values, data["mean"], data["scale"])] + config
        if len(values) != len(data["coefficients"]):
            raise ValueError("Coefficient shape mismatch")
        margin = data["intercept"] + sum(v*w for v, w in zip(values, data["coefficients"]))
        if margin >= 0:
            probability = 1/(1+math.exp(-margin))
        else:
            exp_margin = math.exp(margin)
            probability = exp_margin/(1+exp_margin)
        result.append(probability)
    return result

def are_robust(model_id: str, reasoning_effort: str, problems: list[str]) -> list[bool]:
    """Official current entry point. Native bool values and full coverage."""
    return [bool(p >= 0.5) for p in probabilities(model_id, reasoning_effort, problems)]

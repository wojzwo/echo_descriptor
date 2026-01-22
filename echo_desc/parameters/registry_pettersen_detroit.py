from __future__ import annotations

from typing import Dict

from .base import Parameter, ParamRegistry
from ..config.io import load_yaml, ensure_bootstrap_file  # albo require()


def build_registry_pettersen_detroit() -> ParamRegistry:
    # bierzemy LOCAL plik (z bootstrapem w config layer)
    path = ensure_bootstrap_file("parameters/pettersen_detroit.yaml")
    doc = load_yaml(path)

    if not isinstance(doc, dict) or "params" not in doc or not isinstance(doc["params"], dict):
        raise ValueError(f"Invalid params YAML format in {path}")

    params_out: Dict[str, Parameter] = {}

    for key, spec in doc["params"].items():
        if not isinstance(spec, dict):
            raise ValueError(f"Invalid spec for param {key} in {path}: expected dict")

        alpha = float(spec["alpha"])
        mean = float(spec["mean"])
        sd = float(spec["sd"])
        desc = spec.get("description")
        unit = spec.get("unit")

        params_out[str(key)] = Parameter(
            name=str(key),
            alpha=alpha,
            mean=mean,
            sd=sd,
            description=None if desc is None else str(desc),
            unit=None if unit is None else str(unit),
        )

    return ParamRegistry(params_out)

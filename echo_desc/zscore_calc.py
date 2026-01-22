# echo_desc/zscore_calc.py
from __future__ import annotations
from typing import Dict

from .parameters.base import ParamRegistry
from .model import EchoValues

class ZScoreCalculator:
    def __init__(self, registry: ParamRegistry):
        self.registry = registry

    def compute(self, raw: EchoValues, bsa: float) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for pname in self.registry.names():
            p = self.registry.get(pname)
            if p is None:
                continue
            v = raw.get(pname)
            if v is None:
                continue
            try:
                out[pname + "_z"] = p.z_score(v, bsa)
            except Exception:
                out[pname + "_z"] = float("nan")
        return out

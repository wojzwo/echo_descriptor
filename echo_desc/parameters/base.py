# echo_desc/parameters/base.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, List

from ..core_math import calculate_z_score


@dataclass(frozen=True)
class Parameter:
    name: str
    alpha: float
    mean: float
    sd: float
    description: Optional[str] = None
    unit: Optional[str] = None

    def z_score(self, value: float, bsa: float) -> float:
        return calculate_z_score(value, bsa, self.alpha, self.mean, self.sd)


class ParamRegistry:
    def __init__(self, params: Dict[str, Parameter]):
        self._params = dict(params)

    def get(self, name: str) -> Optional[Parameter]:
        return self._params.get(name)

    def names(self) -> List[str]:
        return sorted(self._params.keys())

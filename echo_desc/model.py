# echo_desc/model.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .core_math import calculate_bsa


@dataclass
class PatientInputs:
    weight_kg: float
    height_cm: float

    @property
    def bsa(self) -> float:
        return calculate_bsa(self.weight_kg, self.height_cm)

@dataclass
class EchoValues:
    values: Dict[str, float]

    def get(self, key: str) -> Optional[float]:
        return self.values.get(key)

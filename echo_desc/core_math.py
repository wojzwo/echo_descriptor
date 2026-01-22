# echo_desc/core_math.py
from __future__ import annotations
from typing import Any

def calculate_bsa(weight_kg: float, height_cm: float) -> float:
    return 0.024265 * (weight_kg ** 0.5378) * (height_cm ** 0.3964)

def calculate_z_score(value: float, bsa: float, alpha: float, mean: float, sd: float) -> float:
    if sd == 0:
        raise ValueError("SD cannot be 0.")
    if bsa <= 0:
        raise ValueError("BSA must be > 0.")
    normalized_value = value / (bsa ** alpha)
    return (normalized_value - mean) / sd

def fmt_num(x: Any, ndigits: int = 2) -> str:
    if x is None:
        return ""
    try:
        if isinstance(x, (int, float)):
            return f"{x:.{ndigits}f}"
        return str(x)
    except Exception:
        return str(x)

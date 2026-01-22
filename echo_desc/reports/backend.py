from __future__ import annotations
from typing import Dict, Any

from ..model import PatientInputs, EchoValues
from ..parameters.base import ParamRegistry
from ..zscore_calc import ZScoreCalculator
from .templating import TemplateRenderer
from .report_templates import ReportTemplate, ParagraphTemplate


def build_context(patient: PatientInputs, raw: EchoValues, zscores: Dict[str, float]) -> Dict[str, Any]:
    ctx: Dict[str, Any] = {"BSA_m2": patient.bsa}
    ctx.update(raw.values)
    ctx.update(zscores)
    return ctx


def generate_report(
    patient: PatientInputs,
    raw: EchoValues,
    registry: ParamRegistry,
    template: ReportTemplate,
    paragraphs: Dict[str, ParagraphTemplate],
) -> str:
    calc = ZScoreCalculator(registry)
    z = calc.compute(raw, patient.bsa)
    ctx = build_context(patient, raw, z)
    renderer = TemplateRenderer()
    return template.render(renderer, ctx, paragraphs)

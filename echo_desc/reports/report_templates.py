# echo_desc/reports/report_templates.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Iterable

from .templating import TemplateRenderer


@dataclass
class ParagraphTemplate:
    id: str
    text: str
    label: str | None = None  # ładna nazwa do UI (checkboxy)


@dataclass
class ReportTemplate:
    id: str
    title: str
    paragraphs: List[ParagraphTemplate]

    def render(self, renderer: TemplateRenderer, ctx: Dict[str, Any]) -> str:
        rendered: List[str] = []
        for p in self.paragraphs:
            rendered.append(renderer.render(p.text, ctx))
        return "\n\n".join(rendered)


def build_report_template_default() -> ReportTemplate:
    paragraphs = [
        ParagraphTemplate(
            id="norms",
            label="Normy / źródło",
            text="W badaniu zastosowano normy wg Pettersen MD i wsp., J Am Soc Echocardiogr. 2008 21(8):922/34 (Z-scores, Detroit Data).",
        ),
        ParagraphTemplate(
            id="bsa",
            label="BSA",
            text="BSA= {BSA_m2:.2f} m2.",
        ),
        ParagraphTemplate(
            id="lv_dims",
            label="LV (LVEDD/LVST/LVPWT)",
            text=(
                "Wymiar poprzeczny i grubość mięśnia lewej komory w normie: "
                "LVEDD= {LVEDD:.2f} (z= {LVEDD_z:.2f}), "
                "LVST= {LVST:.2f} (z= {LVST_z:.2f}), "
                "LVPWT= {LVPWT:.2f} (z= {LVPWT_z:.2f})."
            ),
        ),
        ParagraphTemplate(
            id="aorta",
            label="Aorta (ANN/ROOT/STJ/AAO)",
            text=(
                "Aorta: pierścień {ANN:.2f} (z= {ANN_z:.2f}), "
                "opuszka {ROOT:.2f} (z= {ROOT_z:.2f}), "
                "STJ {STJ:.2f} (z= {STJ_z:.2f}), "
                "aorta wstępująca {AAO:.2f} (z= {AAO_z:.2f})."
            ),
        ),
        ParagraphTemplate(
            id="pa",
            label="T. płucna (MPA/RPA/LPA)",
            text=(
                "Tętnica płucna: MPA= {MPA:.2f} (z= {MPA_z:.2f}), "
                "RPA= {RPA:.2f} (z= {RPA_z:.2f}), "
                "LPA= {LPA:.2f} (z= {LPA_z:.2f})."
            ),
        ),
        ParagraphTemplate(
            id="conclusion",
            label="Wnioski",
            text="Wnioski: Bez cech ewidentnej wady. IT i IP w granicach fizjologii. Struna ścięgnista w LV.",
        ),
    ]
    return ReportTemplate(id="default_echo", title="Domyślny (skrót)", paragraphs=paragraphs)


def get_report_templates() -> Dict[str, ReportTemplate]:
    """
    Zwraca wszystkie dostępne templatki.
    Dodasz kolejne -> dopisujesz tu.
    """
    t1 = build_report_template_default()
    return {t1.id: t1}


def filter_template(base: ReportTemplate, selected_paragraph_ids: Iterable[str]) -> ReportTemplate:
    """
    Zostawia tylko zaznaczone akapity.
    """
    selected = set(selected_paragraph_ids)
    paragraphs = [p for p in base.paragraphs if p.id in selected]
    return ReportTemplate(id=base.id, title=base.title, paragraphs=paragraphs)

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Iterable
from pathlib import Path

from .templating import TemplateRenderer
from ..config.io import load_yaml, ensure_bootstrap_file


@dataclass
class ParagraphTemplate:
    id: str
    text: str
    label: str | None = None


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


def get_report_templates() -> Dict[str, ReportTemplate]:
    """
    Loads templates from LOCAL config:
      ~/.config/echo_desc/reports/templates.yaml
    Bootstrapped from packaged defaults:
      echo_desc/config_defaults/reports/templates.yaml
    """
    path = ensure_bootstrap_file("reports/templates.yaml")
    doc = load_yaml(path)

    if not isinstance(doc, dict) or "templates" not in doc or not isinstance(doc["templates"], list):
        raise ValueError(f"Invalid templates YAML: {path}")

    out: Dict[str, ReportTemplate] = {}

    for t in doc["templates"]:
        if not isinstance(t, dict):
            continue

        tid = str(t.get("id", "")).strip()
        title = str(t.get("title", tid)).strip()
        plist = t.get("paragraphs", [])

        if not tid or not isinstance(plist, list):
            continue

        paragraphs: List[ParagraphTemplate] = []
        for p in plist:
            if not isinstance(p, dict):
                continue
            pid = str(p.get("id", "")).strip()
            text = str(p.get("text", "")).strip()
            label = p.get("label")
            if not pid or not text:
                continue
            paragraphs.append(
                ParagraphTemplate(
                    id=pid,
                    text=text,
                    label=None if label is None else str(label),
                )
            )

        out[tid] = ReportTemplate(id=tid, title=title, paragraphs=paragraphs)

    if not out:
        raise ValueError(f"No templates loaded from {path}")

    return out


def filter_template(base: ReportTemplate, selected_paragraph_ids: Iterable[str]) -> ReportTemplate:
    selected = set(selected_paragraph_ids)
    paragraphs = [p for p in base.paragraphs if p.id in selected]
    return ReportTemplate(id=base.id, title=base.title, paragraphs=paragraphs)

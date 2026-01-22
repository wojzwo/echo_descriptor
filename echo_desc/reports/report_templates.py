from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Iterable, Tuple

from .templating import TemplateRenderer
from ..config.io import load_yaml, ensure_bootstrap_file


@dataclass(frozen=True)
class ParagraphTemplate:
    id: str
    text: str
    label: str | None = None


@dataclass(frozen=True)
class ReportTemplate:
    id: str
    title: str
    paragraph_ids: List[str]

    def render(
        self,
        renderer: TemplateRenderer,
        ctx: Dict[str, Any],
        paragraphs_by_id: Dict[str, ParagraphTemplate],
    ) -> str:
        rendered: List[str] = []
        for pid in self.paragraph_ids:
            p = paragraphs_by_id.get(pid)
            if p is None:
                # twardo sygnalizujemy błąd konfiguracji (zostawiam czytelny marker w raporcie)
                rendered.append(f"###BRAK PARAGRAFU:{pid}###")
                continue
            rendered.append(renderer.render(p.text, ctx))
        return "\n\n".join(rendered)


def _parse_paragraphs(doc: Dict[str, Any]) -> Dict[str, ParagraphTemplate]:
    lst = doc.get("paragraphs")
    if not isinstance(lst, list):
        raise ValueError("Invalid templates YAML: missing or invalid 'paragraphs' (must be list)")

    out: Dict[str, ParagraphTemplate] = {}
    for item in lst:
        if not isinstance(item, dict):
            continue
        pid = str(item.get("id", "")).strip()
        text = str(item.get("text", "")).strip()
        if not pid or not text:
            continue
        label = item.get("label")
        out[pid] = ParagraphTemplate(
            id=pid,
            text=text,
            label=None if label is None else str(label),
        )

    if not out:
        raise ValueError("Invalid templates YAML: no valid paragraphs found")
    return out


def _parse_reports(doc: Dict[str, Any]) -> Dict[str, ReportTemplate]:
    lst = doc.get("reports")
    if not isinstance(lst, list):
        raise ValueError("Invalid templates YAML: missing or invalid 'reports' (must be list)")

    out: Dict[str, ReportTemplate] = {}
    for item in lst:
        if not isinstance(item, dict):
            continue
        rid = str(item.get("id", "")).strip()
        title = str(item.get("title", rid)).strip()
        pids = item.get("paragraph_ids")

        if not rid or not isinstance(pids, list):
            continue

        paragraph_ids: List[str] = []
        for x in pids:
            s = str(x).strip()
            if s:
                paragraph_ids.append(s)

        if not paragraph_ids:
            continue

        out[rid] = ReportTemplate(id=rid, title=title, paragraph_ids=paragraph_ids)

    if not out:
        raise ValueError("Invalid templates YAML: no valid reports found")
    return out


def get_report_templates() -> Tuple[Dict[str, ParagraphTemplate], Dict[str, ReportTemplate]]:
    """
    Loads templates from LOCAL config:
      <repo_root>/config/reports/templates.yaml
    Bootstrapped from packaged defaults:
      echo_desc/config_defaults/reports/templates.yaml

    Returns:
      (paragraphs_by_id, reports_by_id)
    """
    path = ensure_bootstrap_file("reports/templates.yaml")
    doc = load_yaml(path)

    if not isinstance(doc, dict):
        raise ValueError(f"Invalid templates YAML: {path}")

    paragraphs = _parse_paragraphs(doc)
    reports = _parse_reports(doc)

    # Walidacja referencji: reporty muszą wskazywać istniejące paragrafy
    missing: List[str] = []
    for r in reports.values():
        for pid in r.paragraph_ids:
            if pid not in paragraphs:
                missing.append(f"{r.id}:{pid}")
    if missing:
        # celowo fail-fast: config jest niepoprawny
        raise ValueError(
            "Templates YAML: report references unknown paragraph ids: "
            + ", ".join(missing)
        )

    return paragraphs, reports


def filter_report(
    base: ReportTemplate,
    selected_paragraph_ids: Iterable[str],
) -> ReportTemplate:
    """
    Zachowuje kolejność z base.paragraph_ids, ale usuwa te nie zaznaczone.
    """
    selected = set(selected_paragraph_ids)
    new_ids = [pid for pid in base.paragraph_ids if pid in selected]
    return ReportTemplate(id=base.id, title=base.title, paragraph_ids=new_ids)

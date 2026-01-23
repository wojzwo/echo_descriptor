from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Iterable, List, Tuple

from ..config.io import load_yaml, ensure_bootstrap_file, save_yaml
from .templating import TemplateRenderer


@dataclass
class ParagraphTemplate:
    id: str
    label: str
    text: str
    description: str = ""


@dataclass
class ReportTemplate:
    id: str
    title: str
    paragraph_ids: List[str]

    def render(
        self,
        renderer: TemplateRenderer,
        ctx: Dict[str, Any],
        paragraphs: Dict[str, ParagraphTemplate],
    ) -> str:
        rendered: List[str] = []
        for pid in self.paragraph_ids:
            p = paragraphs.get(pid)
            if p is None:
                rendered.append(f"###BRAK PARAGRAFU:{pid}###")
                continue
            rendered.append(renderer.render(p.text, ctx))
        return "\n\n".join(rendered)


def _templates_relpath() -> str:
    # relative path inside config tree
    return "reports/templates.yaml"


def templates_path():
    """
    Repo-local config path (bootstrapped from defaults if missing).
    """
    return ensure_bootstrap_file(_templates_relpath())


def get_report_templates() -> Tuple[Dict[str, ParagraphTemplate], Dict[str, ReportTemplate]]:
    """
    Loads templates YAML (repo-local, bootstrapped from defaults):

      paragraphs:
        - id: ...
          label: ...
          description: ...
          text: ...

      reports:
        - id: ...
          title: ...
          paragraph_ids: [par1, par2, ...]

    Returns:
      (paragraphs_by_id, reports_by_id)

    NOTE (prototype-friendly):
      - empty paragraphs/reports are allowed (editor can start from blank)
      - invalid YAML structure -> ValueError
    """
    path = templates_path()
    doc = load_yaml(path)

    if doc is None:
        # empty file -> treat as blank structure
        return {}, {}

    if not isinstance(doc, dict):
        raise ValueError(f"Invalid templates YAML (root must be dict): {path}")

    par_list = doc.get("paragraphs", [])
    rep_list = doc.get("reports", [])

    if not isinstance(par_list, list) or not isinstance(rep_list, list):
        raise ValueError(f"Invalid templates YAML (paragraphs/reports must be lists): {path}")

    paragraphs: Dict[str, ParagraphTemplate] = {}
    for it in par_list:
        if not isinstance(it, dict):
            continue
        pid = str(it.get("id", "")).strip()
        if not pid:
            continue

        label = str(it.get("label", pid)).strip() or pid
        text = str(it.get("text", "")).strip()
        desc = str(it.get("description", "") or "").strip()

        # allow creating "stub" paragraph in editor (text can be empty), but
        # runtime rendering will show empty -> blank paragraph (fine)
        paragraphs[pid] = ParagraphTemplate(
            id=pid,
            label=label,
            text=text,
            description=desc,
        )

    reports: Dict[str, ReportTemplate] = {}
    for it in rep_list:
        if not isinstance(it, dict):
            continue
        rid = str(it.get("id", "")).strip()
        if not rid:
            continue
        title = str(it.get("title", rid)).strip() or rid

        pids = it.get("paragraph_ids", [])
        if not isinstance(pids, list):
            pids = []

        pids_norm = [str(x).strip() for x in pids if str(x).strip()]
        reports[rid] = ReportTemplate(id=rid, title=title, paragraph_ids=pids_norm)

    return paragraphs, reports


def save_report_templates(
    paragraphs: Dict[str, ParagraphTemplate],
    reports: Dict[str, ReportTemplate],
) -> None:
    """
    Save into repo-local: ./config/reports/templates.yaml
    (path is obtained via ensure_bootstrap_file so file exists)
    """
    path = templates_path()

    par_out: List[Dict[str, Any]] = []
    for pid in sorted(paragraphs.keys()):
        p = paragraphs[pid]
        par_out.append(
            {
                "id": p.id,
                "label": p.label,
                "description": p.description or "",
                "text": p.text or "",
            }
        )

    rep_out: List[Dict[str, Any]] = []
    for rid in sorted(reports.keys()):
        r = reports[rid]
        rep_out.append(
            {
                "id": r.id,
                "title": r.title,
                "paragraph_ids": list(r.paragraph_ids),
            }
        )

    doc = {"paragraphs": par_out, "reports": rep_out}
    save_yaml(path, doc)


def filter_report(
    base: ReportTemplate,
    selected_paragraph_ids: Iterable[str],
) -> ReportTemplate:
    """
    Runtime filter zachowujący kolejność z raportu.
    """
    sel = set(selected_paragraph_ids)
    out = [pid for pid in base.paragraph_ids if pid in sel]
    return ReportTemplate(id=base.id, title=base.title, paragraph_ids=out)

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


# -----------------------
# Paths (relative in config tree)
# -----------------------
def _paragraphs_relpath() -> str:
    return "reports/paragraphs.yaml"


def _reports_relpath() -> str:
    return "reports/reports.yaml"


def paragraphs_path():
    """
    Repo-local config path (bootstrapped from defaults if missing).
    """
    return ensure_bootstrap_file(_paragraphs_relpath())


def reports_path():
    """
    Repo-local config path (bootstrapped from defaults if missing).
    """
    return ensure_bootstrap_file(_reports_relpath())


# -----------------------
# Load
# -----------------------
def get_report_templates() -> Tuple[Dict[str, ParagraphTemplate], Dict[str, ReportTemplate]]:
    """
    Loads templates YAML (repo-local, bootstrapped from defaults):

    paragraphs.yaml:
      paragraphs:
        - id: ...
          label: ...
          description: ...
          text: ...

    reports.yaml:
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
    p_path = paragraphs_path()
    r_path = reports_path()

    par_doc = load_yaml(p_path)
    rep_doc = load_yaml(r_path)

    # empty file -> treat as blank structure
    if par_doc is None:
        par_doc = {}
    if rep_doc is None:
        rep_doc = {}

    if not isinstance(par_doc, dict):
        raise ValueError(f"Invalid paragraphs YAML (root must be dict): {p_path}")
    if not isinstance(rep_doc, dict):
        raise ValueError(f"Invalid reports YAML (root must be dict): {r_path}")

    par_list = par_doc.get("paragraphs", [])
    rep_list = rep_doc.get("reports", [])

    if not isinstance(par_list, list):
        raise ValueError(f"Invalid paragraphs YAML (paragraphs must be list): {p_path}")
    if not isinstance(rep_list, list):
        raise ValueError(f"Invalid reports YAML (reports must be list): {r_path}")

    paragraphs: Dict[str, ParagraphTemplate] = {}
    for it in par_list:
        if not isinstance(it, dict):
            continue
        pid = str(it.get("id", "")).strip()
        if not pid:
            continue

        label = str(it.get("label", pid)).strip() or pid
        text = str(it.get("text", "") or "")  # keep as-is (can contain newlines)
        desc = str(it.get("description", "") or "").strip()

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


# -----------------------
# Save
# -----------------------
def save_report_templates(
    paragraphs: Dict[str, ParagraphTemplate],
    reports: Dict[str, ReportTemplate],
) -> None:
    """
    Save into repo-local:
      ./config/reports/paragraphs.yaml
      ./config/reports/reports.yaml
    (paths are obtained via ensure_bootstrap_file so files exist)
    """
    p_path = paragraphs_path()
    r_path = reports_path()

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

    save_yaml(p_path, {"paragraphs": par_out})
    save_yaml(r_path, {"reports": rep_out})


# -----------------------
# Runtime helper
# -----------------------
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

# echo_desc/web/templates_store.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple
import re

from ..config.io import ensure_bootstrap_file, load_yaml, save_yaml


_ID_RE = re.compile(r"^[a-zA-Z0-9_]+$")


# -----------------------
# Paths (config/io SSOT)
# -----------------------
def paragraphs_path():
    return ensure_bootstrap_file("reports/paragraphs.yaml")


def reports_path():
    return ensure_bootstrap_file("reports/reports.yaml")


# -----------------------
# Load
# -----------------------
def load_templates() -> Dict[str, Any]:
    """
    Unified doc for UI:
      {"paragraphs":[...], "reports":[...]}
    Backing store:
      reports/paragraphs.yaml, reports/reports.yaml
    """
    par_doc = load_yaml(paragraphs_path())
    rep_doc = load_yaml(reports_path())

    if not isinstance(par_doc, dict):
        par_doc = {}
    if not isinstance(rep_doc, dict):
        rep_doc = {}

    paragraphs = par_doc.get("paragraphs", [])
    reports = rep_doc.get("reports", [])

    if not isinstance(paragraphs, list):
        paragraphs = []
    if not isinstance(reports, list):
        reports = []

    return {"paragraphs": paragraphs, "reports": reports}


def ensure_nonempty_reports() -> Dict[str, Any]:
    """
    Guarantees at least one report exists (so UI <select> has something).
    If reports empty -> write minimal default report.
    If paragraphs empty -> write minimal default paragraph first.
    """
    doc = load_templates()
    reports = doc.get("reports", [])
    if isinstance(reports, list) and len(reports) > 0:
        return doc

    paragraphs = doc.get("paragraphs", [])
    if not isinstance(paragraphs, list):
        paragraphs = []

    # ensure at least one paragraph exists so report can reference something
    if len(paragraphs) == 0:
        save_yaml(
            paragraphs_path(),
            {
                "paragraphs": [
                    {
                        "id": "norms",
                        "label": "Normy / źródło",
                        "description": "",
                        "text": "Normy: ...",
                    }
                ]
            },
        )
        paragraphs = load_yaml(paragraphs_path()).get("paragraphs", [])  # type: ignore

    # choose first paragraph id (stable)
    first_pid = ""
    for p in paragraphs:
        if isinstance(p, dict):
            pid = str(p.get("id", "")).strip()
            if pid:
                first_pid = pid
                break
    if not first_pid:
        first_pid = "norms"

    save_yaml(
        reports_path(),
        {
            "reports": [
                {"id": "default_echo", "title": "Domyślny", "paragraph_ids": [first_pid]}
            ]
        },
    )
    return load_templates()


# -----------------------
# UI helper: map reports
# -----------------------
def build_reports_map(doc: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    pars_list = doc.get("paragraphs", [])
    rep_list = doc.get("reports", [])

    pmap: Dict[str, Dict[str, Any]] = {}
    if isinstance(pars_list, list):
        for p in pars_list:
            if not isinstance(p, dict):
                continue
            pid = str(p.get("id", "")).strip()
            if not pid:
                continue
            pmap[pid] = {
                "id": pid,
                "label": str(p.get("label", pid)).strip(),
                "description": str(p.get("description", "") or "").strip(),
                "text": str(p.get("text", "") or ""),
            }

    out: Dict[str, Dict[str, Any]] = {}
    if isinstance(rep_list, list):
        for r in rep_list:
            if not isinstance(r, dict):
                continue
            rid = str(r.get("id", "")).strip()
            if not rid:
                continue
            title = str(r.get("title", rid)).strip()

            pids = r.get("paragraph_ids", [])
            if not isinstance(pids, list):
                pids = []

            paragraphs: List[Dict[str, Any]] = []
            for pid in pids:
                pid2 = str(pid).strip()
                if pid2 in pmap:
                    paragraphs.append(pmap[pid2])

            out[rid] = {"id": rid, "title": title, "paragraphs": paragraphs}

    return out


# -----------------------
# Validate
# -----------------------
def validate_templates(payload: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(payload, dict):
        return False, "payload not dict"

    paragraphs = payload.get("paragraphs")
    reports = payload.get("reports")
    if not isinstance(paragraphs, list) or not isinstance(reports, list):
        return False, "payload must contain paragraphs:list and reports:list"

    seen_par: set[str] = set()
    for p in paragraphs:
        if not isinstance(p, dict):
            return False, "paragraph entry invalid"

        pid = str(p.get("id", "")).strip()
        if not pid or not _ID_RE.match(pid):
            return False, f"invalid paragraph id: {pid}"
        if pid in seen_par:
            return False, f"duplicate paragraph id: {pid}"
        seen_par.add(pid)

        text = str(p.get("text", "") or "")
        if not text.strip():
            return False, f"paragraph {pid} has empty text"

        label = str(p.get("label", "") or "").strip()
        if not label:
            return False, f"paragraph {pid} has empty label"

    seen_rep: set[str] = set()
    for r in reports:
        if not isinstance(r, dict):
            return False, "report entry invalid"

        rid = str(r.get("id", "")).strip()
        if not rid or not _ID_RE.match(rid):
            return False, f"invalid report id: {rid}"
        if rid in seen_rep:
            return False, f"duplicate report id: {rid}"
        seen_rep.add(rid)

        title = str(r.get("title", "") or "").strip()
        if not title:
            return False, f"report {rid} has empty title"

        pids = r.get("paragraph_ids", [])
        if not isinstance(pids, list):
            return False, f"report {rid} paragraph_ids must be list"

        pids_norm = [str(x).strip() for x in pids if str(x).strip()]
        if len(pids_norm) == 0:
            return False, f"report {rid} has empty paragraph_ids"

        for pid in pids_norm:
            if pid not in seen_par:
                return False, f"report {rid} references missing paragraph: {pid}"

    if len(seen_rep) == 0:
        return False, "no reports defined"
    if len(seen_par) == 0:
        return False, "no paragraphs defined"

    return True, ""


# -----------------------
# Save (split into two files)
# -----------------------
def save_templates(payload: Dict[str, Any]) -> None:
    """
    Saves into:
      config/reports/paragraphs.yaml
      config/reports/reports.yaml
    Assumes validate_templates() already passed.
    """
    paragraphs = payload.get("paragraphs", [])
    reports = payload.get("reports", [])

    def _par_key(x: Any) -> str:
        if not isinstance(x, dict):
            return "~~~"
        return str(x.get("id", "")).strip()

    def _rep_key(x: Any) -> str:
        if not isinstance(x, dict):
            return "~~~"
        return str(x.get("id", "")).strip()

    # de-duplicate paragraph_ids per report (preserve order)
    rep_norm: List[Dict[str, Any]] = []
    for r in reports if isinstance(reports, list) else []:
        if not isinstance(r, dict):
            continue
        pids = r.get("paragraph_ids", [])
        if not isinstance(pids, list):
            pids = []

        seen: set[str] = set()
        uniq: List[str] = []
        for pid in pids:
            pid2 = str(pid).strip()
            if not pid2 or pid2 in seen:
                continue
            seen.add(pid2)
            uniq.append(pid2)

        rep_norm.append(
            {
                "id": str(r.get("id", "")).strip(),
                "title": str(r.get("title", "")).strip(),
                "paragraph_ids": uniq,
            }
        )

    save_yaml(paragraphs_path(), {"paragraphs": sorted(paragraphs, key=_par_key)})
    save_yaml(reports_path(), {"reports": sorted(rep_norm, key=_rep_key)})

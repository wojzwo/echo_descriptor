# echo_desc/web/templates_store.py
from __future__ import annotations

from typing import Dict, Any, List, Tuple
from pathlib import Path
import re

from ..config.io import load_yaml, save_yaml


_ID_RE = re.compile(r"^[a-zA-Z0-9_]+$")


# -----------------------
# Path + bootstrap (safe)
# -----------------------
def templates_path(repo_root: Path) -> Path:
    """
    Single source of truth:
      <repo>/config/reports/templates.yaml
    """
    return (repo_root / "config" / "reports" / "templates.yaml").resolve()


def bootstrap_templates(repo_root: Path) -> None:
    """
    Minimal safety: if templates.yaml missing => create minimal valid file.
    No migrations, no versions, no legacy parsing.
    """
    p = templates_path(repo_root)
    if p.exists():
        return

    p.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "paragraphs": [
            {
                "id": "norms",
                "label": "Normy / źródło",
                "description": "",
                "text": "Normy: ...",
            }
        ],
        "reports": [
            {
                "id": "default_echo",
                "title": "Domyślny",
                "paragraph_ids": ["norms"],
            }
        ],
    }
    save_yaml(p, doc)


# -----------------------
# Load / ensure non-empty
# -----------------------
def load_templates(repo_root: Path) -> Dict[str, Any]:
    bootstrap_templates(repo_root)
    p = templates_path(repo_root)

    doc = load_yaml(p)
    if not isinstance(doc, dict):
        return {"paragraphs": [], "reports": []}

    paragraphs = doc.get("paragraphs", [])
    reports = doc.get("reports", [])

    if not isinstance(paragraphs, list):
        paragraphs = []
    if not isinstance(reports, list):
        reports = []

    return {"paragraphs": paragraphs, "reports": reports}


def ensure_nonempty_reports(repo_root: Path) -> Dict[str, Any]:
    """
    Guarantees at least one report exists, otherwise creates minimal defaults.
    This prevents StopIteration when UI wants default report for <select>.
    """
    doc = load_templates(repo_root)
    reports = doc.get("reports", [])
    if isinstance(reports, list) and len(reports) > 0:
        return doc

    # overwrite with minimal defaults
    bootstrap_templates(repo_root)
    return load_templates(repo_root)


# -----------------------
# UI helper: map reports
# -----------------------
def build_reports_map(doc: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    For UI convenience:
      {report_id: {id,title, paragraphs:[{id,label,description,text}]}}
    Missing paragraph references are simply skipped here (validation will catch it on save).
    """
    pars_list = doc.get("paragraphs", [])
    rep_list = doc.get("reports", [])

    pmap: Dict[str, Dict[str, Any]] = {}
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
# Validate / save
# -----------------------
def validate_templates(payload: Dict[str, Any]) -> Tuple[bool, str]:
    """
    payload schema:
      { paragraphs: [ {id,label,description,text}... ],
        reports:    [ {id,title,paragraph_ids:[...]}... ] }
    """
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

        # label can be empty but it's pointless; enforce at least fallback-able
        label = str(p.get("label", "") or "").strip()
        if not label:
            return False, f"paragraph {pid} has empty label"

        # description optional, no constraints

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

        # allow empty report? I'd say no (UI+report generation). Enforce at least one.
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


def save_templates(repo_root: Path, payload: Dict[str, Any]) -> None:
    """
    Write into: <repo>/config/reports/templates.yaml
    Assumes validate_templates() already passed.
    """
    p = templates_path(repo_root)
    p.parent.mkdir(parents=True, exist_ok=True)

    # normalize output (stable ordering makes diffs readable)
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

    out = {
        "paragraphs": sorted(paragraphs, key=_par_key),
        "reports": sorted(reports, key=_rep_key),
    }
    save_yaml(p, out)

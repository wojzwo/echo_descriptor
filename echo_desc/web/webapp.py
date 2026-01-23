from __future__ import annotations

from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import json
import re

from fastapi import FastAPI, Request, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from ..config.io import ensure_bootstrap_tree, load_yaml, save_yaml
from ..model import PatientInputs, EchoValues
from ..parameters.registry_pettersen_detroit import build_registry_pettersen_detroit
from ..reports.backend import generate_report

app = FastAPI(title="Echo Descriptor")

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

REGISTRY = None

_ID_RE = re.compile(r"^[a-zA-Z0-9_]+$")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def active_config_dir() -> Path:
    return (repo_root() / "config").resolve()


# ---------- Param UI ----------
def param_ui_path() -> Path:
    return (active_config_dir() / "web" / "parameters_ui.yaml").resolve()


def load_param_ui() -> Dict[str, Dict[str, Any]]:
    p = param_ui_path()
    if not p.exists():
        return {}
    doc = load_yaml(p)
    if not isinstance(doc, dict):
        return {}
    lst = doc.get("params")
    if not isinstance(lst, list):
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for item in lst:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        enabled = bool(item.get("enabled", True))
        try:
            order = int(item.get("order", 9999))
        except Exception:
            order = 9999
        out[name] = {"enabled": enabled, "order": order}
    return out


def build_param_items() -> List[Dict[str, Any]]:
    assert REGISTRY is not None
    items: List[Dict[str, Any]] = []
    for name in REGISTRY.names():
        p = REGISTRY.get(name)
        desc = getattr(p, "description", None) if p is not None else None
        items.append({"name": name, "label": name, "description": "" if desc is None else str(desc)})
    return items


def split_and_sort_params(
    param_items: List[Dict[str, Any]],
    ui: Dict[str, Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    default_order: Dict[str, int] = {it["name"]: (i + 1) * 10 for i, it in enumerate(param_items)}

    def key_fn(it: Dict[str, Any]) -> tuple:
        n = it["name"]
        order = ui.get(n, {}).get("order", default_order.get(n, 9999))
        return (int(order), n)

    visible: List[Dict[str, Any]] = []
    hidden: List[Dict[str, Any]] = []
    for it in param_items:
        n = it["name"]
        enabled = ui.get(n, {}).get("enabled", True)
        (visible if enabled else hidden).append(it)

    visible.sort(key=key_fn)
    hidden.sort(key=key_fn)
    return visible, hidden


# ---------- Templates V2 (paragraphs + reports) ----------
def templates_v2_path() -> Path:
    return (active_config_dir() / "reports" / "templates_v2.yaml").resolve()


def _bootstrap_templates_v2() -> None:
    """
    If config/reports/templates_v2.yaml doesn't exist, generate it from old v1 templates.yaml
    if present, otherwise create a tiny default.
    """
    p = templates_v2_path()
    if p.exists():
        return

    p.parent.mkdir(parents=True, exist_ok=True)

    old = (active_config_dir() / "reports" / "templates.yaml").resolve()
    if old.exists():
        doc = load_yaml(old)
        # v1: templates: [{id,title,paragraphs:[{id,label,text}]}]
        paragraphs: Dict[str, Dict[str, Any]] = {}
        reports: List[Dict[str, Any]] = []
        if isinstance(doc, dict) and isinstance(doc.get("templates"), list):
            for t in doc["templates"]:
                if not isinstance(t, dict):
                    continue
                tid = str(t.get("id", "")).strip()
                title = str(t.get("title", tid)).strip()
                plist = t.get("paragraphs", [])
                if not tid or not isinstance(plist, list):
                    continue
                pids: List[str] = []
                for par in plist:
                    if not isinstance(par, dict):
                        continue
                    pid = str(par.get("id", "")).strip()
                    if not pid:
                        continue
                    label = str(par.get("label", pid)).strip()
                    text = str(par.get("text", "")).strip()
                    if pid not in paragraphs:
                        paragraphs[pid] = {"id": pid, "label": label, "description": "", "text": text}
                    pids.append(pid)
                reports.append({"id": tid, "title": title, "paragraph_ids": pids})

        out = {"version": 2, "paragraphs": list(paragraphs.values()), "reports": reports}
        save_yaml(p, out)
        return

    # fallback minimal
    out = {
        "version": 2,
        "paragraphs": [
            {"id": "norms", "label": "Normy / źródło", "description": "", "text": "Normy: ..."},
        ],
        "reports": [
            {"id": "default_echo", "title": "Domyślny", "paragraph_ids": ["norms"]},
        ],
    }
    save_yaml(p, out)


def load_templates_v2() -> Dict[str, Any]:
    _bootstrap_templates_v2()
    p = templates_v2_path()
    doc = load_yaml(p)
    if not isinstance(doc, dict):
        return {"version": 2, "paragraphs": [], "reports": []}

    paragraphs = doc.get("paragraphs")
    reports = doc.get("reports")
    if not isinstance(paragraphs, list):
        paragraphs = []
    if not isinstance(reports, list):
        reports = []
    return {"version": 2, "paragraphs": paragraphs, "reports": reports}


def build_reports_map(v2: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Build reports dict compatible with old UI selection:
      {id: {id,title, paragraphs:[{id,label,text}]}}
    """
    pars_list = v2.get("paragraphs", [])
    rep_list = v2.get("reports", [])

    pmap: Dict[str, Dict[str, Any]] = {}
    for p in pars_list:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("id", "")).strip()
        if not pid:
            continue
        pmap[pid] = {
            "id": pid,
            "label": str(p.get("label", pid)),
            "description": str(p.get("description", "")),
            "text": str(p.get("text", "")),
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
        paragraphs = []
        for pid in pids:
            pid2 = str(pid).strip()
            if pid2 in pmap:
                paragraphs.append(pmap[pid2])
        out[rid] = {"id": rid, "title": title, "paragraphs": paragraphs}
    return out


def validate_templates_v2(payload: Dict[str, Any]) -> Tuple[bool, str]:
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

        pids = r.get("paragraph_ids", [])
        if not isinstance(pids, list):
            return False, f"report {rid} paragraph_ids must be list"
        for pid in pids:
            pid2 = str(pid).strip()
            if pid2 and pid2 not in seen_par:
                return False, f"report {rid} references missing paragraph: {pid2}"

    return True, ""


# ---------- startup ----------
@app.on_event("startup")
def _startup() -> None:
    global REGISTRY
    ensure_bootstrap_tree()
    REGISTRY = build_registry_pettersen_detroit()
    _bootstrap_templates_v2()


def _safe_float(x: Any) -> Optional[float]:
    s = str(x).strip()
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def _render_index(
    request: Request,
    *,
    active_tab: str,
    selected_template_id: str,
    selected_paragraph_ids: set[str],
    weight_kg: Any,
    height_cm: Any,
    raw_vals: Dict[str, float],
    report: str,
    error: str,
) -> HTMLResponse:
    assert REGISTRY is not None

    ui = load_param_ui()
    all_items = build_param_items()
    params_visible, params_hidden = split_and_sort_params(all_items, ui)

    v2 = load_templates_v2()
    reports_map = build_reports_map(v2)

    # for select list
    templates_list = list(reports_map.values())

    # for editor preload
    templates_v2_json = json.dumps(v2, ensure_ascii=False)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "active_tab": active_tab,
            "params_visible": params_visible,
            "params_hidden": params_hidden,
            "param_items_all": all_items,
            "param_ui": ui,
            "templates_list": templates_list,
            "selected_template_id": selected_template_id,
            "selected_paragraph_ids": selected_paragraph_ids,
            "weight_kg": weight_kg,
            "height_cm": height_cm,
            "raw_vals": raw_vals,
            "report": report,
            "error": error,
            "templates_v2_json": templates_v2_json,
        },
    )


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    tab = str(request.query_params.get("tab") or "params").strip().lower()
    if tab not in {"params", "template", "settings"}:
        tab = "params"

    v2 = load_templates_v2()
    reports_map = build_reports_map(v2)
    if not reports_map:
        # ensure at least one
        _bootstrap_templates_v2()
        reports_map = build_reports_map(load_templates_v2())

    default_template_id = next(iter(reports_map.keys()))
    default_paragraph_ids = {p["id"] for p in reports_map[default_template_id]["paragraphs"]}

    return _render_index(
        request,
        active_tab=tab,
        selected_template_id=default_template_id,
        selected_paragraph_ids=default_paragraph_ids,
        weight_kg="",
        height_cm="",
        raw_vals={},
        report="",
        error="",
    )


@app.post("/settings/save")
async def save_settings(request: Request):
    form = await request.form()
    assert REGISTRY is not None
    names = REGISTRY.names()

    out_list: List[Dict[str, Any]] = []
    for n in names:
        enabled = (form.get(f"enabled__{n}") == "on")
        order_raw = form.get(f"order__{n}")
        try:
            order = int(str(order_raw).strip())
        except Exception:
            order = 9999
        out_list.append({"name": n, "enabled": enabled, "order": order})

    doc = {"params": out_list}
    p = param_ui_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    save_yaml(p, doc)

    return RedirectResponse(url="/?tab=settings", status_code=303)


@app.post("/generate", response_class=HTMLResponse)
async def generate_one_page(request: Request):
    assert REGISTRY is not None
    form = await request.form()

    weight_kg = _safe_float(form.get("weight_kg"))
    height_cm = _safe_float(form.get("height_cm"))

    v2 = load_templates_v2()
    reports_map = build_reports_map(v2)

    selected_template_id = str(form.get("template_id") or "").strip()
    if not selected_template_id or selected_template_id not in reports_map:
        selected_template_id = next(iter(reports_map.keys()))

    paragraph_ids: List[str] = list(form.getlist("paragraph_ids"))
    selected_paragraph_ids = set(paragraph_ids)

    raw_vals: Dict[str, float] = {}
    for pname in REGISTRY.names():
        v = _safe_float(form.get(pname))
        if v is not None:
            raw_vals[pname] = v

    report = ""
    error = ""

    if weight_kg is None or height_cm is None:
        error = "Nieprawidłowa masa lub wzrost."
    else:
        patient = PatientInputs(weight_kg=weight_kg, height_cm=height_cm)
        raw = EchoValues(values=raw_vals)

        # Build chosen report template paragraphs from reports_map (already materialized)
        base = reports_map[selected_template_id]
        # filter by checked paragraph_ids (old behavior)
        chosen_pars = [p for p in base["paragraphs"] if p["id"] in selected_paragraph_ids] if paragraph_ids else base["paragraphs"]

        # render
        from ..reports.templating import TemplateRenderer
        from ..zscore_calc import ZScoreCalculator
        from ..reports.backend import build_context

        calc = ZScoreCalculator(REGISTRY)
        z = calc.compute(raw, patient.bsa)
        ctx = build_context(patient, raw, z)
        renderer = TemplateRenderer()
        rendered = [renderer.render(p["text"], ctx) for p in chosen_pars]
        report = "\n\n".join(rendered)

    return _render_index(
        request,
        active_tab="params",
        selected_template_id=selected_template_id,
        selected_paragraph_ids=selected_paragraph_ids,
        weight_kg="" if weight_kg is None else weight_kg,
        height_cm="" if height_cm is None else height_cm,
        raw_vals=raw_vals,
        report=report,
        error=error,
    )


# ---------- API for template editor ----------
@app.get("/api/templates/load")
def api_templates_load():
    return load_templates_v2()


@app.post("/api/templates/save")
def api_templates_save(payload: Dict[str, Any] = Body(...)):
    ok, err = validate_templates_v2(payload)
    if not ok:
        return JSONResponse({"ok": False, "error": err}, status_code=400)

    out = {
        "version": 2,
        "paragraphs": payload.get("paragraphs", []),
        "reports": payload.get("reports", []),
    }
    p = templates_v2_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    save_yaml(p, out)
    return {"ok": True}

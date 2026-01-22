from __future__ import annotations

from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

from fastapi import FastAPI, Request, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from ..config.io import ensure_bootstrap_tree, load_yaml, save_yaml
from ..model import PatientInputs, EchoValues
from ..parameters.registry_pettersen_detroit import build_registry_pettersen_detroit
from ..reports.backend import generate_report
from ..reports.report_templates import (
    get_report_templates,
    save_report_templates,
    ParagraphTemplate,
    ReportTemplate,
)

app = FastAPI(title="Echo Descriptor")

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

REGISTRY = None
PARAGRAPHS: Dict[str, ParagraphTemplate] | None = None
REPORTS: Dict[str, ReportTemplate] | None = None


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def active_config_dir() -> Path:
    return (repo_root() / "config").resolve()


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


@app.on_event("startup")
def _startup() -> None:
    global REGISTRY, PARAGRAPHS, REPORTS
    ensure_bootstrap_tree()
    REGISTRY = build_registry_pettersen_detroit()
    PARAGRAPHS, REPORTS = get_report_templates()


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
    selected_report_id: str,
    weight_kg: Any,
    height_cm: Any,
    raw_vals: Dict[str, float],
    report: str,
    error: str,
) -> HTMLResponse:
    assert REGISTRY is not None
    assert PARAGRAPHS is not None
    assert REPORTS is not None

    ui = load_param_ui()
    all_items = build_param_items()
    params_visible, params_hidden = split_and_sort_params(all_items, ui)

    # report list do selecta
    reports_list = list(REPORTS.values())
    reports_list.sort(key=lambda r: r.id)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "active_tab": active_tab,
            "params_visible": params_visible,
            "params_hidden": params_hidden,
            "param_items_all": all_items,
            "param_ui": ui,
            "reports_list": reports_list,
            "selected_report_id": selected_report_id,
            # Editor needs full data (JS will render it)
            "editor_paragraphs": [vars(PARAGRAPHS[k]) for k in sorted(PARAGRAPHS.keys())],
            "editor_reports": [
                {"id": r.id, "title": r.title, "paragraph_ids": r.paragraph_ids}
                for r in sorted(REPORTS.values(), key=lambda x: x.id)
            ],
            "weight_kg": weight_kg,
            "height_cm": height_cm,
            "raw_vals": raw_vals,
            "report": report,
            "error": error,
        },
    )


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    assert REPORTS is not None

    tab = str(request.query_params.get("tab") or "params").strip().lower()
    if tab not in {"params", "template", "settings"}:
        tab = "params"

    default_report_id = next(iter(REPORTS.keys()))
    return _render_index(
        request,
        active_tab=tab,
        selected_report_id=default_report_id,
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
    assert PARAGRAPHS is not None
    assert REPORTS is not None

    form = await request.form()

    weight_kg = _safe_float(form.get("weight_kg"))
    height_cm = _safe_float(form.get("height_cm"))

    selected_report_id = str(form.get("report_id") or "").strip()
    if not selected_report_id or selected_report_id not in REPORTS:
        selected_report_id = next(iter(REPORTS.keys()))

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
        tpl = REPORTS[selected_report_id]
        report = generate_report(patient=patient, raw=raw, registry=REGISTRY, template=tpl, paragraphs=PARAGRAPHS)

    return _render_index(
        request,
        active_tab="params",
        selected_report_id=selected_report_id,
        weight_kg="" if weight_kg is None else weight_kg,
        height_cm="" if height_cm is None else height_cm,
        raw_vals=raw_vals,
        report=report,
        error=error,
    )


# -----------------------
# TEMPLATE EDITOR API
# -----------------------

@app.get("/api/templates/v2")
def api_get_templates_v2():
    assert PARAGRAPHS is not None
    assert REPORTS is not None
    return {
        "paragraphs": [vars(PARAGRAPHS[k]) for k in sorted(PARAGRAPHS.keys())],
        "reports": [
            {"id": r.id, "title": r.title, "paragraph_ids": r.paragraph_ids}
            for r in sorted(REPORTS.values(), key=lambda x: x.id)
        ],
    }


@app.post("/api/templates/v2/save")
def api_save_templates_v2(payload: Dict[str, Any] = Body(...)):
    """
    payload:
      { paragraphs: [{id,label,description,text}, ...],
        reports: [{id,title,paragraph_ids:[...]}, ...] }
    """
    global PARAGRAPHS, REPORTS

    par_in = payload.get("paragraphs")
    rep_in = payload.get("reports")
    if not isinstance(par_in, list) or not isinstance(rep_in, list):
        return JSONResponse({"ok": False, "error": "Invalid payload"}, status_code=400)

    paragraphs: Dict[str, ParagraphTemplate] = {}
    for it in par_in:
        if not isinstance(it, dict):
            continue
        pid = str(it.get("id", "")).strip()
        if not pid:
            continue
        label = str(it.get("label", pid)).strip()
        desc = str(it.get("description", "") or "").strip()
        text = str(it.get("text", "") or "").strip()
        if not text:
            continue
        paragraphs[pid] = ParagraphTemplate(id=pid, label=label, description=desc, text=text)

    reports: Dict[str, ReportTemplate] = {}
    for it in rep_in:
        if not isinstance(it, dict):
            continue
        rid = str(it.get("id", "")).strip()
        if not rid:
            continue
        title = str(it.get("title", rid)).strip()
        pids = it.get("paragraph_ids", [])
        if not isinstance(pids, list):
            pids = []
        pids_norm = [str(x).strip() for x in pids if str(x).strip()]
        reports[rid] = ReportTemplate(id=rid, title=title, paragraph_ids=pids_norm)

    if not paragraphs or not reports:
        return JSONResponse({"ok": False, "error": "Must have at least 1 paragraph and 1 report"}, status_code=400)

    # persist
    save_report_templates(paragraphs, reports)

    # update in-memory for current process
    PARAGRAPHS = paragraphs
    REPORTS = reports

    return {"ok": True}

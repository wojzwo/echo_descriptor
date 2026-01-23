# echo_desc/web/webapp.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import json

from fastapi import FastAPI, Body, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..config.io import ensure_bootstrap_tree, ensure_bootstrap_file, load_yaml, save_yaml
from ..model import PatientInputs, EchoValues
from ..parameters.registry_pettersen_detroit import build_registry_pettersen_detroit
from ..reports.backend import build_context
from ..reports.templating import TemplateRenderer
from ..zscore_calc import ZScoreCalculator

from .templates_store import (
    ensure_nonempty_reports,
    build_reports_map,
    load_templates,
    validate_templates,
    save_templates,
)

app = FastAPI(title="Echo Descriptor")

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

REGISTRY = None


# -----------------------
# Param UI (settings tab) via config/io SSOT
# -----------------------
def param_ui_path():
    # env override is handled inside ensure_bootstrap_file via ConfigPaths.resolve()
    return ensure_bootstrap_file("web/parameters_ui.yaml")


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
        items.append(
            {"name": name, "label": name, "description": "" if desc is None else str(desc)}
        )
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


# -----------------------
# Startup
# -----------------------
@app.on_event("startup")
def _startup() -> None:
    global REGISTRY
    ensure_bootstrap_tree()
    REGISTRY = build_registry_pettersen_detroit()
    # template store bootstraps lazily via ensure_bootstrap_file()


# -----------------------
# Helpers
# -----------------------
def _safe_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip()
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def _load_templates_for_ui() -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Returns: doc, reports_map, templates_list
    Ensures at least one report exists (safe default for <select>).
    """
    doc = ensure_nonempty_reports()
    reports_map = build_reports_map(doc)
    templates_list = list(reports_map.values())
    return doc, reports_map, templates_list


def _default_template_selection(reports_map: Dict[str, Dict[str, Any]]) -> Tuple[str, Set[str]]:
    if not reports_map:
        return "", set()

    default_template_id = next(iter(reports_map.keys()))
    pars = reports_map[default_template_id].get("paragraphs", [])
    if not isinstance(pars, list):
        pars = []

    default_paragraph_ids: Set[str] = set()
    for p in pars:
        if isinstance(p, dict):
            pid = str(p.get("id", "")).strip()
            if pid:
                default_paragraph_ids.add(pid)

    return default_template_id, default_paragraph_ids


def _render_index(
    request: Request,
    *,
    active_tab: str,
    selected_template_id: str,
    selected_paragraph_ids: Set[str],
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

    doc, reports_map, templates_list = _load_templates_for_ui()

    if not selected_template_id or selected_template_id not in reports_map:
        selected_template_id, selected_paragraph_ids = _default_template_selection(reports_map)

    templates_json = json.dumps(doc, ensure_ascii=False)

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
            "templates_json": templates_json,
        },
    )


# -----------------------
# Routes
# -----------------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    tab = str(request.query_params.get("tab") or "params").strip().lower()
    if tab not in {"params", "template", "settings"}:
        tab = "params"

    _, reports_map, _ = _load_templates_for_ui()
    default_template_id, default_paragraph_ids = _default_template_selection(reports_map)

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

    save_yaml(param_ui_path(), {"params": out_list})
    return RedirectResponse(url="/?tab=settings", status_code=303)


@app.get("/api/settings/parameters_ui")
def api_settings_parameters_ui():
    """
    Returns current server-side settings as a normalized list:
      { ok: true, params: [ {name, enabled, order} ... ] }
    """
    ui = load_param_ui()

    # normalize (list, deterministic order by name)
    out: List[Dict[str, Any]] = []
    for name in sorted(ui.keys()):
        st = ui.get(name, {})
        out.append(
            {
                "name": name,
                "enabled": bool(st.get("enabled", True)),
                "order": int(st.get("order", 9999)),
            }
        )

    return {"ok": True, "params": out}


@app.post("/generate", response_class=HTMLResponse)
async def generate_one_page(request: Request):
    assert REGISTRY is not None
    form = await request.form()

    weight_kg = _safe_float(form.get("weight_kg"))
    height_cm = _safe_float(form.get("height_cm"))

    _, reports_map, _ = _load_templates_for_ui()

    selected_template_id = str(form.get("template_id") or "").strip()
    if not selected_template_id or selected_template_id not in reports_map:
        selected_template_id, _ = _default_template_selection(reports_map)

    # optional (if you ever re-add checkbox list)
    paragraph_ids: List[str] = list(form.getlist("paragraph_ids"))
    selected_paragraph_ids: Set[str] = {str(x).strip() for x in paragraph_ids if str(x).strip()}

    raw_vals: Dict[str, float] = {}
    for pname in REGISTRY.names():
        v = _safe_float(form.get(pname))
        if v is not None:
            raw_vals[pname] = v

    if weight_kg is None or height_cm is None:
        return _render_index(
            request,
            active_tab="params",
            selected_template_id=selected_template_id,
            selected_paragraph_ids=selected_paragraph_ids,
            weight_kg="" if weight_kg is None else weight_kg,
            height_cm="" if height_cm is None else height_cm,
            raw_vals=raw_vals,
            report="",
            error="Nieprawidłowa masa lub wzrost.",
        )

    patient = PatientInputs(weight_kg=weight_kg, height_cm=height_cm)
    raw = EchoValues(values=raw_vals)

    base = reports_map[selected_template_id]
    base_pars = base.get("paragraphs", [])
    if not isinstance(base_pars, list):
        base_pars = []

    chosen_pars = (
        [p for p in base_pars if isinstance(p, dict) and str(p.get("id", "")).strip() in selected_paragraph_ids]
        if selected_paragraph_ids
        else [p for p in base_pars if isinstance(p, dict)]
    )

    calc = ZScoreCalculator(REGISTRY)
    z = calc.compute(raw, patient.bsa)
    ctx = build_context(patient, raw, z)
    renderer = TemplateRenderer()

    rendered: List[str] = []
    for p in chosen_pars:
        rendered.append(renderer.render(str(p.get("text", "") or ""), ctx))

    return _render_index(
        request,
        active_tab="params",
        selected_template_id=selected_template_id,
        selected_paragraph_ids=selected_paragraph_ids,
        weight_kg=weight_kg,
        height_cm=height_cm,
        raw_vals=raw_vals,
        report="\n\n".join(rendered),
        error="",
    )


# -----------------------
# API: Template Editor
# -----------------------
@app.get("/api/templates/load")
def api_templates_load():
    return load_templates()


@app.post("/api/templates/save")
def api_templates_save(payload: Dict[str, Any] = Body(...)):
    ok, err = validate_templates(payload)
    if not ok:
        return JSONResponse({"ok": False, "error": err}, status_code=400)

    save_templates(payload)
    return {"ok": True}

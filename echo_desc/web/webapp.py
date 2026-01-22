from __future__ import annotations

from typing import Dict, Any, List, Tuple
from pathlib import Path

from fastapi import FastAPI, Request, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from ..config.io import ensure_bootstrap_tree, load_yaml, save_yaml, ConfigPaths
from ..model import PatientInputs, EchoValues
from ..parameters.registry_pettersen_detroit import build_registry_pettersen_detroit
from ..reports.backend import generate_report
from ..reports.report_templates import get_report_templates, filter_template

app = FastAPI(title="Echo Descriptor")

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

REGISTRY = None
TEMPLATES = None


# -----------------------------
# UI config (repo-local / env override via ConfigPaths)
# -----------------------------
def param_ui_path() -> Path:
    # respects ECHO_DESC_CONFIG_DIR override + repo-local default
    return ConfigPaths.resolve().file("web/parameters_ui.yaml")


def _as_bool(x: Any, default: bool = True) -> bool:
    if x is None:
        return default
    if isinstance(x, bool):
        return x
    if isinstance(x, (int, float)):
        return bool(x)
    s = str(x).strip().lower()
    if s in ("true", "1", "yes", "y", "on"):
        return True
    if s in ("false", "0", "no", "n", "off"):
        return False
    return default


def _as_int(x: Any, default: int = 9999) -> int:
    try:
        return int(str(x).strip())
    except Exception:
        return default


def load_param_ui() -> Dict[str, Dict[str, Any]]:
    """
    Returns mapping:
      { "LVEDD": {"enabled": bool, "order": int}, ... }

    If missing file -> empty dict (means: show all, natural order).
    """
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
        enabled = _as_bool(item.get("enabled", True), default=True)
        order = _as_int(item.get("order", 9999), default=9999)
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
    """
    Returns (visible, hidden), both sorted by order then name.
    Default if not in ui: enabled=True, order=registry order * 10.
    """
    default_order: Dict[str, int] = {}
    for i, it in enumerate(param_items):
        default_order[it["name"]] = (i + 1) * 10

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


# -----------------------------
# App lifecycle
# -----------------------------
@app.on_event("startup")
def _startup() -> None:
    global REGISTRY, TEMPLATES
    ensure_bootstrap_tree()
    REGISTRY = build_registry_pettersen_detroit()
    TEMPLATES = get_report_templates()


def _safe_float(x: Any) -> float | None:
    s = str(x).strip()
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


# -----------------------------
# Routes
# -----------------------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    assert REGISTRY is not None
    assert TEMPLATES is not None

    ui = load_param_ui()
    all_items = build_param_items()
    params_visible, params_hidden = split_and_sort_params(all_items, ui)

    default_template_id = next(iter(TEMPLATES.keys()))
    default_paragraph_ids = [p.id for p in TEMPLATES[default_template_id].paragraphs]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "params_visible": params_visible,
            "params_hidden": params_hidden,
            "param_items_all": all_items,  # Settings tab
            "param_ui": ui,                # Settings tab values
            "templates_list": list(TEMPLATES.values()),
            "selected_template_id": default_template_id,
            "selected_paragraph_ids": set(default_paragraph_ids),
            "weight_kg": "",
            "height_cm": "",
            "raw_vals": {},
            "report": "",
            "error": "",
        },
    )


@app.post("/generate", response_class=HTMLResponse)
async def generate_one_page(request: Request):
    assert REGISTRY is not None
    assert TEMPLATES is not None

    form = await request.form()

    weight_kg = _safe_float(form.get("weight_kg"))
    height_cm = _safe_float(form.get("height_cm"))

    selected_template_id = str(form.get("template_id") or "").strip()
    if not selected_template_id or selected_template_id not in TEMPLATES:
        selected_template_id = next(iter(TEMPLATES.keys()))

    paragraph_ids: List[str] = list(form.getlist("paragraph_ids"))

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

        base_template = TEMPLATES[selected_template_id]
        chosen_template = filter_template(base_template, paragraph_ids)

        report = generate_report(
            patient=patient,
            raw=raw,
            registry=REGISTRY,
            template=chosen_template,
        )

    # re-render with current UI config
    ui = load_param_ui()
    all_items = build_param_items()
    params_visible, params_hidden = split_and_sort_params(all_items, ui)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "params_visible": params_visible,
            "params_hidden": params_hidden,
            "param_items_all": all_items,
            "param_ui": ui,
            "templates_list": list(TEMPLATES.values()),
            "selected_template_id": selected_template_id,
            "selected_paragraph_ids": set(paragraph_ids),
            "weight_kg": "" if weight_kg is None else weight_kg,
            "height_cm": "" if height_cm is None else height_cm,
            "raw_vals": raw_vals,
            "report": report,
            "error": error,
        },
    )


@app.post("/api/settings/save")
def api_save_settings(payload: Dict[str, Any] = Body(...)):
    """
    payload:
      { "params": [ {"name": "...", "enabled": true/false, "order": 10}, ... ] }

    Normalizujemy zapis tak, żeby plik miał stabilną, pełną listę parametrów z registry.
    """
    assert REGISTRY is not None

    params = payload.get("params")
    if not isinstance(params, list):
        return JSONResponse({"ok": False, "error": "Invalid payload: params must be a list"}, status_code=400)

    # Build quick lookup from payload
    in_map: Dict[str, Dict[str, Any]] = {}
    for item in params:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        in_map[name] = {
            "enabled": _as_bool(item.get("enabled", True), default=True),
            "order": _as_int(item.get("order", 9999), default=9999),
        }

    # Normalize: one entry per registry param, in registry order (stable)
    out_list: List[Dict[str, Any]] = []
    for i, n in enumerate(REGISTRY.names()):
        default_order = (i + 1) * 10
        st = in_map.get(n, {})
        enabled = _as_bool(st.get("enabled", True), default=True)
        order = _as_int(st.get("order", default_order), default=default_order)
        out_list.append({"name": n, "enabled": enabled, "order": order})

    doc = {"params": out_list}
    p = param_ui_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    save_yaml(p, doc)

    return {"ok": True, "path": str(p)}

from __future__ import annotations

from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from ..config.io import ensure_bootstrap_tree, load_yaml, save_yaml
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


def repo_root() -> Path:
    # echo_desc/web/webapp.py -> repo_root
    return Path(__file__).resolve().parents[2]


def active_config_dir() -> Path:
    return (repo_root() / "config").resolve()


def param_ui_path() -> Path:
    return (active_config_dir() / "web" / "parameters_ui.yaml").resolve()


def load_param_ui() -> Dict[str, Dict[str, Any]]:
    """
    Returns mapping:
      { "LVEDD": {"enabled": bool, "order": int}, ... }

    If file missing/invalid -> empty dict (means defaults: show all + registry order).
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
            {
                "name": name,
                "label": name,
                "description": "" if desc is None else str(desc),
            }
        )
    return items


def split_and_sort_params(
    param_items: List[Dict[str, Any]],
    ui: Dict[str, Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Returns (visible, hidden), both sorted by (order, name).
    Default if not in ui: enabled=True, order=(registry_position*10).
    """
    default_order: Dict[str, int] = {
        it["name"]: (i + 1) * 10 for i, it in enumerate(param_items)
    }

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
    global REGISTRY, TEMPLATES
    ensure_bootstrap_tree()
    REGISTRY = build_registry_pettersen_detroit()
    TEMPLATES = get_report_templates()


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
    assert TEMPLATES is not None

    ui = load_param_ui()
    all_items = build_param_items()
    params_visible, params_hidden = split_and_sort_params(all_items, ui)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "active_tab": active_tab,
            "params_visible": params_visible,
            "params_hidden": params_hidden,
            "param_items_all": all_items,
            "param_ui": ui,
            "templates_list": list(TEMPLATES.values()),
            "selected_template_id": selected_template_id,
            "selected_paragraph_ids": selected_paragraph_ids,
            "weight_kg": weight_kg,
            "height_cm": height_cm,
            "raw_vals": raw_vals,
            "report": report,
            "error": error,
        },
    )


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    assert TEMPLATES is not None
    tab = str(request.query_params.get("tab") or "params").strip().lower()
    if tab not in {"params", "template", "settings"}:
        tab = "params"

    default_template_id = next(iter(TEMPLATES.keys()))
    default_paragraph_ids = {p.id for p in TEMPLATES[default_template_id].paragraphs}

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
    """
    Saves UI settings into ./config/web/parameters_ui.yaml (repo-local).
    """
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

    # wracamy na settings tab
    return RedirectResponse(url="/?tab=settings", status_code=303)


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

        base_template = TEMPLATES[selected_template_id]
        chosen_template = filter_template(base_template, paragraph_ids)

        report = generate_report(
            patient=patient,
            raw=raw,
            registry=REGISTRY,
            template=chosen_template,
        )

    # po generacji zostajemy w tabie params (najbardziej praktyczne)
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

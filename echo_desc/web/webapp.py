from __future__ import annotations

from typing import Dict, Any, List
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..config.io import ensure_bootstrap_tree
from ..model import PatientInputs, EchoValues
from ..parameters.registry_pettersen_detroit import build_registry_pettersen_detroit
from ..reports.backend import generate_report
from ..reports.report_templates import get_report_templates, filter_template

app = FastAPI(title="Echo Descriptor")

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Filled on startup
REGISTRY = None
TEMPLATES = None


@app.on_event("startup")
def _startup() -> None:
    """
    1) Create local editable config files (if missing) by copying defaults.
    2) Load registry + templates from LOCAL config.
    """
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


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    assert REGISTRY is not None
    assert TEMPLATES is not None

    default_template_id = next(iter(TEMPLATES.keys()))
    default_paragraph_ids = [p.id for p in TEMPLATES[default_template_id].paragraphs]

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "param_names": REGISTRY.names(),
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

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "param_names": REGISTRY.names(),
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

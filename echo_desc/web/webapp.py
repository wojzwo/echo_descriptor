# echo_desc/web/webapp.py
from __future__ import annotations

from typing import Dict
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..model import PatientInputs, EchoValues
from ..parameters.registry_pettersen_detroit import build_registry_pettersen_detroit
from ..reports.report_templates import build_report_template_default
from ..reports.backend import generate_report

app = FastAPI(title="Echo Z-score")

BASE_DIR = Path(__file__).resolve().parent              # .../echo_desc
TEMPLATES_DIR = BASE_DIR / "templates"                 # .../echo_desc/templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

REGISTRY = build_registry_pettersen_detroit()
REPORT_TEMPLATE = build_report_template_default()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    # szybki sanity: jak templates dir nie istnieje, zwróć czytelny komunikat
    if not TEMPLATES_DIR.exists():
        return HTMLResponse(
            f"<h1>Templates dir not found</h1><pre>{TEMPLATES_DIR}</pre>",
            status_code=500,
        )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "param_names": REGISTRY.names(),
        },
    )


@app.post("/generate_async", response_class=HTMLResponse)
async def generate_async(request: Request):
    form = await request.form()

    try:
        weight_kg = float(str(form.get("weight_kg", "")).strip())
        height_cm = float(str(form.get("height_cm", "")).strip())
    except Exception:
        return templates.TemplateResponse(
            "result.html",
            {"request": request, "error": "Nieprawidłowa masa lub wzrost.", "report": ""},
        )

    patient = PatientInputs(weight_kg=weight_kg, height_cm=height_cm)

    raw_vals: Dict[str, float] = {}
    for pname in REGISTRY.names():
        s = str(form.get(pname, "")).strip()
        if not s:
            continue
        try:
            raw_vals[pname] = float(s)
        except Exception:
            pass

    raw = EchoValues(values=raw_vals)

    report = generate_report(patient, raw, REGISTRY, REPORT_TEMPLATE)

    return templates.TemplateResponse(
        "result.html",
        {"request": request, "error": "", "report": report},
    )
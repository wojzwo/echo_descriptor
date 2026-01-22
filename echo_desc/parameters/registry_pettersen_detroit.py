# echo_desc/parameters/registry_pettersen_detroit.py
from __future__ import annotations
from typing import Dict

from .base import Parameter, ParamRegistry

def build_registry_pettersen_detroit() -> ParamRegistry:
    """
    Pettersen MD et al. / Detroit Data (hardcoded):
    Parameter -> alpha, mean, sd.

    NOTE:
    - Raw values dict must use EXACTLY these keys.
    - alpha=0 => no BSA scaling (value/(BSA**0) == value).
    """
    params: Dict[str, Parameter] = {
        "MVAP":     Parameter(name="MVAP",     alpha=0.50, mean=2.31,  sd=0.24, description="Mitral valve annulus (AP)"),
        "MVLAT":    Parameter(name="MVLAT",    alpha=0.50, mean=2.23,  sd=0.22, description="Mitral valve annulus (LAT)"),
        "MVA":      Parameter(name="MVA",      alpha=1.00, mean=4.06,  sd=0.68, description="Mitral valve area"),

        "TVAP":     Parameter(name="TVAP",     alpha=0.50, mean=2.36,  sd=0.28, description="Tricuspid valve annulus (AP)"),
        "TVLAT":    Parameter(name="TVLAT",    alpha=0.50, mean=2.36,  sd=0.29, description="Tricuspid valve annulus (LAT)"),
        "TVA":      Parameter(name="TVA",      alpha=1.00, mean=4.39,  sd=0.83, description="Tricuspid valve area"),

        "ANN":      Parameter(name="ANN",      alpha=0.50, mean=1.48,  sd=0.14, description="Aortic annulus"),
        "ROOT":     Parameter(name="ROOT",     alpha=0.50, mean=2.06,  sd=0.18, description="Aortic root"),
        "STJ":      Parameter(name="STJ",      alpha=0.50, mean=1.69,  sd=0.16, description="Sinotubular junction"),
        "AAO":      Parameter(name="AAO",      alpha=0.50, mean=1.79,  sd=0.18, description="Ascending aorta"),

        "ARCHPROX": Parameter(name="ARCHPROX", alpha=0.50, mean=1.53,  sd=0.23, description="Aortic arch proximal"),
        "ARCHDIST": Parameter(name="ARCHDIST", alpha=0.50, mean=1.36,  sd=0.19, description="Aortic arch distal"),
        "ISTH":     Parameter(name="ISTH",     alpha=0.50, mean=1.25,  sd=0.18, description="Aortic isthmus"),

        "LMCA":     Parameter(name="LMCA",     alpha=0.45, mean=2.95,  sd=0.57, description="Left main coronary artery"),
        "LAD":      Parameter(name="LAD",      alpha=0.45, mean=1.90,  sd=0.34, description="Left anterior descending artery"),
        "RCA":      Parameter(name="RCA",      alpha=0.45, mean=2.32,  sd=0.55, description="Right coronary artery"),

        "PVSAX":    Parameter(name="PVSAX",    alpha=0.50, mean=1.91,  sd=0.24, description="Pulmonary valve (SAX)"),
        "PVLAX":    Parameter(name="PVLAX",    alpha=0.50, mean=2.01,  sd=0.28, description="Pulmonary valve (LAX)"),

        "MPA":      Parameter(name="MPA",      alpha=0.50, mean=1.82,  sd=0.24, description="Main pulmonary artery"),
        "RPA":      Parameter(name="RPA",      alpha=0.50, mean=1.07,  sd=0.18, description="Right pulmonary artery"),
        "LPA":      Parameter(name="LPA",      alpha=0.50, mean=1.10,  sd=0.18, description="Left pulmonary artery"),

        "LVEDD":    Parameter(name="LVEDD",    alpha=0.45, mean=3.89,  sd=0.33, description="LV end-diastolic diameter"),
        "LVPWT":    Parameter(name="LVPWT",    alpha=0.40, mean=0.57,  sd=0.09, description="LV posterior wall thickness (diastole)"),
        "LVST":     Parameter(name="LVST",     alpha=0.40, mean=0.58,  sd=0.09, description="LV septal thickness (diastole)"),

        "LVEDL":    Parameter(name="LVEDL",    alpha=0.45, mean=6.31,  sd=0.46, description="LV end-diastolic length"),
        "LVEDLEPI": Parameter(name="LVEDLEPI", alpha=0.45, mean=6.87,  sd=0.45, description="LV end-diastolic length (epi)"),

        "LVEDA":    Parameter(name="LVEDA",    alpha=0.90, mean=11.91, sd=1.89, description="LV end-diastolic area"),
        "LVEDAEPI": Parameter(name="LVEDAEPI", alpha=0.90, mean=20.00, sd=2.59, description="LV end-diastolic area (epi)"),

        "LVEDV":    Parameter(name="LVEDV",    alpha=1.30, mean=62.02, sd=11.94, description="LV end-diastolic volume"),
        "LVEDVEPI": Parameter(name="LVEDVEPI", alpha=1.30, mean=113.14, sd=17.85, description="LV end-diastolic volume (epi)"),

        "LVM":      Parameter(name="LVM",      alpha=1.25, mean=53.02, sd=9.06, description="LV mass"),

        "LVMTV":    Parameter(name="LVMTV",    alpha=0.00, mean=0.88,  sd=0.16, description="LVMTV (alpha=0)"),
        "LVTTD":    Parameter(name="LVTTD",    alpha=0.00, mean=0.15,  sd=0.03, description="LVTTD (alpha=0)"),
        "LVSI":     Parameter(name="LVSI",     alpha=0.00, mean=1.63,  sd=0.17, description="LV sphericity index (alpha=0)"),
    }

    return ParamRegistry(params)

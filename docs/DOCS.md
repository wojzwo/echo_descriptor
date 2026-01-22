# Echo Descriptor - Project Documentation

DOCS CAN BE DEPRECATED ARE NOT UPDATED CONSISTENTLY

## Overview

**Echo Descriptor** is an automated descriptor generator for pediatric echocardiography procedures with Z-score calculations. It uses the Pettersen MD et al. (Detroit Data) norms to calculate Z-scores for various cardiac measurements based on patient's body surface area (BSA).

The application provides a web interface where you can input patient data (weight, height) and echocardiography measurements, then automatically generate a medical report with calculated Z-scores.

---

## Project Structure

```
echo_descriptor/
├── echo_desc/                  # Main application package
│   ├── __init__.py            # Package initialization
│   ├── __main__.py            # Entry point for CLI command
│   ├── model.py               # Core data models
│   ├── core_math.py           # Mathematical utilities (BSA, Z-score)
│   ├── zscore_calc.py         # Z-score calculator engine
│   ├── parameters/            # Parameter definitions and registry
│   │   ├── __init__.py
│   │   ├── base.py           # Base Parameter class and ParamRegistry
│   │   └── registry_pettersen_detroit.py  # Detroit Data parameters
│   ├── reports/              # Report generation system
│   │   ├── __init__.py
│   │   ├── backend.py        # Report generation logic
│   │   ├── templating.py     # Template rendering engine
│   │   └── report_templates.py  # Report template definitions
│   └── web/                  # Web application
│       ├── __init__.py
│       ├── webapp.py         # FastAPI web server
│       └── templates/        # HTML templates
│           ├── index.html    # Main form page
│           └── result.html   # Report display page
├── pyproject.toml            # Project configuration and dependencies
├── requirements.txt          # Python dependencies list
├── README.md                 # Project overview and setup instructions
└── DOCS.md                   # This documentation file
```


REF FILE: CONFIGURATION_SYSTEM.md 

---

## File-by-File Breakdown

### Root Directory Files

#### `pyproject.toml`
**Purpose:** Project configuration file using the modern Python packaging standard.

**Contents:**
- Project metadata (name, version, description, authors)
- Python version requirement (>=3.11)
- Dependencies (FastAPI, Uvicorn, Jinja2)
- CLI script definition (`echo_desc` command)
- Build system configuration (Hatchling)
- Package specification

**Key sections:**
- `[project]`: Basic project info and dependencies
- `[project.scripts]`: Defines the `echo_desc` CLI command
- `[build-system]`: Specifies how to build the package
- `[tool.hatch.build.targets.wheel]`: Tells the build system where the package code is

#### `requirements.txt`
**Purpose:** Simple list of Python package dependencies for reference.

**Note:** The actual dependencies are managed in `pyproject.toml`. This file is kept for convenience.

#### `README.md`
**Purpose:** Quick start guide and project overview for developers.

**Contains:**
- Project description
- Installation instructions
- How to run the application
- Project structure overview
- Basic usage examples

---

### Core Application Package (`echo_desc/`)

#### `echo_desc/__init__.py`
**Purpose:** Makes `echo_desc` a Python package.

**Contents:** Currently empty (just a marker file).

#### `echo_desc/__main__.py`
**Purpose:** Entry point when running the application via `uv run echo_desc` command.

**What it does:**
1. Imports `uvicorn` (ASGI server)
2. Reads environment variables:
   - `ECHOZ_HOST` (default: 127.0.0.1)
   - `ECHOZ_PORT` (default: 8000)
3. Launches the web application with hot-reload enabled

**Usage:** This is automatically called when you run `uv run echo_desc`.

#### `echo_desc/model.py`
**Purpose:** Defines core data structures used throughout the application.

**Classes:**

1. **`PatientInputs`**
   - Dataclass storing patient measurements
   - Fields:
     - `weight_kg: float` - Patient weight in kilograms
     - `height_cm: float` - Patient height in centimeters
   - Property:
     - `bsa: float` - Calculated body surface area (computed automatically)
   - Used for: Storing patient data and calculating BSA

2. **`EchoValues`**
   - Dataclass storing echocardiography measurements
   - Fields:
     - `values: Dict[str, float]` - Dictionary of measurement name → value
   - Methods:
     - `get(key: str) -> Optional[float]` - Safely retrieve a measurement value
   - Used for: Storing all the cardiac measurements (e.g., LVEDD, ROOT, MPA, etc.)

#### `echo_desc/core_math.py`
**Purpose:** Mathematical functions for BSA and Z-score calculations.

**Functions:**

1. **`calculate_bsa(weight_kg: float, height_cm: float) -> float`**
   - Calculates Body Surface Area using the Mosteller formula
   - Formula: `BSA = 0.024265 × (weight^0.5378) × (height^0.3964)`
   - Returns: BSA in square meters (m²)
   - Used by: `PatientInputs.bsa` property

2. **`calculate_z_score(value: float, bsa: float, alpha: float, mean: float, sd: float) -> float`**
   - Calculates Z-score for a measurement
   - Formula: `z = (value/BSA^alpha - mean) / sd`
   - Parameters:
     - `value`: The measured cardiac dimension (e.g., 2.5 cm)
     - `bsa`: Body surface area in m²
     - `alpha`: Scaling exponent (parameter-specific)
     - `mean`: Expected mean for normalized value
     - `sd`: Standard deviation
   - Returns: Z-score (how many standard deviations from the mean)
   - Raises: ValueError if SD is 0 or BSA ≤ 0

3. **`fmt_num(x: Any, ndigits: int = 2) -> str`**
   - Formats numbers for display
   - Handles None values (returns empty string)
   - Rounds floats to specified decimal places
   - Used for: Consistent number formatting in reports

#### `echo_desc/zscore_calc.py`
**Purpose:** Z-score calculation engine that processes all measurements.

**Classes:**

1. **`ZScoreCalculator`**
   - Main calculator class
   - Constructor: Takes a `ParamRegistry` with all parameter definitions
   - Method: `compute(raw: EchoValues, bsa: float) -> Dict[str, float]`
     - Input: Raw measurements and patient's BSA
     - Process: For each measurement in the registry, calculates its Z-score
     - Output: Dictionary with keys like `"LVEDD_z"`, `"ROOT_z"`, etc.
     - Handles missing values gracefully (skips them)
     - Handles calculation errors (returns NaN)

**Example:**
```python
calculator = ZScoreCalculator(registry)
raw = EchoValues({"LVEDD": 3.5, "ROOT": 2.1})
z_scores = calculator.compute(raw, bsa=0.85)
# Result: {"LVEDD_z": -0.45, "ROOT_z": 0.22}
```

---

### Parameters System (`echo_desc/parameters/`)

This directory defines all cardiac parameters and their normative data.

#### `echo_desc/parameters/__init__.py`
**Purpose:** Makes `parameters` a Python package.

#### `echo_desc/parameters/base.py`
**Purpose:** Base classes for the parameter system.

**Classes:**

1. **`Parameter`**
   - Frozen dataclass (immutable) representing one cardiac measurement parameter
   - Fields:
     - `name: str` - Parameter code (e.g., "LVEDD", "ROOT")
     - `alpha: float` - BSA scaling exponent
     - `mean: float` - Expected mean for normalized value
     - `sd: float` - Standard deviation
     - `description: Optional[str]` - Human-readable description
     - `unit: Optional[str]` - Measurement unit (e.g., "cm")
   - Method: `z_score(value: float, bsa: float) -> float`
     - Calculates Z-score for this specific parameter
     - Uses the `calculate_z_score` function from `core_math`

2. **`ParamRegistry`**
   - Container for all parameters
   - Stores parameters in a dictionary
   - Methods:
     - `get(name: str) -> Optional[Parameter]` - Retrieve parameter by name
     - `names() -> List[str]` - Get sorted list of all parameter names
   - Used for: Looking up parameter definitions during Z-score calculation

**Scaling (alpha) explained:**
- `alpha=0.5`: Parameter scales with square root of BSA (most common)
- `alpha=1.0`: Parameter scales linearly with BSA (areas)
- `alpha=0.45`: Custom scaling for specific parameters
- `alpha=0.0`: No BSA scaling (raw value)

#### `echo_desc/parameters/registry_pettersen_detroit.py`
**Purpose:** **THIS IS WHERE ALL THE NORMATIVE DATA IS DEFINED!**

**Function:**

**`build_registry_pettersen_detroit() -> ParamRegistry`**
- Creates and returns the complete parameter registry
- Contains 30+ cardiac parameters with Detroit Data norms
- Each parameter includes:
  - Code name (e.g., "MVAP", "LVEDD")
  - Alpha (scaling exponent)
  - Mean and SD values
  - Description

**Parameter Categories:**

1. **Mitral Valve:**
   - MVAP, MVLAT (annulus dimensions)
   - MVA (valve area)

2. **Tricuspid Valve:**
   - TVAP, TVLAT (annulus dimensions)
   - TVA (valve area)

3. **Aortic Valve and Root:**
   - ANN (annulus)
   - ROOT (aortic root)
   - STJ (sinotubular junction)
   - AAO (ascending aorta)

4. **Aortic Arch:**
   - ARCHPROX, ARCHDIST (proximal/distal arch)
   - ISTH (isthmus)

5. **Coronary Arteries:**
   - LMCA (left main)
   - LAD (left anterior descending)
   - RCA (right coronary artery)

6. **Pulmonary Valve:**
   - PVSAX, PVLAX (short/long axis views)

7. **Pulmonary Arteries:**
   - MPA (main)
   - RPA, LPA (right/left branches)

8. **Left Ventricle:**
   - LVEDD (end-diastolic diameter)
   - LVPWT (posterior wall thickness)
   - LVST (septal thickness)
   - LVEDL, LVEDLEPI (end-diastolic lengths)

**To add new parameters:** Edit this file and add a new Parameter definition to the dictionary.

---

### Reports System (`echo_desc/reports/`)

This directory handles report generation and templating.

#### `echo_desc/reports/__init__.py`
**Purpose:** Makes `reports` a Python package.

#### `echo_desc/reports/templating.py`
**Purpose:** Simple template rendering engine.

**Classes:**

1. **`TemplateRenderer`**
   - Custom template engine (not using Jinja2 for reports)
   - Supports placeholders: `{KEY}` and `{KEY:format}`
   - Examples:
     - `{BSA_m2}` → inserts BSA value
     - `{BSA_m2:.2f}` → inserts BSA rounded to 2 decimals
     - `{LVEDD_z:.2f}` → inserts LVEDD Z-score rounded to 2 decimals
   - Missing values: Replaced with `###BRAK PARAMETRU:KEY###`
   - Methods:
     - `render(text: str, ctx: Dict[str, Any]) -> str`
       - Takes template text and context dictionary
       - Returns rendered text with values filled in

**How it works:**
1. Uses regex to find all `{...}` patterns
2. Extracts key name and optional format specifier
3. Looks up key in context dictionary
4. Formats value if format specifier present
5. Replaces placeholder with formatted value

#### `echo_desc/reports/report_templates.py`
**Purpose:** **THIS IS WHERE REPORT DESCRIPTIONS ARE DEFINED!**

**Classes:**

1. **`ParagraphTemplate`**
   - Dataclass representing one paragraph in a report
   - Fields:
     - `id: str` - Paragraph identifier (e.g., "bsa", "lv_dims")
     - `text: str` - Template text with placeholders

2. **`ReportTemplate`**
   - Dataclass representing a complete report
   - Fields:
     - `id: str` - Template identifier
     - `paragraphs: List[ParagraphTemplate]` - List of paragraphs
   - Method: `render(renderer: TemplateRenderer, ctx: Dict[str, Any]) -> str`
     - Renders all paragraphs and joins them with double newlines

**Function:**

**`build_report_template_default() -> ReportTemplate`**
- Creates the default echocardiography report template
- **TO CUSTOMIZE REPORTS: Edit this function!**

**Current template paragraphs:**

1. **"norms"** - Reference citation
   - States which normative data is used (Pettersen MD et al., Detroit Data)

2. **"bsa"** - Body surface area
   - Shows calculated BSA: `BSA= {BSA_m2:.2f} m2.`

3. **"lv_dims"** - Left ventricle dimensions
   - Reports LVEDD, LVST, LVPWT with Z-scores
   - Template: `LVEDD= {LVEDD:.2f} (z= {LVEDD_z:.2f}), ...`

4. **"aorta"** - Aortic measurements
   - Reports ANN, ROOT, STJ, AAO with Z-scores

5. **"pa"** - Pulmonary artery measurements
   - Reports MPA, RPA, LPA with Z-scores

6. **"conclusion"** - Final conclusion
   - Currently hardcoded conclusion text
   - **TO DO:** Make this dynamic based on Z-scores

**To modify report content:**
1. Edit the paragraph templates in this function
2. Add new ParagraphTemplate objects for new sections
3. Use `{PARAMETER}` for raw values and `{PARAMETER_z}` for Z-scores
4. Use format specifiers like `:.2f` for decimal places

#### `echo_desc/reports/backend.py`
**Purpose:** Orchestrates the report generation process.

**Functions:**

1. **`build_context(patient: PatientInputs, raw: EchoValues, zscores: Dict[str, float]) -> Dict[str, Any]`**
   - Creates the context dictionary for template rendering
   - Combines:
     - BSA value
     - All raw measurements (LVEDD, ROOT, etc.)
     - All Z-scores (LVEDD_z, ROOT_z, etc.)
   - Returns: Single dictionary with all available values

2. **`generate_report(patient: PatientInputs, raw: EchoValues, registry: ParamRegistry, template: ReportTemplate) -> str`**
   - **Main function for report generation**
   - Steps:
     1. Creates ZScoreCalculator
     2. Computes all Z-scores
     3. Builds context dictionary
     4. Renders template with context
   - Returns: Complete report as string

**This is the "glue" that connects all parts:**
```
Patient data + Raw values → ZScoreCalculator → Z-scores
                                                    ↓
                                         build_context()
                                                    ↓
                                    Template + Context → Report
```

---

### Web Application (`echo_desc/web/`)

#### `echo_desc/web/__init__.py`
**Purpose:** Makes `web` a Python package.

#### `echo_desc/web/webapp.py`
**Purpose:** FastAPI web server application.

**Framework:** FastAPI (modern Python web framework)

**Global Objects:**
- `app`: FastAPI application instance
- `templates`: Jinja2Templates for HTML rendering
- `REGISTRY`: Parameter registry (loaded once at startup)
- `REPORT_TEMPLATE`: Report template (loaded once at startup)

**Routes:**

1. **`GET /`** - Main page
   - Function: `index(request: Request)`
   - Renders: `index.html`
   - Passes: List of all parameter names for the form
   - Purpose: Display the input form

2. **`POST /generate_async`** - Report generation
   - Function: `generate_async(request: Request)`
   - Receives: Form data with weight, height, and measurements
   - Process:
     1. Extracts weight and height from form
     2. Creates PatientInputs object
     3. Extracts all parameter values from form
     4. Creates EchoValues object
     5. Generates report using `generate_report()`
     6. Renders result page
   - Error handling: Shows error message if weight/height invalid
   - Renders: `result.html`
   - Purpose: Process form and show generated report

**Form processing:**
- All parameter fields are optional (can be empty)
- Only numeric values are accepted
- Invalid numbers are silently skipped
- Parameter names must match registry exactly

#### `echo_desc/web/templates/index.html`
**Purpose:** Main input form page.

**Layout:**
1. **Patient data section:**
   - Weight input (kg)
   - Height input (cm)
   - Both required fields

2. **Parameters section:**
   - Dynamically generated from `param_names`
   - One input field per parameter
   - All optional
   - Uses parameter code as label (e.g., "LVEDD", "ROOT")

**Styling:** Minimal CSS with grid layout for clean appearance.

**Form submission:** Posts to `/generate_async`

#### `echo_desc/web/templates/result.html`
**Purpose:** Display generated report.

**Elements:**
- Error message area (if any)
- Report text in preformatted block
- "Back" link to return to form

**Styling:** Simple, readable text display with monospace font for report.

---

## Data Flow Diagram

Here's how data flows through the application:

```
1. User Input (Web Form)
   ↓
2. webapp.py (receives form data)
   ↓
3. PatientInputs (weight, height → BSA calculated)
   ↓
4. EchoValues (all measurements)
   ↓
5. ZScoreCalculator + ParamRegistry
   ↓
6. Z-scores computed for each parameter
   ↓
7. Context built (raw values + Z-scores + BSA)
   ↓
8. ReportTemplate + TemplateRenderer
   ↓
9. Final Report (text)
   ↓
10. result.html (display to user)
```

---

## How to Customize


### Changing Calculations

**File:** `echo_desc/core_math.py`

- **BSA formula:** Edit `calculate_bsa()` function
- **Z-score formula:** Edit `calculate_z_score()` function

---

## Environment Variables

- `ECHOZ_HOST`: Server host address (default: 127.0.0.1)
- `ECHOZ_PORT`: Server port (default: 8000)

**Example:**
```bash
export ECHOZ_HOST=0.0.0.0
export ECHOZ_PORT=8080
uv run echo_desc
```


REF FILE: CONFIGURATION_SYSTEM.md 

---

## Development Workflow

### Making Changes

1. Edit the relevant file (see sections above)
2. If server is running with `uv run echo_desc`, it will auto-reload
3. Refresh browser to see changes

### Testing Changes

1. Start the server: `uv run echo_desc`
2. Open: http://127.0.0.1:8000
3. Fill in test data
4. Check generated report

### Adding Dependencies

1. Edit `pyproject.toml` → add to `dependencies` list
2. Run: `uv sync`
3. Restart application

---

## Common Tasks

### Task: Add a new cardiac measurement

**Files to edit:**
1. `registry_pettersen_detroit.py` - Add parameter definition
2. `report_templates.py` - Add to report template (if needed)

**Steps:**
1. Add Parameter with name, alpha, mean, sd
2. Add to appropriate paragraph in report template
3. Restart application
4. New field appears in form automatically

### Task: Change report wording

**File:** `report_templates.py`

**Example:** Change "w normie" to "prawidłowy":
```python
text=(
    "Wymiar poprzeczny i grubość mięśnia lewej komory prawidłowy: "
    "LVEDD= {LVEDD:.2f} (z= {LVEDD_z:.2f}), ..."
)
```

### Task: Add conditional text to report

**File:** `report_templates.py` or `backend.py`

Currently, the template system is simple. For conditional logic:
1. Add logic in `backend.py` to set flags in context
2. Use those flags in template
3. Or: Implement conditional rendering in `TemplateRenderer`

**Example approach:**
```python
# In backend.py
ctx["lv_abnormal"] = any(abs(z) > 2 for k, z in zscores.items() if k.startswith("LV"))

# In template
text="LV: {lv_status}" where lv_status is computed based on flags
```

---

## Technical Notes

### Why Two Template Systems?

1. **Jinja2** (in `web/templates/`) - For HTML pages
2. **Custom TemplateRenderer** (in `reports/templating.py`) - For medical reports

Reason: Medical reports need precise control over text formatting and explicit handling of missing values.

### Parameter Naming Convention

- Use SHORT, UPPERCASE codes (e.g., "LVEDD", "ROOT", "MPA")
- Keep consistent with medical literature
- Z-score keys automatically get `_z` suffix (e.g., "LVEDD_z")

### BSA Calculation

Uses Mosteller formula (most common in pediatric cardiology):
```
BSA (m²) = √[(height(cm) × weight(kg)) / 3600]
```

Implemented as:
```python
BSA = 0.024265 × weight^0.5378 × height^0.3964
```

### Z-Score Interpretation

- Z = 0: Exactly average
- Z = +2: 2 standard deviations above average
- Z = -2: 2 standard deviations below average
- |Z| > 2: Generally considered abnormal
- |Z| > 3: Definitely abnormal

---

## Troubleshooting

### Problem: Parameter not showing in form
**Solution:** Check that parameter is added to registry in `registry_pettersen_detroit.py`

### Problem: Report shows "###BRAK PARAMETRU:XXX###"
**Solution:** Either the parameter wasn't entered in the form, or the key name in the template doesn't match the registry

### Problem: Changes not appearing
**Solution:** The server auto-reloads, but you may need to hard-refresh the browser (Ctrl+Shift+R)

### Problem: Module not found error
**Solution:** Run `uv sync` to reinstall the package after renaming files

---

## For Beginners: Quick Start Guide

### Just want to run it?
```bash
cd echo_descriptor
uv sync
uv run echo_desc
# Open http://127.0.0.1:8000 in browser
```

### Want to add a measurement?
1. Open: `echo_desc/parameters/registry_pettersen_detroit.py`
2. Find the `params` dictionary
3. Add your parameter (copy existing format)
4. Save and restart

### Want to change report text?
1. Open: `echo_desc/reports/report_templates.py`
2. Find `build_report_template_default()`
3. Edit the paragraph text
4. Save and refresh browser

### Want to understand the code flow?
1. Start at: `web/webapp.py` (receives user input)
2. Follow to: `model.py` (data structures)
3. Then: `zscore_calc.py` (calculations)
4. Finally: `reports/backend.py` (report generation)

---

## References

- **Normative Data:** Pettersen MD et al., "Regression equations for calculation of z scores of cardiac structures in a large cohort of healthy infants, children, and adolescents: an echocardiographic study." J Am Soc Echocardiogr. 2008 Aug;21(8):922-34.

- **BSA Formula:** Mosteller RD. "Simplified calculation of body-surface area." N Engl J Med. 1987 Oct 22;317(17):1098.

---

## License & Contact

See project metadata in `pyproject.toml` for author information.

---

**Last Updated:** January 22, 2026

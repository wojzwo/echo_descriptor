# Configuration System (Parameters & Report Templates)

Echo Descriptor uses **file-based configuration stored directly in the repository**.  
At the current stage of development, configuration files are **edited manually and committed to the repo**.

There is **no automatic user-local config**, no `$HOME`, no XDG paths, and no runtime persistence outside the project directory.

## Configuration Directories

```
echo_descriptor/
├── config/                     # ACTIVE configuration (edited & committed)
│   ├── parameters/
│   │   └── pettersen_detroit.yaml
│   └── reports/
│       └── templates.yaml
│
└── echo_desc/
    └── config_defaults/        # PACKAGED defaults (fallback only)
        ├── parameters/
        │   └── pettersen_detroit.yaml
        └── reports/
            └── templates.yaml
```

## Key Principles

- `config/` is the source of truth during development  
- Configuration is edited manually and committed to git  
- No configuration files are written automatically at runtime  
- No user-specific or machine-specific config directories are used  
- The application always tries to load configuration from `config/` first  

## Fallback Mechanism

If a required configuration file is **missing from `config/`**, the application:

1. Loads the corresponding file from:
   ```
   echo_desc/config_defaults/
   ```
2. Uses it as a **read-only fallback**
3. Does **NOT** automatically copy or generate files

This means:

- Missing config does not crash the app  
- Defaults are bundled with the package  
- Developers explicitly control when configs are copied or promoted  

## Parameters Configuration

**File:**

```
config/parameters/pettersen_detroit.yaml
```

**Purpose:**  
Defines all echocardiographic parameters and their normative data  
(α exponent, mean, SD, description).

**Example:**

```yaml
params:
  LVEDD:
    alpha: 0.45
    mean: 3.89
    sd: 0.33
    description: "LV end-diastolic diameter"
```

This file fully replaces hardcoded parameter definitions.

## Report Templates Configuration

**File:**

```
config/reports/templates.yaml
```

**Purpose:**  
Defines report templates and their paragraphs in a declarative way.

**Example:**

```yaml
templates:
  - id: default_echo
    title: "Domyślny (skrót)"
    paragraphs:
      - id: bsa
        label: "BSA"
        text: "BSA= {BSA_m2:.2f} m2."
```

Each paragraph:

- Has a stable `id`  
- Can be enabled/disabled in the UI  
- Uses the same placeholder syntax as the internal template renderer  

## Editing Workflow (Current)

1. Edit files in `config/`  
2. Commit changes to git  
3. Restart the application (or rely on auto-reload)  
4. Verify output in the web UI  

## Releasing Defaults (Later Stage)

When configuration stabilizes:

1. Copy contents of `config/` into:
   ```
   echo_desc/config_defaults/
   ```
2. Commit updated defaults  
3. `config_defaults/` becomes the official packaged baseline  

At the current stage, this step is **manual and intentional**.

# Echo Descriptor

Auto descriptor generator for pediatric echocardiography procedures with Z-score calculation using Pettersen MD et al. / Detroit Data.

## Requirements

- Python 3.11 or higher
- uv package manager

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd echo_descriptor
```

2. Sync dependencies with uv:
```bash
uv sync
```

## Running the Application

Start the web application:
```bash
uv run echo_desc
```

Or use uvicorn directly:
```bash
uv run uvicorn echo_desc.web.webapp:app --reload --host 127.0.0.1 --port 8000
```

The application will be available at http://127.0.0.1:8000

## Project Structure

```
echo_desc/
├── parameters/          # Parameter definitions and registry
├── reports/            # Report generation logic
├── web/                # FastAPI web application
│   └── templates/      # HTML templates
├── model.py           # Core data models
├── core_math.py       # Mathematical utilities
└── zscore_calc.py     # Z-score calculations
```

## Environment Variables

- `ECHOZ_HOST` - Server host (default: 127.0.0.1)
- `ECHOZ_PORT` - Server port (default: 8000)

## Reference

Pettersen MD et al., J Am Soc Echocardiogr. 2008 21(8):922-34 (Z-scores, Detroit Data)

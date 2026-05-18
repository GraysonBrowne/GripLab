![GripLab](images/GripLab_Banner.png)

# GripLab Developer Guide - v2026.05.2

## Table of Contents
1. [Project Overview](#project-overview)
2. [Development Setup](#development-setup)
3. [Architecture](#architecture)
4. [Code Structure](#code-structure)
5. [Module Documentation](#module-documentation)
6. [Style Guide](#style-guide)
7. [Contributing Guidelines](#contributing-guidelines)
8. [Building the Executable](#building-the-executable)
9. [Troubleshooting](#troubleshooting)
10. [Version History](#version-history)

---

## Project Overview

GripLab is a tire data analysis application built with Panel, Plotly, and scientific Python libraries. It provides an interactive browser-based interface for importing, processing, and visualizing TTC tire test data, with support for multiple unit systems and sign conventions.

### Technology Stack

| Component | Library | Version |
|---|---|---|
| UI Framework | Panel (HoloViz) | 1.7.5 |
| Visualization | Plotly | 6.3.0 |
| Data Processing | NumPy | 2.3.2 |
| Data Processing | SciPy | 1.16.1 |
| Data Processing | Pandas | 2.3.2 |
| Configuration | PyYAML | 6.0.2 |
| Logging | Rich | 14.1.0 |
| Python | | 3.12+ |

---

## Development Setup

### 1. Clone the Repository
```bash
git clone https://github.com/GraysonBrowne/GripLab.git
cd GripLab
```

### 2. Create a Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

### 3. Install Dependencies
```bash
pip install -e .[dev]
```

The editable install registers all project packages (`app`, `core`, `converters`, `ui`, `utils`) with Python, eliminating the need for any `sys.path` manipulation. The `[dev]` group includes Ruff for linting and formatting.

### 4. Run the App
```bash
panel serve main.py --show --autoreload
```

> **Note:** GripLab is served via `panel serve`, which imports `main.py` as a module rather than running it as `__main__`. The bare `main()` call at the bottom of `main.py` is intentional — do not wrap it in `if __name__ == "__main__":`.

---

## Architecture

### High-Level Design

```
┌───────────────────────────────────────────────────┐
│                    Entry Point                    │
│                     (main.py)                     │
├───────────────────────────────────────────────────┤
│                 Application Layer                 │
│            ┌─────────────────────────┐            │
│            │    app/                 │            │
│            ├─────────────────────────┤            │
│            │ • app.py (GripLabApp)   │            │
│            │ • config.py (AppConfig) │            │
│            │ • controllers.py        │            │
│            └─────────────────────────┘            │
├───────────────────────────────────────────────────┤
│                User Interface Layer               │
│            ┌─────────────────────────┐            │
│            │    ui/                  │            │
│            ├─────────────────────────┤            │
│            │ • components.py         │            │
│            │ • modals.py             │            │
│            │ • styles.css            │            │
│            └─────────────────────────┘            │
├───────────────────────────────────────────────────┤
│                   Core Services                   │
│   ┌────────────┐  ┌─────────────┐  ┌──────────┐   │
│   │  core/     │  │converters/  │  │  utils/  │   │
│   ├────────────┤  ├─────────────┤  ├──────────┤   │
│   │• dataio    │  │• units      │  │• logger  │   │
│   │• plotting  │  │• conventions│  │• dialogs │   │
│   │• processing│  │• command    │  │          │   │
│   └────────────┘  │• channels   │  └──────────┘   │
│                   └─────────────┘                 │
└───────────────────────────────────────────────────┘
```

### Design Principles

- **Parse at boundaries:** Raw strings from files, YAML, and UI widgets are parsed into typed enums (`SignConvention`, `UnitSystem`) at the entry point. Internal code passes enum values, never raw strings.
- **Unidirectional flow:** UI → Controllers → Core. Core modules never import from `app/` or `ui/`.
- **Avoid circular imports:** `__init__.py` files declare `__all__` but do not import from submodules. All imports reference submodules directly (e.g. `from core.dataio import DataManager`).
- **Fail gracefully:** Errors are caught, logged with `exc_info=True`, and surfaced to the user via Panel notifications where appropriate.

---

## Code Structure

```
GripLab/
├── main.py                    # Entry point — calls GripLabApp().serve()
├── config.yaml                # User configuration (auto-generated on first run)
├── pyproject.toml             # Project metadata, dependencies, Ruff config
├── version.txt                # PyInstaller Windows VERSIONINFO resource
├── README.md                  # Project overview
├── LICENSE                    # MIT license
│
├── app/                       # Application orchestration
│   ├── __init__.py
│   ├── app.py                 # GripLabApp — UI wiring and callbacks
│   ├── config.py              # AppConfig — configuration dataclass
│   └── controllers.py         # DataController, PlotController
│
├── ui/                        # User interface components
│   ├── __init__.py
│   ├── components.py          # Widget groups (PlotControlWidgets, etc.)
│   ├── modals.py              # Modal dialog layouts
│   └── styles.css             # Custom CSS
│
├── core/                      # Core data handling
│   ├── __init__.py
│   ├── dataio.py              # Dataset, DataManager, DataImporter
│   ├── plotting.py            # PlotBuilder, PlotConfig, PlottingUtils
│   └── processing.py          # SignalProcessor, DataDownsampler
│
├── converters/                # Data transformation utilities
│   ├── __init__.py
│   ├── channels.py            # ChannelMetadata — standard channel labels
│   ├── units.py               # UnitSystem, UnitSystemConverter
│   ├── conventions.py         # SignConvention, ConventionConverter
│   └── command.py             # CmdChannelGenerator
│
├── utils/                     # Shared utilities
│   ├── __init__.py
│   ├── logger.py              # Logging configuration
│   └── dialogs.py             # Tk_utils — file dialog wrappers
│
└── docs/                      # Documentation
    ├── images/                # Screenshots and diagrams
    ├── USER_GUIDE.md          # End-user documentation
    ├── DEVELOPER_GUIDE.md     # This document
    └── Sign_Convention.pdf    # Sign convention reference
```

---

## Module Documentation

### Application Layer (`app/`)

#### `app.py` — `GripLabApp`
Main application class. Initializes Panel, creates and lays out all UI components, and wires all callbacks. Entry point is `GripLabApp().serve()`.

Key methods:
- `_setup_panel()` — configures Panel extensions
- `_initialize_ui()` — instantiates all widget groups
- `_layout_ui()` — places widgets into the FastListTemplate
- `_setup_callbacks()` — binds all `pn.bind` and `on_click` handlers
- `serve()` — serves the app (via template for `panel serve`, or `show()` for frozen executable)

#### `config.py` — `AppConfig`
Configuration dataclass backed by `config.yaml`.

```python
@dataclass
class AppConfig:
    theme: str = "default"
    unit_system: UnitSystem = UnitSystem.USCS
    sign_convention: SignConvention = SignConvention.ISO
    colorway: str = "Plotly"
    colormap: str = "Jet"
    demo_mode: bool = False
    data_dir: str = ""

    @classmethod
    def from_yaml(cls, filepath: str) -> "AppConfig": ...

    def save(self, filepath: str): ...
```

The app version is read from `pyproject.toml` at startup using `tomllib` and is available as `app.config.__version__`.

#### `controllers.py` — `DataController`, `PlotController`
Business logic layer between UI callbacks and core services.

- `DataController` — import, remove, rename, and query datasets
- `PlotController` — collect widget values into a `plot_params` dict and call `PlottingUtils.plot_data()`

---

### UI Layer (`ui/`)

#### `components.py`
Widget groups instantiated once and passed to the layout and callbacks. Each class holds related widgets as instance attributes.

- `PlotControlWidgets` — plot type, axis selectors, command channel filters, downsample slider
- `PlotSettingsWidgets` — title, labels, color map, font/marker settings, marker opacity
- `DataInfoWidgets` — dataset selector, metadata fields, color picker
- `AppSettingsWidgets` — theme, unit system, sign convention, demo mode, data directory
- `WidgetFactory` — static helpers for creating consistently styled common widgets

#### `modals.py`
Layout functions that assemble modal dialog content from existing widget instances. Modals are not instantiated until opened.

---

### Core Services (`core/`)

#### `dataio.py`
Data structures and I/O.

- `Dataset` — frozen dataclass holding channel names, data array, and metadata
- `DataManager` — in-memory store for the active session's datasets
- `DataImporter` — static methods `import_mat()` and `import_dat()` that parse files and return `Dataset` instances

Channel names are normalized to uppercase and temperature unit strings are normalized (e.g. `"deg f"` → `"deg F"`) at import time, before the `Dataset` is created.

#### `plotting.py`
Visualization pipeline.

- `PlotType` — `StrEnum` of supported plot types
- `PlotConfig` — dataclass of all parameters needed to build a figure
- `DataProcessor` — applies unit conversion, sign convention conversion, and command channel filters to a dataset
- `PlotBuilder` — static methods that add Plotly traces to a `go.Figure`
- `PlotMetadataBuilder` — builds titles, subtitles, and axis labels using `ChannelMetadata`
- `PlottingUtils` — top-level entry point called by `PlotController`

Two module-level utilities handle colorscale alpha:
```python
def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str: ...
def colorscale_with_alpha(colorscale: list[str], alpha: float) -> list[list]: ...
```

#### `processing.py`
Signal processing and downsampling.

- `SignalProcessor.apply_butterworth_filter()` — zero-phase Butterworth filter (lowpass, highpass, bandpass, bandstop)
- `DataDownsampler.downsample_uniform()` — every-nth-point downsampling, the primary path used by plotting
- `DataDownsampler.downsample_random()` / `downsample_grid()` — alternative strategies
- `low_pass_filter()` — legacy wrapper used by `CmdChannelGenerator`

---

### Converters (`converters/`)

#### `channels.py` — `ChannelMetadata`
Standard display labels for known TTC channels. Used by `PlotMetadataBuilder` to generate human-readable axis labels. Returns the raw channel name as a fallback for unlabelled channels.

```python
class ChannelMetadata:
    CHANNEL_LABELS: Dict[str, str] = {
        "FY": "Lateral Force",
        "SA": "Slip Angle",
        # ...
    }

    @classmethod
    def get_label(cls, channel: str) -> str:
        """Return the standard label, or the channel name if unknown."""
```

#### `units.py` — `UnitSystem`, `UnitSystemConverter`
`UnitSystem` is a `StrEnum` with members `SI`, `METRIC`, `USCS`. Conversion factors are pre-computed and cached in `_CONVERSION_CACHE` on first use.

#### `conventions.py` — `SignConvention`, `ConventionConverter`
`SignConvention` is a `StrEnum` with members `SAE`, `ADAPTED_SAE`, `ISO`, `ADAPTED_ISO`. Sign multipliers (±1) are defined per channel in `SIGN_DEFINITIONS`. The multiplier for a conversion is `to_sign * from_sign` — equivalent to division for ±1 values.

#### `command.py` — `CmdChannelGenerator`
Generates discretized command channels (`CmdFZ`, `CmdSA`, etc.) by snapping each data point to the nearest target command value. These channels drive the conditional filter selectors in the UI.

---

### Utilities (`utils/`)

#### `logger.py`
Configures a `logging.Logger` with a `Rich` handler for terminal output and a `FileHandler` for the log file written alongside the executable.

```python
logger.debug()    # Detailed diagnostic info
logger.info()     # General information
logger.warning()  # Recoverable issues
logger.error()    # Errors — always pass exc_info=True
```

#### `dialogs.py` — `Tk_utils`
Wraps Tkinter file dialogs. All methods raise the dialog on top of other windows and destroy the hidden root window after use.

- `select_file()` → `tuple` of selected paths, or `tuple()` if cancelled
- `select_dir()` → `str` path, or `""` if cancelled
- `save_file()` → `str` path, or `""` if cancelled

---

## Style Guide

### Linting and Formatting

GripLab uses [**Ruff**](https://docs.astral.sh/ruff/) for linting and formatting, replacing Black, isort, and flake8. Run before committing:

```bash
ruff check .           # lint
ruff format --check .  # check formatting without modifying
```

To auto-fix:
```bash
ruff check --fix .  # fix lint issues
ruff format .       # apply formatting
```

Ruff is configured in `pyproject.toml` under `[tool.ruff]`.

### Naming Conventions

```python
# Classes: PascalCase
class DataManager: ...

# Functions and methods: snake_case
def calculate_average(): ...

# Constants: UPPER_SNAKE_CASE
CHANNEL_LABELS: Dict[str, str] = { ... }

# Private/internal: leading underscore
def _internal_helper(): ...
```

### Type Hints

All public functions and methods should have full type annotations.

```python
def convert_dataset(
    dataset: Dataset,
    to_system: UnitSystem,
) -> Dataset: ...
```

### Docstrings

Use Google-style docstrings for all public functions, methods, and classes:

```python
def get_multiplier(
    cls, channel: str, from_convention: SignConvention, to_convention: SignConvention
) -> int:
    """
    Get the sign multiplier for converting a channel between conventions.

    Args:
        channel: Channel name (e.g. "FY")
        from_convention: Source sign convention
        to_convention: Target sign convention

    Returns:
        Multiplier of 1 or -1
    """
```

### Imports

Always use absolute imports. Never use relative imports outside of `__init__.py`.

```python
# Standard library
from pathlib import Path
from typing import Any, Dict, Optional

# Third-party
import numpy as np
import panel as pn

# Local
from core.dataio import DataManager
from converters.conventions import SignConvention
from utils.logger import logger
```

---

## Contributing Guidelines

### Branching

Create a feature branch from `develop` named after the issue number:

```bash
git checkout develop
git checkout -b 42-your-feature-description
```

Open pull requests targeting `develop`. Merges to `main` are reserved for releases.

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<optional body>
```

Types:
- `feat` — new feature
- `fix` — bug fix
- `docs` — documentation only
- `style` — formatting, no logic change
- `refactor` — restructuring without behaviour change
- `perf` — performance improvement
- `chore` — maintenance (dependency updates, build scripts)

Examples:
```bash
git commit -m "feat(plotting): add marker opacity control"
git commit -m "fix(dataio): normalize channel names to uppercase on import"
git commit -m "docs: update developer guide versioning section"
```

### Pull Request Checklist

Before opening a PR:

- [ ] `ruff check .` passes
- [ ] `ruff format --check .` passes
- [ ] Type hints on all public functions
- [ ] Docstrings complete on new classes and methods
- [ ] No `print()` statements — use `logger`
- [ ] No commented-out code
- [ ] Error handling included where appropriate

---

## Building the Executable

### Prerequisites
```bash
pip install -e .[build]   # installs PyInstaller
```

### Build
```bash
python scripts/build_exe.py
```

The output executable is written to `dist/GripLab.exe`.

### Version File
`version.txt` in the project root contains Windows VERSIONINFO metadata embedded by PyInstaller. Update it alongside `DEVELOPER_GUIDE.md`
and `USER_GUIDE.md` headers, and `pyproject.toml` when releasing a new version.

---

## Troubleshooting

### Import errors on startup
Ensure the project is installed in the active virtual environment:
```bash
pip install -e .
```
This registers all packages (`app`, `core`, `converters`, `ui`, `utils`) and eliminates Pylance and runtime import resolution issues.

### Panel not updating after widget change
Use the `@hold()` decorator when updating multiple widgets in one callback to batch the updates and prevent intermediate re-renders:
```python
@hold()
def _on_something(self, value):
    self.widget_a.value = x
    self.widget_b.options = y
```

### Plotly figure not rendering
- Check the browser console for JavaScript errors
- Ensure `pn.extension("plotly")` is called before the figure is rendered
- Verify the data arrays passed to the trace are not empty

### Performance issues with large datasets
- Increase the downsample factor to reduce the number of plotted points
- Confirm unit conversion is using the cached `_CONVERSION_CACHE` and not recomputing on every call
- Profile with `cProfile` to identify bottlenecks:
  ```python
  import cProfile
  cProfile.run("slow_function()", sort="cumtime")
  ```

---

## Version History

### Versioning Scheme

GripLab uses a date-based versioning structure: **`YYYY.MM.Build`**

- **YYYY** — Year of release
- **MM** — Month of release
- **Build** — Build number within that month, starting at 1

Examples:
- `2025.10.1` — First release in October 2025
- `2025.10.2` — Second release in October 2025
- `2026.05.1` — First release in May 2026

When releasing, update the version in **both** `pyproject.toml` and `version.txt`.

### Release History

| Version | Date | Notes |
|---|---|---|
| 2026.05.1 | 2026-05-06 | Initial release |
| 2026.05.2 | 2026-05-09 | Documentation Update |

---

*Keep this guide up to date when adding new modules, changing architecture, or establishing new patterns.*

![GripLab](images/GripLab_Banner.png)
# Developer Guide (v2025.10.1.0)

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Code Structure](#code-structure)
4. [Module Documentation](#module-documentation)
5. [Style Guide](#style-guide)
6. [Performance Guidelines](#performance-guidelines)
7. [Contributing Guidelines](#contributing-guidelines)
8. [Common Patterns](#common-patterns)
9.  [Troubleshooting](#troubleshooting)

---

## Project Overview

GripLab is an internal tire data analysis application built with Panel, Plotly, and scientific Python libraries. It provides comprehensive tools for importing, processing, visualizing, and analyzing tire test data with support for multiple unit systems and sign conventions.

### Key Features
- Multi-format data import (MATLAB .mat, ASCII .dat/.txt)
- 2D/3D interactive visualization with Plotly
- Unit system conversion (USCS/Metric/SI)
- Sign convention conversion (SAE/ISO variants)
- Command channel generation for conditional parsing
- PyInstaller support for standalone executables

### Technology Stack
- **Frontend**: Panel (HoloViz) v1.7.5
- **Visualization**: Plotly v6.3.0
- **Data Processing**: NumPy v2.3.2, Pandas v2.3.2, SciPy v1.16.1
- **Configuration**: YAML
- **Logging**: Python logging with Rich
- **File Dialogs**: Tkinter
- **Python**: 3.12+

---

## Architecture

### High-Level Architecture

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
│   │• processing│  │• commands   │  │          │   │
│   └────────────┘  └─────────────┘  └──────────┘   │
└───────────────────────────────────────────────────┘
```

### Design Principles

1. **Simplicity First**: Avoid over-engineering; use simple, direct solutions
2. **Performance Matters**: Optimize for large datasets (100k+ data points)
3. **Clear Dependencies**: Unidirectional flow (UI → Controllers → Core)
4. **Fail Gracefully**: Always handle errors and provide user feedback

---

## Code Structure

### Directory Layout

```
GripLab/
├── main.py                    # Application entry point
├── config.yaml                # User configuration
├── requirements.txt           # Python dependencies
├── README.md                  # Project overview
├── LICENSE                    # MIT permissive license
│
├── app/                       # Application orchestration
│   ├── __init__.py
│   ├── app.py                 # Main application class (GripLabApp)
│   ├── config.py              # Configuration management (AppConfig)
│   └── controllers.py         # Business logic (DataController, PlotController)
│
├── ui/                        # User interface components
│   ├── __init__.py
│   ├── components.py          # UI widgets (PlotControlWidgets, DataInfoWidgets, etc.)
│   ├── modals.py              # Modal dialogs (settings, plot settings, removal)
│   └── styles.css             # Custom CSS styles
│
├── core/                      # Core data handling
│   ├── __init__.py
│   ├── dataio.py              # Data I/O (Dataset, DataManager, DataImporter)
│   ├── plotting.py            # Visualization (PlottingUtils, PlotBuilder, PlotConfig)
│   └── processing.py          # Signal processing (SignalProcessor, DataDownsampler)
│
├── converters/                # Data transformation utilities
│   ├── __init__.py
│   ├── units.py               # Unit system conversion (UnitSystemConverter)
│   ├── conventions.py         # Sign convention conversion (ConventionConverter)
│   └── commands.py            # Command channel generation (CmdChannelGenerator)
│
├── utils/                     # Shared utilities
│   ├── __init__.py
│   ├── logger.py              # Logging configuration
│   └── dialogs.py             # File dialog utilities (Tk_utils)
│
├── docs/                      # Documentation
│   ├── guides/                # User guides
│   ├── images/                # Screenshots and diagrams
│   ├── DEVELOPER_GUIDE.md     # This document
│   └── Sign_Convention.pdf    # Sign convention reference
│
└── scripts/                   # Utility scripts
    └── build_exe.py           # PyInstaller build script
```

---

## Module Documentation

### Application Layer (`app/`)

#### `app.py`
Main application class that orchestrates the entire application.

```python
class GripLabApp:
    """Main application orchestrator."""
    
    def __init__(self, config_path: str = "config.yaml"):
        # Initialize configuration
        # Initialize data manager and controllers
        # Setup Panel extensions
        # Create UI components
        # Wire callbacks
        
    def serve(self):
        """Serve the application."""
```

**Key Responsibilities:**
- Initialize and configure Panel
- Create and layout UI components
- Handle high-level application flow
- Manage modal dialogs

#### `config.py`
Configuration management using dataclasses.

```python
@dataclass
class AppConfig:
    """Application configuration container."""
    theme: str = "dark"
    unit_system: str = "USCS"
    sign_convention: str = "ISO"
    # ...
    
    @classmethod
    def from_yaml(cls, filepath: str) -> 'AppConfig':
        """Load configuration from YAML file."""
    
    def save(self, filepath: str):
        """Save configuration to YAML file."""
```

#### `controllers.py`
Business logic controllers that coordinate between UI and core services.

```python
class DataController:
    """Manages data operations."""
    - import_data()
    - remove_dataset()
    - update_dataset_info()
    - get_dataset_info()
    
class PlotController:
    """Manages plotting operations."""
    - create_plot()
    - get_plot_parameters()
```

### UI Layer (`ui/`)

#### `components.py`
Reusable UI widget components.

```python
class PlotControlWidgets:
    """Plot control UI components."""
    - plot_type selector
    - axis selectors (x, y, z, color)
    - command channel filters
    - downsample controls

class DataInfoWidgets:
    """Dataset information UI components."""
    - dataset selector
    - metadata editors
    - update controls
```

#### `modals.py`
Modal dialog layouts.

```python
def create_settings_layout(widgets, callbacks):
    """Create application settings modal layout."""

def create_plot_settings_layout(widgets):
    """Create plot settings modal layout."""

def create_removal_dialog(dataset_name, callbacks):
    """Create dataset removal confirmation dialog."""
```

### Core Services (`core/`)

#### `dataio.py`
Data structures and I/O operations.

```python
@dataclass
class Dataset:
    """Container for tire test data."""
    path: Path
    name: str
    channels: List[str]
    data: NDArray[np.float64]
    # ... metadata

class DataManager:
    """Manages collection of datasets."""
    - add_dataset()
    - get_dataset()
    - remove_dataset()
    - parse_dataset()  # Filter by conditions

class DataImporter:
    """Import data from various formats."""
    - import_mat()  # MATLAB files
    - import_dat()  # ASCII files
```

#### `plotting.py`
Visualization utilities using Plotly.

```python
@dataclass
class PlotConfig:
    """Configuration for plot generation."""
    plot_type: PlotType
    channels: Dict[str, str]
    downsample_factor: int
    # ... plot styling

class PlotBuilder:
    """Builds Plotly figures."""
    - create_figure()
    - add_2d_trace()
    - add_3d_trace()
    - update_layout()

class DataProcessor:
    """Processes datasets for plotting."""

class PlottingUtils:
    """Main plotting interface (legacy compatibility)."""
    - plot_data()  # Main entry point
```

#### `processing.py`
Signal processing and data manipulation.

```python
class SignalProcessor:
    """Signal processing operations."""
    - apply_butterworth_filter()
    - remove_outliers()

class DataDownsampler:
    """Data reduction for visualization."""
    - downsample_uniform()
    - downsample_random()
    - downsample_grid()
    - smart_downsample()
```

### Converters (`converters/`)

#### `units.py`
Unit system conversions.

```python
class UnitSystemConverter:
    """Unit system converter."""
    
    # Pre-computed conversion cache
    _CONVERSION_CACHE = {}
    
    @classmethod
    def convert_dataset(cls, dataset, to_system):
        """Convert entire dataset."""
    
    @classmethod
    def convert_value(cls, value, unit_type, from_system, to_system):
        """Convert single value."""
```

**Performance Notes:**
- Cache all conversion factors on first use
- Use NumPy broadcasting for vectorized operations

#### `conventions.py`
Sign convention transformations.

```python
class ConventionConverter:
    """Sign convention converter."""
    
    SIGN_DEFINITIONS = {
        # Channel-specific sign multipliers
        "FY": {"SAE": 1, "ISO": -1, ...},
        # ...
    }
    
    @classmethod
    def convert_dataset_convention(cls, dataset, target):
        """Convert dataset to target convention."""
```

#### `commands.py`
Command channel generation for conditional parsing.

```python
class CmdChannelGenerator:
    """Generate discretized command channels."""
    
    CMD_TARGETS = {
        'FZ': {'USCS': [0, -50, -100, ...], ...}
    }
    
    @classmethod
    def create_cmd_channels(cls, channels, units, data, ...):
        """Create command channels for filtering."""
```

### Utilities (`utils/`)

#### `logger.py`
Centralized logging configuration.

```python
# Configured logger instance
logger = logging.getLogger(__name__)

# Log levels in use:
logger.debug()    # Detailed diagnostic info
logger.info()     # General information
logger.warning()  # Potential issues
logger.error()    # Errors with traceback
```

#### `dialogs.py`
File dialog utilities using Tkinter.

```python
class Tk_utils:
    @staticmethod
    def select_file(filetypes, initialdir):
        """Open file selection dialog."""
    
    @staticmethod
    def select_dir(initialdir):
        """Open directory selection dialog."""
```

---

## Style Guide

### Python Style [PEP 8](https://peps.python.org/pep-0008/)

Use [**Black**](https://black.readthedocs.io/en/stable/) for auto-formatting:
  ```bash
  black .
  ```
Use [**isort**](https://pycqa.github.io/isort/) for import sorting:
  ```bash
  isort .
  ```

#### Imports
```python
# Standard library
import os
import sys
from pathlib import Path

# Third-party
import numpy as np
import pandas as pd

# Local - use relative imports within package
from dataio import Dataset
from utils.logger import logger
```

#### Naming Conventions
```python
# Classes: PascalCase
class DataManager:

# Functions/methods: snake_case  
def calculate_average():

# Constants: UPPER_SNAKE_CASE
MAX_POINTS = 10000

# Private: leading underscore
def _internal_helper():
```

#### Type Hints
```python
from typing import List, Dict, Optional, Tuple

def process_data(
    data: np.ndarray,
    config: Optional[Dict[str, Any]] = None
) -> Tuple[np.ndarray, int]:
    """Always use type hints for public APIs."""
```

#### Docstrings (Google Style)
```python
def convert_units(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert a value between unit systems.
    
    Args:
        value: The numeric value to convert
        from_unit: Source unit identifier  
        to_unit: Target unit identifier
        
    Returns:
        Converted value in target units
        
    Raises:
        ValueError: If conversion not supported
    """
```

---

## Performance Guidelines

### Critical Performance Areas

1. **Data Import**: Must handle files with 1M+ data points
2. **Unit Conversion**: Frequent operation, must be optimized
3. **Plotting**: Downsampling critical for responsive UI
4. **Filtering**: Command channel filtering must be fast

---

## Contributing Guidelines

### Development Setup

1. **Clone Repository**
```bash
git clone <repository-url>
cd GripLab
```

2. **Create Virtual Environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Run Application**
```bash
panel serve main.py --show --autoreload
```

### Making Changes

#### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

#### 2. Follow Code Organization
- Put UI code in `ui/`
- Put data logic in `core/`
- Put converters in `converters/`
- Keep main.py minimal

#### 3. Update Documentation
- Add docstrings to new functions
- Update this guide if adding new patterns
- Include examples in docstrings

### Commit Message Format

Follow conventional commits with version awareness:

```
<type>(<scope>): <subject> [v<YYYY.MM.Major.Minor>]

<body>

<footer>
```

Types:
- `feat`: New feature (increment Major)
- `fix`: Bug fix (increment Minor)
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

Examples:
```bash
# Major feature - increment Major version
git commit -m "feat(plotting): add 3D surface plots [v2024.12.3.0]

- Added surface plot option to PlotType enum
- Implemented PlotBuilder.add_surface_trace()
- Updated UI to include surface option"

# Bug fix - increment Minor version
git commit -m "fix(converter): correct metric conversion factor [v2024.12.2.1]

- Fixed incorrect conversion factor for force units
- Added validation for edge cases"

# Documentation update - no version change
git commit -m "docs: update developer guide with examples"
```

### Code Review Checklist

Before submitting changes:

- [ ] Code follows style guide
- [ ] Type hints on public functions
- [ ] Docstrings are complete
- [ ] No commented-out code
- [ ] No print statements (use logger)
- [ ] Performance impact considered
- [ ] Error handling included
- [ ] UI remains responsive

---

## Common Patterns

### Callback Pattern
```python
# UI callback with error handling
def _on_button_click(self, event):
    """Handle button click event."""
    try:
        # Perform operation
        result = self.controller.process()
        
        # Update UI
        self.update_display(result)
        
    except ValueError as e:
        logger.warning(f"Invalid input: {e}")
        pn.state.notifications.warning(str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        pn.state.notifications.error("An error occurred")
```

### Factory Pattern
```python
class WidgetFactory:
    @staticmethod
    def create_button(name: str, **kwargs) -> pn.widgets.Button:
        """Create standardized button."""
        defaults = {"button_type": "primary"}
        defaults.update(kwargs)
        return pn.widgets.Button(name=name, **defaults)
```
---

## Troubleshooting

### Common Issues

#### 1. Import Errors
```python
# If getting ImportError, check:
- Virtual environment activated?
- All requirements installed?
- Running from project root?

# Add project to path if needed:
sys.path.insert(0, str(Path(__file__).parent))
```

#### 2. Performance Issues
```python
# Profile the slow operation
import cProfile
cProfile.run('slow_function()', sort='cumtime')

# Check for:
- Missing vectorization
- Unnecessary loops
- Missing cache
- Large data copies
```

#### 3. Panel/Plotly Issues
```python
# Panel not updating:
@hold()  # Use hold decorator for batch updates
def update_multiple_widgets():
    widget1.value = x
    widget2.value = y

# Plotly not rendering:
- Check browser console for JS errors
- Ensure plotly properly imported
- Check data format matches plot type
```

#### 4. Memory Issues
```python
# Monitor memory usage
import psutil
process = psutil.Process()
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")

# Common causes:
- Not deleting large arrays
- Keeping all datasets in memory
- Missing downsampling
```

### Debug Mode
```python
# Enable debug logging
logger.setLevel(logging.DEBUG)

# Add debug output
logger.debug(f"Data shape: {data.shape}")
logger.debug(f"Processing time: {time.perf_counter() - start:.3f}s")
```

---

## Building Executable

### PyInstaller Build
```python
# scripts/build_exe.py
import PyInstaller.__main__

PyInstaller.__main__.run([
    'main.py',
    '--name=GripLab',
    '--onefile',
    '--windowed',
    '--add-data=ui/styles.css:ui',
    '--add-data=config.yaml:.',
    '--add-data=docs:docs',
    '--hidden-import=panel',
    '--hidden-import=plotly',
])
```

### Build Process
```bash
# Build executable
python scripts/build_exe.py

# Output in dist/GripLab.exe
```

---

## Resources

### Documentation
- [Panel Documentation](https://panel.holoviz.org/)
- [Plotly Python](https://plotly.com/python/)
- [NumPy User Guide](https://numpy.org/doc/stable/)

### Tools
- **IDE**: VSCode with Python extension
- **Linting**: `pylint`, `flake8`
- **Formatting**: `black`
- **Testing**: `pytest`

---

## Version History

### Versioning Scheme
GripLab uses a date-based versioning structure: **`YYYY.MM.Major.Minor`**

- **YYYY**: Year of release
- **MM**: Month of release
- **Major**: Major version within that month (breaking changes, significant features)
- **Minor**: Minor version/patch (bug fixes, small improvements)

Examples:
- `2025.10.1.0` - First major release in October 2025
- `2025.10.1.1` - Bug fix for the above release
- `2025.10.2.0` - Second major release in October 2025
- `2026.01.1.0` - First major release in January 2026

### Release History

| Version | Date | Changes |
|---------|------|---------|
| 2025.10.1.0 | 2025-10-19 | Initial release |

---

*This guide is maintained alongside the codebase. Please update when adding new patterns or changing architecture.*
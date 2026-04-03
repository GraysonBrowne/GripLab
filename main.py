# main.py
"""GripLab - Tire Data Analysis Application"""

import importlib
import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.app import GripLabApp

if'_PYI_SPLASH_IPC' in os.environ and importlib.uyit.find_spec("pyi_splash"):
    import pyi_splash
    pyi_splash.update_text("UI Loaded ...")
    pyi_splash.close()


def main():
    """Main entry point."""
    app = GripLabApp()
    app.serve()


main()

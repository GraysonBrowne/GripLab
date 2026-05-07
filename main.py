# main.py
"""GripLab - Tire Data Analysis Application"""

import importlib
import os

from app.app import GripLabApp

if'_PYI_SPLASH_IPC' in os.environ and importlib.util.find_spec("pyi_splash"):
    import pyi_splash
    pyi_splash.update_text("UI Loaded ...")
    pyi_splash.close()

def main():
    """Main entry point."""
    app = GripLabApp()
    app.serve()


main()

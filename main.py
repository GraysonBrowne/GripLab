# main.py
"""GripLab - Tire Data Analysis Application"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.app import GripLabApp


def main():
    """Main entry point."""
    app = GripLabApp()
    app.serve()


main()

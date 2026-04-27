# main.py
"""GripLab - Tire Data Analysis Application"""

from app.app import GripLabApp


def main():
    """Main entry point."""
    app = GripLabApp()
    app.serve()

main()

# scripts/logger_setup.py
import logging
import sys
from pathlib import Path

from rich.logging import RichHandler

logger = logging.getLogger(__name__)

# Handler determines where logs go: stdout/file
shell_handler = RichHandler()

if getattr(sys, "frozen", False):
    # If running as a frozen executable, set the log file to the same directory
    program_dir = Path(sys.executable).parent
else:
    program_dir = Path(__file__).parent

file_handler = logging.FileHandler(Path(program_dir, "app.log"))

# Set the logging level
logger.setLevel(logging.DEBUG)
shell_handler.setLevel(logging.DEBUG)
file_handler.setLevel(logging.DEBUG)

# Format for the logs
shell_format = "%(message)s"
file_format = (
    "%(levelname)s %(asctime)s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s"
)

shell_formatter = logging.Formatter(shell_format)
file_formatter = logging.Formatter(file_format)

# Assign the formatters to the handlers
shell_handler.setFormatter(shell_formatter)
file_handler.setFormatter(file_formatter)

# Add the handlers to the logger
logger.addHandler(shell_handler)
logger.addHandler(file_handler)

logger.propagate = False

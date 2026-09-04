import logging
import sys
from pathlib import Path

# Create logs folder if it doesn't exist
LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Set up the logger
logger = logging.getLogger("email_automation")
logger.setLevel(logging.INFO)

# Format: 2026-08-12 18:30:45 - INFO - Email fetched
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Write to file: logs/app.log
file_handler = logging.FileHandler(LOGS_DIR / "app.log", encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Also print to terminal (console)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def get_logger():
    """Other files will call this to get the logger."""
    return logger
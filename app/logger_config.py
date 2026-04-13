import logging
import sys
import os

def setup_logging(level=logging.INFO):
    os.makedirs("data", exist_ok=True)
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("data/execution.log", encoding="utf-8")
        ]
    )
    for lib in ["selenium", "urllib3", "requests", "undetected_chromedriver"]:
        logging.getLogger(lib).setLevel(logging.WARNING)

setup_logging()
logger = logging.getLogger("AI-DE-S")
